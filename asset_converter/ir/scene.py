"""Scene IR: neutral robot / ground / objects layout. No pxr import.

Only neutral fields; engine-specific settings (PhysX, Newton, ...) must
not appear here.
"""

from dataclasses import dataclass, field

from asset_converter.ir.errors import IRError
from asset_converter.ir.model import Pose


def _model(value):
    if not isinstance(value, str) or not value:
        raise IRError("model", "must be a non-empty string")


def _pose(value):
    if not isinstance(value, Pose):
        raise IRError("pose", "must be a Pose")


@dataclass(frozen=True)
class SceneRobot:
    model: str
    pose: Pose = field(default_factory=Pose)

    def __post_init__(self):
        _model(self.model)
        _pose(self.pose)


@dataclass(frozen=True)
class SceneObject:
    model: str
    pose: Pose = field(default_factory=Pose)

    def __post_init__(self):
        _model(self.model)
        _pose(self.pose)


@dataclass(frozen=True)
class Scene:
    robot: SceneRobot
    ground: bool = False
    objects: tuple = ()

    def __post_init__(self):
        if not isinstance(self.robot, SceneRobot):
            raise IRError("robot", "must be a SceneRobot")
        if not isinstance(self.ground, bool):
            raise IRError("ground", "must be a bool")
        objects = tuple(self.objects)
        for i, o in enumerate(objects):
            if not isinstance(o, SceneObject):
                raise IRError(f"objects[{i}]", "must be a SceneObject")
        object.__setattr__(self, "objects", objects)
