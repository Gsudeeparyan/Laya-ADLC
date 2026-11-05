from adlc_workbook import formulas


def test_normalise_expands_this_row_shorthand():
    f = formulas.normalise('[@[Due date]]-TODAY()+[@Status]', "tblActions")
    assert f == "=tblActions[[#This Row],[Due date]]-TODAY()+tblActions[[#This Row],[Status]]"


def test_normalise_is_idempotent():
    once = formulas.normalise('=IF([@Score]>=10,"Red","Green")', "tblRAID")
    assert formulas.normalise(once, "tblRAID") == once


def test_newer_functions_get_xlfn_prefix_once():
    f = formulas.normalise('=IFS([@A]>1,"x",TRUE,"y")', "tblT")
    assert f.startswith("=_xlfn.IFS(")
    assert formulas.normalise(f, "tblT").count("_xlfn.") == 1


def test_display_returns_friendly_form():
    f = formulas.normalise("=[@[Due date]]-TODAY()", "tblActions")
    assert formulas.display(f, "tblActions") == "=[@[Due date]]-TODAY()"


def test_dynamic_array_functions_are_detected():
    assert formulas.dynamic_array_functions_used("=FILTER(tblA[X],tblA[Y]=1)") == ["FILTER"]
    assert formulas.dynamic_array_functions_used("=SUM(tblA[X])") == []


def test_rename_only_touches_the_named_table():
    f = "=COUNTIF(tblActions[Due date],tblOther[Due date])+tblActions[[#This Row],[Due date]]"
    out = formulas.rename_column_refs(f, "tblActions", "Due date", "Deadline")
    assert out == "=COUNTIF(tblActions[Deadline],tblOther[Due date])+tblActions[[#This Row],[Deadline]]"


def test_references_column_matches_whole_names():
    f = "=tblActions[[#This Row],[Status]]"
    assert formulas.references_column(f, "tblActions", "Status")
    assert not formulas.references_column(f, "tblActions", "Stat")
    assert not formulas.references_column(f, "tblAction", "Status")
