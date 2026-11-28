import dataclasses

import pytest

from asset_converter.ir.errors import IRError
from asset_converter.ir.model import Pose
from asset_converter.ir.scene import Scene, SceneObject, SceneRobot


def test_scene_robot_requires_model():
    with pytest.raises(IRError) as e:
        SceneRobot(model="")
    assert "model" in str(e.value)
    assert SceneRobot(model="a.urdf").pose == Pose()


def test_scene_object_requires_model():
    with pytest.raises(IRError) as e:
        SceneObject(model="")
    assert "model" in str(e.value)


def test_scene_object_pose():
    o = SceneObject(model="box", pose=Pose(xyz=(2, 0, 0.5)))
    assert o.pose.xyz == (2.0, 0.0, 0.5)


def test_scene_valid_and_frozen():
    s = Scene(
        robot=SceneRobot(model="r.urdf", pose=Pose(xyz=(0, 0, 0.05))),
        ground=True,
        objects=[SceneObject(model="wall")],
    )
    assert isinstance(s.objects, tuple) and len(s.objects) == 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.ground = False


def test_scene_defaults():
    s = Scene(robot=SceneRobot(model="r.urdf"))
    assert s.ground is False and s.objects == ()


def test_scene_rejects_wrong_types():
    with pytest.raises(IRError) as e:
        Scene(robot="r.urdf")
    assert "robot" in str(e.value)
    with pytest.raises(IRError) as e:
        Scene(robot=SceneRobot(model="r"), objects=["wall"])
    assert "objects[0]" in str(e.value)
    with pytest.raises(IRError):
        Scene(robot=SceneRobot(model="r"), ground="yes")


def test_scene_no_engine_specific_fields():
    names = {f.name for s in (Scene, SceneRobot, SceneObject)
             for f in dataclasses.fields(s)}
    assert not any("physx" in n.lower() or "newton" in n.lower() for n in names)
