"""Robot IR: frozen dataclasses in SI units (m, kg, rad, s). No pxr import.

Drive gains and velocities are stored as SI physical intent (per rad);
per-degree conversion belongs to the exporter (see units.py).
"""

import math
from dataclasses import dataclass, field
from types import MappingProxyType

from asset_converter.ir.errors import IRError
from asset_converter.ir.units import check_number

JOINT_TYPES = ("fixed", "revolute", "continuous", "prismatic", "floating", "planar")
DRIVE_MODES = ("velocity", "position", "effort")
SENSOR_KINDS = ("camera", "lidar", "imu")


def _vec(value, n, name):
    try:
        items = tuple(value)
    except TypeError:
        raise IRError(name, f"must be a sequence of {n} numbers") from None
    if len(items) != n:
        raise IRError(name, f"must have {n} elements, got {len(items)}")
    return tuple(check_number(v, f"{name}[{i}]") for i, v in enumerate(items))


def _name(value, name):
    if not isinstance(value, str) or not value:
        raise IRError(name, "must be a non-empty string")
    return value


def _opt(value, name, nonneg=False):
    if value is None:
        return None
    value = check_number(value, name)
    if nonneg and value < 0:
        raise IRError(name, f"must be >= 0, got {value}")
    return value


def _set(obj, name, value):
    object.__setattr__(obj, name, value)


@dataclass(frozen=True)
class Pose:
    xyz: tuple = (0.0, 0.0, 0.0)
    rpy: tuple = (0.0, 0.0, 0.0)

    def __post_init__(self):
        _set(self, "xyz", _vec(self.xyz, 3, "xyz"))
        _set(self, "rpy", _vec(self.rpy, 3, "rpy"))


@dataclass(frozen=True)
class Inertial:
    mass: float
    inertia: tuple  # ixx, ixy, ixz, iyy, iyz, izz
    com: tuple = (0.0, 0.0, 0.0)

    def __post_init__(self):
        mass = check_number(self.mass, "mass")
        if mass < 0:
            raise IRError("mass", f"must be >= 0, got {mass}")
        _set(self, "mass", mass)
        _set(self, "com", _vec(self.com, 3, "com"))
        ixx, ixy, ixz, iyy, iyz, izz = inertia = _vec(self.inertia, 6, "inertia")
        _set(self, "inertia", inertia)
        det = (
            ixx * (iyy * izz - iyz * iyz)
            - ixy * (ixy * izz - iyz * ixz)
            + ixz * (ixy * iyz - iyy * ixz)
        )
        if (
            ixx < 0 or iyy < 0 or izz < 0
            or ixx * iyy - ixy * ixy < 0
            or ixx * izz - ixz * ixz < 0
            or iyy * izz - iyz * iyz < 0
            or det < 0
        ):
            raise IRError("inertia", "must be positive semi-definite")


@dataclass(frozen=True)
class Link:
    name: str
    inertial: Inertial = None

    def __post_init__(self):
        _name(self.name, "name")
        if self.inertial is not None and not isinstance(self.inertial, Inertial):
            raise IRError("inertial", "must be an Inertial")


@dataclass(frozen=True)
class JointLimit:
    lower: float = None
    upper: float = None
    effort: float = None  # N or N*m
    velocity: float = None  # m/s or rad/s

    def __post_init__(self):
        _set(self, "lower", _opt(self.lower, "lower"))
        _set(self, "upper", _opt(self.upper, "upper"))
        _set(self, "effort", _opt(self.effort, "effort", nonneg=True))
        _set(self, "velocity", _opt(self.velocity, "velocity", nonneg=True))
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise IRError("limit", f"lower {self.lower} > upper {self.upper}")


@dataclass(frozen=True)
class Joint:
    name: str
    type: str
    parent: str
    child: str
    origin: Pose = field(default_factory=Pose)
    axis: tuple = (1.0, 0.0, 0.0)
    limit: JointLimit = None

    def __post_init__(self):
        _name(self.name, "name")
        if self.type not in JOINT_TYPES:
            raise IRError("type", f"must be one of {JOINT_TYPES}, got {self.type!r}")
        _name(self.parent, "parent")
        _name(self.child, "child")
        if self.parent == self.child:
            raise IRError("child", f"joint {self.name!r} connects {self.parent!r} to itself")
        if not isinstance(self.origin, Pose):
            raise IRError("origin", "must be a Pose")
        axis = _vec(self.axis, 3, "axis")
        norm = math.sqrt(sum(a * a for a in axis))
        if norm == 0:
            raise IRError("axis", "must be non-zero")
        _set(self, "axis", tuple(a / norm for a in axis))
        if self.limit is not None and not isinstance(self.limit, JointLimit):
            raise IRError("limit", "must be a JointLimit")


