from mcp_server_autocad_lisp_helper.server import (
    analyze_lisp_syntax,
    extract_lisp_functions,
    check_missing_cleanups,
)

SAMPLE_LISP = """
(defun c:draw_box (pt1 pt2 / width height)
  (setvar "CMDECHO" 0)
  (setq width 100)
  (setq unlocalized_var 50)
  (princ "\nBox drawn.")
  (princ)
)
"""

def test_syntax():
    res = analyze_lisp_syntax(SAMPLE_LISP)
    assert res["valid"] is True, "Syntax should be valid"

def test_extract():
    res = extract_lisp_functions(SAMPLE_LISP)
    assert res["total_functions"] == 1
    fn = res["functions"][0]
    assert fn["name"] == "c:draw_box"
    assert fn["is_command"] is True
    assert fn["arguments"] == ["pt1", "pt2"]
    assert fn["local_variables"] == ["width", "height"]

def test_cleanups():
    res = check_missing_cleanups(SAMPLE_LISP)
    assert res["clean"] is False
    leak_vars = [item["variable"] for item in res["state_leakages"]]
    assert "unlocalized_var" in leak_vars
    sys_vars = [item["system_variable"] for item in res["system_variable_warnings"]]
    assert "CMDECHO" in sys_vars
    print("\n=======================================================")
    print("SUCCESS: All AutoLISP Helper Tests Passed Successfully!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_syntax()
    test_extract()
    test_cleanups()
