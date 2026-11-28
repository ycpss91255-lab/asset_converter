import dataclasses

import pytest

from asset_converter.ir.errors import IRError
from asset_converter.ir.model import (
    Drive,
    Inertial,
    Joint,
    JointLimit,
    Link,
    Pose,
    Robot,
    Sensor,
)


def _robot(**kw):
    links = kw.pop("links", (Link("base"), Link("wheel")))
    joints = kw.pop(
        "joints",
        (Joint("j", "continuous", "base", "wheel", axis=(0, 1, 0)),),
    )
    return Robot("r", links, joints, **kw)


def test_pose_defaults_and_frozen():
    p = Pose()
    assert p.xyz == (0.0, 0.0, 0.0) and p.rpy == (0.0, 0.0, 0.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.xyz = (1.0, 0.0, 0.0)


def test_pose_coerces_sequences_to_float_tuples():
    p = Pose(xyz=[1, 2, 3], rpy=[0, 0, 1])
    assert p.xyz == (1.0, 2.0, 3.0)
    assert all(isinstance(v, float) for v in p.xyz)


@pytest.mark.parametrize("xyz", [(1, 2), (1, 2, 3, 4), (1, 2, float("nan"))])
def test_pose_bad_xyz(xyz):
    with pytest.raises(IRError) as e:
        Pose(xyz=xyz)
    assert "xyz" in str(e.value)


def test_pose_bad_rpy_names_field():
    with pytest.raises(IRError) as e:
        Pose(rpy=(0, 0))
    assert "rpy" in str(e.value)


def test_inertial_valid():
    i = Inertial(mass=1.5, inertia=(1, 0, 0, 1, 0, 1))
    assert i.mass == 1.5 and i.com == (0.0, 0.0, 0.0)


@pytest.mark.parametrize("mass", [-1.0, float("inf")])
def test_inertial_bad_mass(mass):
    with pytest.raises(IRError):
        Inertial(mass=mass, inertia=(1, 0, 0, 1, 0, 1))


def test_inertial_zero_mass_ok():
    Inertial(mass=0.0, inertia=(0, 0, 0, 0, 0, 0))


def test_inertial_bad_inertia_len_and_nonpositive_definite():
    with pytest.raises(IRError):
        Inertial(mass=1, inertia=(1, 0, 0, 1))
    with pytest.raises(IRError):
        Inertial(mass=1, inertia=(-1, 0, 0, 1, 0, 1))


def test_link_requires_name():
    with pytest.raises(IRError) as e:
        Link("")
    assert "name" in str(e.value)


def test_joint_limit_order():
    with pytest.raises(IRError):
        JointLimit(lower=1.0, upper=0.0)
    with pytest.raises(IRError):
        JointLimit(velocity=-1.0)
    with pytest.raises(IRError):
        JointLimit(effort=-1.0)
    assert JointLimit(lower=-1, upper=1, velocity=10).velocity == 10.0


def test_joint_type_validated():
    with pytest.raises(IRError) as e:
        Joint("j", "wobbly", "a", "b")
    assert "type" in str(e.value)


def test_joint_axis_normalized_and_zero_rejected():
    j = Joint("j", "revolute", "a", "b", axis=(0, 0, 2))
    assert j.axis == (0.0, 0.0, 1.0)
    with pytest.raises(IRError):
        Joint("j", "revolute", "a", "b", axis=(0, 0, 0))


def test_joint_parent_equals_child_rejected():
    with pytest.raises(IRError):
        Joint("j", "fixed", "a", "a")


@pytest.mark.parametrize("mode", ["velocity", "position", "effort"])
def test_drive_modes(mode):
    assert Drive(mode=mode).mode == mode


def test_drive_bad_mode_and_negative_gains():
    with pytest.raises(IRError):
        Drive(mode="torque")
    with pytest.raises(IRError):
        Drive(mode="velocity", damping=-1.0)
    with pytest.raises(IRError):
        Drive(mode="position", stiffness=-1.0)


def test_drive_si_values_stored_as_given():
    # IR keeps SI (per rad); no per-degree conversion here.
    d = Drive(mode="position", stiffness=100.0, damping=1.0, max_velocity=10.0)
    assert d.stiffness == 100.0 and d.max_velocity == 10.0


def test_sensor_kind_and_parent():
    s = Sensor("cam", "camera", "base", pose=Pose(xyz=(0, 0, 1)))
    assert s.kind == "camera"
    with pytest.raises(IRError):
        Sensor("x", "radar", "base")
    with pytest.raises(IRError):
        Sensor("x", "imu", "")


def test_robot_valid_and_frozen():
    r = _robot()
    assert r.root == "base"
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.name = "x"


def test_robot_duplicate_link_and_joint_names():
    with pytest.raises(IRError):
        _robot(links=(Link("a"), Link("a")), joints=())
    j = Joint("j", "fixed", "base", "wheel")
    with pytest.raises(IRError):
        _robot(links=(Link("base"), Link("wheel"), Link("w2")),
               joints=(j, Joint("j", "fixed", "base", "w2")))


def test_robot_joint_unknown_link_names_it():
    with pytest.raises(IRError) as e:
        _robot(joints=(Joint("j", "fixed", "base", "ghost"),))
    assert "ghost" in str(e.value)


def test_robot_must_be_tree():
    # two roots
    with pytest.raises(IRError):
        _robot(links=(Link("a"), Link("b")), joints=())
    # two parents
    with pytest.raises(IRError):
        _robot(
            links=(Link("a"), Link("b"), Link("c")),
            joints=(Joint("j1", "fixed", "a", "c"), Joint("j2", "fixed", "b", "c")),
        )
    # cycle
    with pytest.raises(IRError):
        _robot(
            links=(Link("a"), Link("b"), Link("c")),
            joints=(
                Joint("j1", "fixed", "a", "b"),
                Joint("j2", "fixed", "b", "c"),
                Joint("j3", "fixed", "c", "b"),
            ),
        )


def test_robot_drive_must_target_existing_non_fixed_joint():
    r = _robot(drives={"j": Drive(mode="velocity", damping=1.0)})
    assert r.drives["j"].mode == "velocity"
    with pytest.raises(IRError) as e:
        _robot(drives={"nope": Drive(mode="velocity")})
    assert "nope" in str(e.value)
    fixed = (Joint("f", "fixed", "base", "wheel"),)
    with pytest.raises(IRError):
        _robot(joints=fixed, drives={"f": Drive(mode="velocity")})


def test_robot_sensor_parent_must_exist():
    with pytest.raises(IRError) as e:
        _robot(sensors=(Sensor("c", "camera", "ghost"),))
    assert "ghost" in str(e.value)


def test_robot_containers_are_immutable():
    r = _robot(drives={"j": Drive(mode="velocity")})
    assert isinstance(r.links, tuple) and isinstance(r.joints, tuple)
    with pytest.raises(TypeError):
        r.drives["x"] = Drive(mode="effort")


def test_robot_requires_name_and_links():
    with pytest.raises(IRError):
        Robot("", (Link("a"),), ())
    with pytest.raises(IRError):
        Robot("r", (), ())


def test_no_pxr_import():
    import subprocess
    import sys

    code = (
        "import sys; import asset_converter.ir.model, asset_converter.ir.scene;"
        "sys.exit(any(m == 'pxr' or m.startswith('pxr.') for m in sys.modules))"
    )
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
