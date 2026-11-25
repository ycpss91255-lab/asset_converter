# asset_converter

URDF + TOML to USD conversion tooling. Supplements the official urdf-usd-converter with: DriveAPI from TOML, sensor prim creation, world link handling (fixed vs floating), concave collision pre-processing.

## Current status

Early stage. Contains design (issue #1) and sensor seed code from the isaac repo.

## Sensor seed code

Extracted from ycpss91255-lab/isaac @ c068e3a. The sensor creation code (Camera / LiDAR / IMU USD prims) will be refactored into a clean API.

See [SOURCE.md](SOURCE.md) for seed file provenance and layer split.

## License

[Apache-2.0](LICENSE)
