# asset_converter

URDF + TOML 转 USD 转换工具。在官方 urdf-usd-converter 基础上补充：TOML 驱动的 DriveAPI、传感器 prim 创建、world link 处理（fixed vs floating）、凹面碰撞体预处理。

## 当前状态

早期阶段。包含设计规划（issue #1）及从 isaac repo 提取的传感器种子代码。

## 传感器种子代码

从 ycpss91255-lab/isaac @ c068e3a 提取。传感器创建代码（Camera / LiDAR / IMU USD prims）将在后续重构为干净的 API。

详见 [SOURCE.md](SOURCE.md) 了解种子文件的来源与 layer 切分。

种子代码的验证逻辑由 `devel-test` 内的 pytest 覆盖（`test/pytest/unit/test_sensor_validation.py`），`seed/` 出现语法错误会让构建失败。需要 Isaac Sim 的部分（`setup_sensor` 等）是参考代码，不在功能测试范围内。

## 许可证

[Apache-2.0](LICENSE)