@dataclass(frozen=True)
class Drive:
    mode: str
    stiffness: float = 0.0  # N/m or N*m/rad
    damping: float = 0.0  # N*s/m or N*m*s/rad
    max_velocity: float = None  # m/s or rad/s

    def __post_init__(self):
        if self.mode not in DRIVE_MODES:
            raise IRError("mode", f"must be one of {DRIVE_MODES}, got {self.mode!r}")
        _set(self, "stiffness", _opt(self.stiffness, "stiffness", nonneg=True))
        _set(self, "damping", _opt(self.damping, "damping", nonneg=True))
        _set(self, "max_velocity", _opt(self.max_velocity, "max_velocity", nonneg=True))


@dataclass(frozen=True)
class Sensor:
    name: str
    kind: str
    parent: str  # link name
    pose: Pose = field(default_factory=Pose)

    def __post_init__(self):
        _name(self.name, "name")
        if self.kind not in SENSOR_KINDS:
            raise IRError("kind", f"must be one of {SENSOR_KINDS}, got {self.kind!r}")
        _name(self.parent, "parent")
        if not isinstance(self.pose, Pose):
            raise IRError("pose", "must be a Pose")


@dataclass(frozen=True)
class Robot:
    name: str
    links: tuple
    joints: tuple = ()
    sensors: tuple = ()
    drives: dict = field(default_factory=dict)  # joint name -> Drive

    def __post_init__(self):
        _name(self.name, "name")
        links = _items(self.links, Link, "links")
        joints = _items(self.joints, Joint, "joints")
        sensors = _items(self.sensors, Sensor, "sensors")
        if not links:
            raise IRError("links", "must not be empty")
        link_names = _unique([l.name for l in links], "links")
        joint_names = _unique([j.name for j in joints], "joints")
        _unique([s.name for s in sensors], "sensors")

        parent_of = {}
        for j in joints:
            for end in (j.parent, j.child):
                if end not in link_names:
                    raise IRError("joints", f"joint {j.name!r} references unknown link {end!r}")
            if j.child in parent_of:
                raise IRError("joints", f"link {j.child!r} has more than one parent joint")
            parent_of[j.child] = j.parent
        roots = [n for n in link_names if n not in parent_of]
        if len(roots) != 1:
            raise IRError("links", f"must form a tree with one root, found roots {roots}")
        for n in link_names:  # every link must reach the root (no cycles)
            seen = set()
            while n in parent_of:
                if n in seen:
                    raise IRError("joints", f"cycle through link {n!r}")
                seen.add(n)
                n = parent_of[n]

        for s in sensors:
            if s.parent not in link_names:
                raise IRError("sensors", f"sensor {s.name!r} references unknown link {s.parent!r}")
        by_name = {j.name: j for j in joints}
        drives = dict(self.drives)
        for jn, d in drives.items():
            if jn not in joint_names:
                raise IRError("drives", f"unknown joint {jn!r}")
            if by_name[jn].type == "fixed":
                raise IRError("drives", f"joint {jn!r} is fixed and cannot be driven")
            if not isinstance(d, Drive):
                raise IRError("drives", f"value for {jn!r} must be a Drive")

        _set(self, "links", links)
        _set(self, "joints", joints)
        _set(self, "sensors", sensors)
        _set(self, "drives", MappingProxyType(drives))
        object.__setattr__(self, "_root", roots[0])

    @property
    def root(self):
        return self._root


def _items(value, cls, name):
    items = tuple(value)
    for i, v in enumerate(items):
        if not isinstance(v, cls):
            raise IRError(f"{name}[{i}]", f"must be a {cls.__name__}")
    return items


def _unique(names, field_name):
    seen = set()
    for n in names:
        if n in seen:
            raise IRError(field_name, f"duplicate name {n!r}")
        seen.add(n)
    return seen
