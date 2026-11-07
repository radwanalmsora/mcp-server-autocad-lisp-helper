"""
AutoCAD AutoLISP Helper MCP Server.
Provides deterministic static analysis, syntax checking, function extraction,
and local variable leakage detection for AutoLISP (.lsp) files.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP(
    name="mcp-server-autocad-lisp-helper",
)


def _strip_comments_and_strings(code: str) -> str:
    """
    Safely replaces string literals and comments with whitespace to preserve character indices.
    """
    output = []
    i = 0
    n = len(code)
    while i < n:
        # Block comments: ;| ... |;
        if code[i:i+2] == ";|":
            output.append("  ")
            i += 2
            while i < n and code[i:i+2] != "|;":
                output.append("\n" if code[i] == "\n" else " ")
                i += 1
            if i < n:
                output.append("  ")
                i += 2
            continue

        # Single-line comment: ; ...
        if code[i] == ";":
            output.append(" ")
            i += 1
            while i < n and code[i] != "\n":
                output.append(" ")
                i += 1
            continue

        # String literal: "..."
        if code[i] == '"':
            output.append(" ")
            i += 1
            while i < n:
                if code[i] == "\\" and i + 1 < n:
                    output.append("  ")
                    i += 2
                    continue
                if code[i] == '"':
                    output.append(" ")
                    i += 1
                    break
                output.append("\n" if code[i] == "\n" else " ")
                i += 1
            continue

        output.append(code[i])
        i += 1

    return "".join(output)


@mcp.tool()
def analyze_lisp_syntax(code: str) -> Dict[str, Any]:
    """
    Checks AutoLISP code for balanced parentheses, quotation marks, comments,
    and structural syntax errors with exact line and column numbers.
    """
    stack: List[Tuple[str, int, int]] = []
    errors: List[Dict[str, Any]] = []

    lines = code.splitlines(keepends=True)
    line_num = 1
    col_num = 1
    i = 0
    n = len(code)

    while i < n:
        ch = code[i]

        if ch == "\n":
            line_num += 1
            col_num = 1
            i += 1
            continue

        # Check for block comment ;| ... |;
        if ch == ";" and i + 1 < n and code[i + 1] == "|":
            start_l, start_c = line_num, col_num
            i += 2
            col_num += 2
            closed = False
            while i < n:
                if code[i] == "\n":
                    line_num += 1
                    col_num = 1
                    i += 1
                    continue
                if code[i] == "|" and i + 1 < n and code[i + 1] == ";":
                    i += 2
                    col_num += 2
                    closed = True
                    break
                i += 1
                col_num += 1
            if not closed:
                errors.append({
                    "type": "unclosed_block_comment",
                    "message": f"Unclosed block comment ;| starting at line {start_l}, column {start_c}",
                    "line": start_l,
                    "column": start_c
                })
            continue

        # Check for single line comment
        if ch == ";":
            while i < n and code[i] != "\n":
                i += 1
                col_num += 1
            continue

        # Check for string literal
        if ch == '"':
            start_l, start_c = line_num, col_num
            i += 1
            col_num += 1
            closed = False
            while i < n:
                if code[i] == "\n":
                    line_num += 1
                    col_num = 1
                    i += 1
                    continue
                if code[i] == "\\" and i + 1 < n:
                    i += 2
                    col_num += 2
                    continue
                if code[i] == '"':
                    i += 1
                    col_num += 1
                    closed = True
                    break
                i += 1
                col_num += 1
            if not closed:
                errors.append({
                    "type": "unclosed_string",
                    "message": f"Unclosed string literal starting at line {start_l}, column {start_c}",
                    "line": start_l,
                    "column": start_c
                })
            continue

        # Parentheses
        if ch == "(":
            stack.append(("(", line_num, col_num))
        elif ch == ")":
            if not stack:
                errors.append({
                    "type": "unexpected_closing_paren",
                    "message": f"Unexpected closing parenthesis ')' at line {line_num}, column {col_num}",
                    "line": line_num,
                    "column": col_num
                })
            else:
                stack.pop()

        i += 1
        col_num += 1

    # Remaining unclosed parentheses
    for p, pline, pcol in stack:
        errors.append({
            "type": "unclosed_parenthesis",
            "message": f"Unclosed opening parenthesis '(' at line {pline}, column {pcol}",
            "line": pline,
            "column": pcol
        })

    is_valid = len(errors) == 0
    return {
        "valid": is_valid,
        "total_errors": len(errors),
        "errors": errors,
        "summary": "AutoLISP code structure is balanced and valid." if is_valid else f"Found {len(errors)} structural syntax error(s)."
    }


@mcp.tool()
def extract_lisp_functions(code: str) -> Dict[str, Any]:
    """
    Extracts function definitions (defun C:...), argument lists, and localized variables
    from AutoLISP code.
    """
    # Regex to capture defun and parameter blocks
    defun_pattern = re.compile(
        r"\(\s*defun\s+([cC]:[^\s()]+|[^\s()]+)\s*\(\s*([^()]*)\s*\)",
        re.IGNORECASE
    )

    functions: List[Dict[str, Any]] = []

    for match in defun_pattern.finditer(code):
        raw_name = match.group(1).strip()
        params_str = match.group(2).strip()
        start_pos = match.start()

        # Calculate line number
        line_num = code[:start_pos].count("\n") + 1

        is_command = raw_name.lower().startswith("c:")
        clean_name = raw_name[2:] if is_command else raw_name

        # Parse arguments and localized variables separated by /
        if "/" in params_str:
            parts = params_str.split("/", 1)
            raw_args = parts[0].split()
            raw_locals = parts[1].split()
        else:
            raw_args = params_str.split()
            raw_locals = []

        args = [a.strip() for a in raw_args if a.strip()]
        locals_list = [l.strip() for l in raw_locals if l.strip()]

        functions.append({
            "name": raw_name,
            "clean_name": clean_name,
            "is_command": is_command,
            "line": line_num,
            "arguments": args,
            "local_variables": locals_list,
            "signature": f"(defun {raw_name} ({' '.join(args)}{' / ' + ' '.join(locals_list) if locals_list else ''}))"
        })

    return {
        "total_functions": len(functions),
        "functions": functions
    }


@mcp.tool()
def check_missing_cleanups(code: str) -> Dict[str, Any]:
    """
    Identifies unhandled local variables (assigned via setq but not declared after '/')
    and unmodified system variables to prevent AutoCAD state leakage.
    """
    # 1. First extract all functions
    func_data = extract_lisp_functions(code)
    clean_code = _strip_comments_and_strings(code)

    leakage_issues: List[Dict[str, Any]] = []
    sysvar_issues: List[Dict[str, Any]] = []

    builtins = {"t", "nil", "pi", "pause", "*error*"}

    # Detect setq assignments: (setq var1 val1 var2 val2 ...)
    # Find matching expressions
    for func in func_data["functions"]:
        func_name = func["name"]
        declared_args = set(a.lower() for a in func["arguments"])
        declared_locals = set(l.lower() for l in func["local_variables"])
        safe_scope = declared_args | declared_locals | builtins

        # Locate function span roughly
        func_sig = func["name"]
        idx = code.find(func_sig)
        if idx == -1:
            continue

        # Look for setq occurrences inside function
        setq_matches = re.finditer(r"\(\s*setq\s+([^()]+)\)", clean_code[idx:], re.IGNORECASE)
        for sm in setq_matches:
            body = sm.group(1).strip()
            tokens = body.split()
            # In setq, variables appear at even indices: 0, 2, 4...
            abs_pos = idx + sm.start()
            setq_line = code[:abs_pos].count("\n") + 1

            for i in range(0, len(tokens), 2):
                var = tokens[i].lower()
                # Skip numeric or non-identifier tokens
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_\-:#]*$", var):
                    continue
                if var not in safe_scope:
                    leakage_issues.append({
                        "function": func_name,
                        "variable": tokens[i],
                        "line": setq_line,
                        "severity": "WARNING",
                        "message": f"Variable '{tokens[i]}' is assigned in function '{func_name}' at line {setq_line} but is NOT declared in local list (/ ...). This will leak into AutoCAD's global memory namespace.",
                        "recommended_fix": f"Add '{tokens[i]}' after the '/' in function definition: (defun {func_name} ({' '.join(func['arguments'])} / {' '.join(func['local_variables'] + [tokens[i]])}))"
                    })

    # Detect System Variables without restoration
    # e.g., (setvar "CMDECHO" 0) or (setvar 'osmode 0)
    setvar_pattern = re.finditer(r"\(\s*setvar\s+[\"']?([a-zA-Z0-9_-]+)[\"']?\s+([^()]+)\)", code, re.IGNORECASE)
    getvar_pattern_str = r"\(getvar\s+[\"']?{var}[\"']?\)"

    for svm in setvar_pattern:
        var_name = svm.group(1).upper()
        pos = svm.start()
        line = code[:pos].count("\n") + 1

        # Check if code ever retrieves and restores it
        has_getter = re.search(r"\(getvar\s+[\"']?" + re.escape(var_name) + r"[\"']?\)", code, re.IGNORECASE)
        if not has_getter:
            sysvar_issues.append({
                "system_variable": var_name,
                "line": line,
                "severity": "CRITICAL",
                "message": f"AutoCAD System Variable '{var_name}' is modified via setvar at line {line} without saving its initial state via (getvar \"{var_name}\").",
                "recommended_fix": f"Store original state: (setq old_{var_name.lower()} (getvar \"{var_name}\")) and restore in exit/error handler."
            })

    total_issues = len(leakage_issues) + len(sysvar_issues)
    return {
        "total_issues": total_issues,
        "state_leakages": leakage_issues,
        "system_variable_warnings": sysvar_issues,
        "clean": total_issues == 0,
        "summary": "No state leakage or unhandled system variables detected." if total_issues == 0 else f"Found {len(leakage_issues)} state leakages and {len(sysvar_issues)} system variable issues."
    }


def main():
    """Runs the MCP server over standard input/output (stdio)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
