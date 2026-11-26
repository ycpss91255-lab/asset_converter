import textwrap

import pytest
from pxr import Usd, UsdGeom, UsdPhysics

from asset_converter.convert import ConvertError, convert_urdf
from asset_converter.drive import drive_axis
from asset_converter.preflight import PreflightError
from asset_converter.world_link import find_synthetic_root_joint

_OBJ = textwrap.dedent("""\
    v 0 0 0
    v 1 0 0
    v 1 1 0
    v 0 1 0
    f 1 2 3 4
    """)

_INERTIAL = (
    '<inertial><mass value="1"/>'
    '<inertia ixx="1" ixy="0" ixz="0" iyy="1" iyz="0" izz="1"/></inertial>'
)


def _mesh_link(name, uri):
    return f"""
      <link name="{name}">
        {_INERTIAL}
        <visual><geometry><mesh filename="{uri}"/></geometry></visual>
        <collision><geometry><mesh filename="{uri}"/></geometry></collision>
      </link>"""


def _urdf(body):
    return f'<?xml version="1.0"?><robot name="r">{body}</robot>'


def _make_package(tmp_path):
    """A package outside the URDF's directory tree (auto-search can't find it)."""
    pkg = tmp_path / "pkgs" / "mycam_description"
    (pkg / "meshes").mkdir(parents=True)
    (pkg / "meshes" / "cube.obj").write_text(_OBJ)
    src = tmp_path / "src"
    src.mkdir()
    return pkg, src


def _meshes(usd_path):
    stage = Usd.Stage.Open(str(usd_path))
    return [p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh)]


def _pkg_urdf(extra=""):
    return _urdf(
        _mesh_link("base_link", "package://mycam_description/meshes/cube.obj")
        + extra
    )


def test_package_mesh_resolves_with_map(tmp_path):
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(_pkg_urdf())
    out = convert_urdf(urdf, tmp_path / "out", {"mycam_description": pkg})
    assert out.is_absolute() and out.suffix == ".usda" and out.exists()
    assert len(_meshes(out)) == 2  # visual + collision


def test_relative_package_path_is_relative_to_urdf_dir(tmp_path):
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(_pkg_urdf())
    out = convert_urdf(
        urdf, tmp_path / "out", {"mycam_description": "../pkgs/mycam_description"}
    )
    assert len(_meshes(out)) == 2


def test_missing_map_raises_instead_of_silent_degradation(tmp_path):
    _, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(_pkg_urdf())
    with pytest.raises(PreflightError, match="not in package map") as e:
        convert_urdf(urdf, tmp_path / "out")
    assert not isinstance(e.value, ConvertError)


def test_partial_degradation_is_detected(tmp_path):
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    bad = _mesh_link("other", "package://nopkg/meshes/x.obj")
    joint = (
        '<joint name="j" type="fixed"><parent link="base_link"/>'
        '<child link="other"/></joint>'
    )
    urdf.write_text(_pkg_urdf(bad + joint))
    with pytest.raises(PreflightError, match="nopkg") as e:
        convert_urdf(urdf, tmp_path / "out", {"mycam_description": pkg})
    assert not isinstance(e.value, ConvertError)


def test_missing_mesh_file_raises_preflight_error(tmp_path):
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(
        _urdf(_mesh_link("base_link", "package://mycam_description/meshes/nope.obj"))
    )
    with pytest.raises(PreflightError, match="mesh file not found") as e:
        convert_urdf(urdf, tmp_path / "out", {"mycam_description": pkg})
    assert not isinstance(e.value, ConvertError)
    assert not (tmp_path / "out").exists()  # failed before conversion


def test_urdf_without_meshes_converts(tmp_path):
    urdf = tmp_path / "r.urdf"
    urdf.write_text(_urdf(f'<link name="base_link">{_INERTIAL}</link>'))
    out = convert_urdf(urdf, tmp_path / "out")
    assert out.exists()


def test_world_rule_applied(tmp_path):
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(_pkg_urdf())  # no world link -> floating base
    out = convert_urdf(urdf, tmp_path / "out", {"mycam_description": pkg})
    assert find_synthetic_root_joint(Usd.Stage.Open(str(out))) is None

    urdf_w = src / "w.urdf"
    urdf_w.write_text(
        _urdf(
            '<link name="world"/>'
            + _mesh_link("base_link", "package://mycam_description/meshes/cube.obj")
            + '<joint name="wj" type="fixed"><parent link="world"/>'
            '<child link="base_link"/></joint>'
        )
    )
    out_w = convert_urdf(urdf_w, tmp_path / "out_w", {"mycam_description": pkg})
    stage_w = Usd.Stage.Open(str(out_w))
    assert any(p.GetName() == "wj" for p in stage_w.Traverse())


def test_drives_applied(tmp_path):
    urdf = tmp_path / "r.urdf"
    urdf.write_text(
        _urdf(
            f'<link name="base_link">{_INERTIAL}</link>'
            f'<link name="arm">{_INERTIAL}</link>'
            '<joint name="rj" type="revolute"><parent link="base_link"/>'
            '<child link="arm"/><axis xyz="0 0 1"/>'
            '<limit lower="-1" upper="1" effort="10" velocity="1"/>'
            '<dynamics damping="0.5"/></joint>'
        )
    )
    out = convert_urdf(urdf, tmp_path / "out")
    stage = Usd.Stage.Open(str(out))
    joints = [p for p in stage.Traverse() if drive_axis(p) is not None]
    assert len(joints) == 1
    assert "PhysicsDriveAPI:angular" in joints[0].GetAppliedSchemas()
    drive = UsdPhysics.DriveAPI(joints[0], "angular")
    assert drive.GetMaxForceAttr().Get() == pytest.approx(10)


def _output_layers(out):
    """Every USD file the converter wrote (root, payload and sublayers)."""
    files = sorted(
        p for p in out.rglob("*")
        if p.suffix in {".usd", ".usda", ".usdc"}
    )
    assert len(files) > 1, "expected root plus payload/sub layers"
    return files


def test_every_output_layer_authors_z_up_and_meter_units(tmp_path):
    """Issue #44: upAxis=Z / metersPerUnit=1 explicitly authored (not defaults)."""
    pkg, src = _make_package(tmp_path)
    urdf = src / "r.urdf"
    urdf.write_text(_pkg_urdf())
    out = convert_urdf(urdf, tmp_path / "out", {"mycam_description": pkg})
    for path in _output_layers(tmp_path / "out"):
        stage = Usd.Stage.Open(str(path))
        keys = stage.GetRootLayer().pseudoRoot.ListInfoKeys()
        assert "upAxis" in keys and "metersPerUnit" in keys, path
        assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z, path
        assert UsdGeom.GetStageMetersPerUnit(stage) == 1, path
    assert out in _output_layers(tmp_path / "out")
