"""SI <-> degree helpers. The IR stores SI (rad); degrees only at output."""

import math

from asset_converter.ir.errors import IRError


def check_number(value, field="value"):
    """Return ``value`` as float; reject bool, non-numbers, nan and inf."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise IRError(field, f"must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise IRError(field, f"must be finite, got {value!r}")
    return value


def rad_to_deg(value):
    return math.degrees(check_number(value))


def deg_to_rad(value):
    return math.radians(check_number(value))


def per_rad_to_per_deg(value):
    """SI quantity per rad -> per degree (multiply by pi/180)."""
    return check_number(value) * math.pi / 180.0


def per_deg_to_per_rad(value):
    """Per degree -> SI quantity per rad (multiply by 180/pi)."""
    return check_number(value) * 180.0 / math.pi
