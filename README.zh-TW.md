# asset_converter

URDF + TOML 轉 USD 轉換工具。在官方 urdf-usd-converter 基礎上補充：TOML 驅動的 DriveAPI、感測器 prim 建立、world link 處理（fixed vs floating）、凹面碰撞體前處理。

## 目前狀態

早期階段。包含設計規劃（issue #1）及從 isaac repo 擷取的感測器種子程式碼。

## 感測器種子程式碼

從 ycpss91255-lab/isaac @ c068e3a 擷取。感測器建立程式碼（Camera / LiDAR / IMU USD prims）將在後續重構為乾淨的 API。

詳見 [SOURCE.md](SOURCE.md) 了解種子檔案的來源與 layer 切分。

種子程式碼的驗證邏輯由 `devel-test` 內的 pytest 涵蓋（`test/pytest/unit/test_sensor_validation.py`），`seed/` 出現語法錯誤會讓建置失敗。需要 Isaac Sim 的部分（`setup_sensor` 等）是參考程式碼，不在功能測試範圍內。

## 授權條款

[Apache-2.0](LICENSE)
