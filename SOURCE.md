# Source

Seed code extracted from ycpss91255-lab/isaac @ c068e3a.

The seed validation logic is pure Python (no Isaac Sim needed). Its tests live in `test/pytest/unit/test_sensor_validation.py` and run in `devel-test`; a syntax error in any `seed/**/*.py` fails the gate. The Isaac-side setup functions (`setup_sensor` etc.) are not exercised.

| Seed file | Origin |
|-----------|--------|
| seed/sensors_prim.py | framework/isaac_devkit/sensors.py (full 756 lines) |
| test/pytest/unit/test_sensor_validation.py | test/unit/pytest/test_sensor_setup.py |

This seed contains the full sensors.py including entangled OmniGraph code.
Only the sensor-prim-creation layer belongs in asset_converter:

**Belongs here (layer a -- sensor prim creation in USD)**:
- Config loading + validation: load_config, get_category, _validate_*, validate_camera
- Helper functions: _fov_to_aperture, _role_to_helper_type
- USD prim creation: _set_camera_intrinsics, _set_xform_pose
- Sensor prim creation (currently mixed into OmniGraph functions):
  - Mount Xform creation + pose
  - UsdGeom.Camera definition + intrinsics
  - Isaac sensor commands: IsaacSensorCreateRtxLidar, IsaacSensorCreateImuSensor
  - RealSense asset referencing + RigidBodyAPI override + depth clipping

**Does NOT belong here (layer b/c -- moves to isaac / isaac_ros2)**:
- OmniGraph action graph construction (og.Controller.edit, nodes, connects)
- ROS 2 bridge nodes (ROS2CameraHelper, ROS2PublishImu, ROS2RtxLidarHelper)
- Topic names, frame_id assignment
- _build_graph_topology, _enable_extensions (Kit extension management)

Refactoring to separate these layers is the next step.
See ycpss91255-lab/isaac#309 and asset_converter#1 for the design.
