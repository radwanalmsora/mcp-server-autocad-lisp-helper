# 📐 AutoCAD AutoLISP Helper MCP Server

<div align="center">

[![PyPI - Version](https://img.shields.io/pypi/v/mcp-server-autocad-lisp-helper?style=for-the-badge&logo=pypi&logoColor=white&color=0073e6)](https://pypi.org/project/mcp-server-autocad-lisp-helper/)
[![Python Version](https://img.shields.io/pypi/pyversions/mcp-server-autocad-lisp-helper?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/mcp-server-autocad-lisp-helper/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F5A623?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)
[![MCP Compliant](https://img.shields.io/badge/MCP-Standard-10b981?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io)

**A high-precision, deterministic [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server engineered in Python to statically inspect, parse, and debug AutoCAD AutoLISP (`.lsp`) files with 100% precision.**

[Quickstart](#-quickstart-zero-install) • [Tools Overview](#-exposed-mcp-tools) • [Claude Desktop Setup](#-claude-desktop-integration) • [Architecture](#-architecture--deterministic-parsing)

</div>

---

## 🌟 Highlights

- 🔒 **Zero Cloud Dependencies**: 100% local, fast, and deterministic AST parsing with regex. No external APIs or telemetry.
- 🎯 **Pinpoint Accuracy**: Flags balanced parenthesis mismatches with exact line and column numbers.
- 🛡️ **AutoCAD State Protection**: Prevents global namespace contamination by detecting unlocalized `setq` variables.
- ⚙️ **System Variable Auditing**: Detects AutoCAD system variable mutations (`setvar`) lacking initial preservation (`getvar`).
- ⚡ **Zero-Install Ready**: Run instantly in any MCP client via `uvx`.

---

## 🛠️ Exposed MCP Tools

| Tool | Purpose | Key Capabilities |
| :--- | :--- | :--- |
| **`analyze_lisp_syntax`** | Structural Syntax Audit | Validates balanced parentheses `( )`, quotes `"..."`, and block comments `;\| ... \|;`. Reports exact line and column offsets for syntax errors. |
| **`extract_lisp_functions`** | AST Function Inspection | Extracts all `(defun ...)` and AutoCAD commands `(defun c:... ...)`. Accurately isolates arguments and localized variables declared after the `/`. |
| **`check_missing_cleanups`** | State Leakage Detection | Identifies global variable pollution caused by unlocalized `setq` assignments and flags unpreserved AutoCAD system variables (`setvar`). |

---

## ⚡ Quickstart (Zero-Install)

No manual clone or installation required. Launch directly using **`uvx`**:

```bash
uvx mcp-server-autocad-lisp-helper
