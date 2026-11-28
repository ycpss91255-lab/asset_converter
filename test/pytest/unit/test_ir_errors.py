from asset_converter.ir.errors import IRError


def test_is_value_error_and_names_field():
    e = IRError("pose.xyz", "must have 3 elements, got 2")
    assert isinstance(e, ValueError)
    assert e.field == "pose.xyz"
    assert "pose.xyz" in str(e)
    assert "3 elements" in str(e)
