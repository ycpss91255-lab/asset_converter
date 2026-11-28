import math

import pytest

from asset_converter.ir import units
from asset_converter.ir.errors import IRError


def test_deg_rad_roundtrip():
    assert units.rad_to_deg(math.pi) == pytest.approx(180.0)
    assert units.deg_to_rad(180.0) == pytest.approx(math.pi)
    assert units.deg_to_rad(units.rad_to_deg(1.234)) == pytest.approx(1.234)


def test_per_rad_to_per_deg():
    # SI value per radian -> USD value per degree = SI * pi/180
    assert units.per_rad_to_per_deg(180.0 / math.pi) == pytest.approx(1.0)


def test_per_deg_to_per_rad_inverse():
    assert units.per_deg_to_per_rad(units.per_rad_to_per_deg(7.5)) == pytest.approx(7.5)


def test_rejects_non_finite():
    for bad in (float("nan"), float("inf")):
        with pytest.raises(IRError):
            units.rad_to_deg(bad)


def test_rejects_bool_and_str():
    with pytest.raises(IRError):
        units.deg_to_rad(True)
    with pytest.raises(IRError):
        units.deg_to_rad("1")
