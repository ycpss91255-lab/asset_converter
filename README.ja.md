# asset_converter

URDF + TOML から USD への変換ツール。公式 urdf-usd-converter を補完し、TOML 駆動の DriveAPI、センサー prim 作成、world link 処理（fixed vs floating）、凹面コリジョン前処理を追加。

## 現在の状態

初期段階。設計（issue #1）および isaac リポジトリから抽出したセンサーシードコードを含む。

## センサーシードコード

ycpss91255-lab/isaac @ c068e3a から抽出。センサー作成コード（Camera / LiDAR / IMU USD prims）は、今後クリーンな API にリファクタリング予定。

詳細は [SOURCE.md](SOURCE.md) を参照（シードファイルの出典とレイヤー分割）。

シードコードの検証ロジックは `devel-test` の pytest（`test/pytest/unit/test_sensor_validation.py`）でカバーされ、`seed/` に構文エラーがあるとビルドが失敗します。Isaac Sim が必要な部分（`setup_sensor` など）は参考コードであり、機能テストの対象外です。

## ライセンス

[Apache-2.0](LICENSE)
