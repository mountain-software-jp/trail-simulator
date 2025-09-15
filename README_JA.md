# **トレイルランニングレース渋滞シミュレーター**

## **概要**

このプロジェクトは、GPXコースデータとモンテカルロ法を用いて、トレイルランニングレースにおけるランナーの渋滞をシミュレーション・分析するための一連のPythonスクリプトです。

追い越しが困難な狭いシングルトラック区間での渋滞をモデル化することで、より現実的な予測を目指す点が特徴です。主な目的は、参加者数やスタート時間などの要因がレースに与える影響を評価し、エイドステーションのリソース配分計画を支援することで、レースディレクターや主催者が情報に基づいた意思決定を行えるようにすることです。

### サンプル

#### ランナー分布のスナップショットグラフ

![](sample/runner_distribution_snapshot_500runners_active.png)

#### エイドステーションの渋滞グラフ

![](sample/aid_station_congestion.png)

#### ドットアニメーションのGIF

![](sample/dot_animation_sample.gif)

## **免責事項**

このシミュレーターは、簡略化された物理モデルと統計的な仮定に基づいています。そのため、シミュレーション結果は**近似値**として捉えるべきであり、実際のレースコンディションを完全または正確に表現するものではありません。

天候、トレイルの状態、個々のランナーの体調、装備の問題、DNF（途中棄権）など、このシミュレーションではモデル化されていない多くの予測不可能な要因が実際のレースに影響を与える可能性があります。このツールの使用によって生じたいかなる損害や損失についても、作成者は一切の責任を負いません。

## **主な機能**

*   GPXファイルからコース情報（距離、標高、勾配）を抽出します。
*   各ランナーのペースが正規分布に従うモンテカルロシミュレーションを実装しています。
*   コースのキャパシティ（例：シングルトラック）に基づいた渋滞モデルを特徴としています。
*   「スナップショット分析」により、特定の時刻における全体のランナー分布を可視化します。
*   「チェックポイント分析」により、特定の地点（例：エイドステーション）での通過時間を分析し、渋滞のピークを可視化します。

## **セットアップ**

### **前提条件**

これらのスクリプトを実行するには、以下のPythonライブラリが必要です。

*   gpxpy
*   pandas
*   numpy
*   matplotlib

以下のコマンドで、これらすべてを一度にインストールできます。

```shell
pip install gpxpy pandas numpy matplotlib
```

## **使用方法**

ワークフローは、スクリプトを順番に使用する4つの主要なステップで構成されます。

[GPXファイル] -> (1. gpx_parser.py) -> [コースCSV] -> (2. single_track_simulation.py) -> [シミュレーション結果CSV] -> (3. & 4. 分析スクリプト) -> [分析グラフ]

### **ステップ1：GPXファイルからコースデータCSVを作成する**

まず、レースのGPXファイルを、他のスクリプトが読み取れるCSV形式に変換します。

**コマンド**

```shell
python src/gpx_parser.py [path/to/your/gpx_file.gpx] [options]
```

**オプション**

*   `-o, --output`: 出力CSVファイルのパス。指定しない場合、デフォルトの名前（例：`your_gpx_file_course_data.csv`）が生成されます。

**実行例**

```shell
python src/gpx_parser.py your_race.gpx -o my_course.csv

# 出力
my_course.csv という名前のファイルが作成されます。
```

### **ステップ2 & 3: シミュレーションと分析の実行**

シミュレーションと分析の全パラメータは、単一のプロジェクトJSONファイルで管理します。

**プロジェクトJSONファイルの構造**

`simulation` と `analysis` の2つの主要なセクションで構成されます。

```json
{
  "simulation": {
    "settings": {
      "runners": 500,
      "avg_pace_min_per_km": 12,
      "std_dev_pace": 1.5,
      "time_limit_hours": 26
    },
    "wave_start": {
      "groups": 3,
      "interval_minutes": 10
    },
    "cutoffs": [
      {"distance_km": 39, "time_hours": 10},
      {"distance_km": 66, "time_hours": 15}
    ],
    "single_track_sections": [
      {"range_km": [5, 8], "capacity": 2}
    ]
  },
  "analysis": {
    "runner_distribution": {
      "snapshot_times_hours": [5, 10, 15, 20],
      "output_filename": "runner_distribution_snapshot.png"
    },
    "aid_station": {
      "stations_km": [39, 66],
      "output_filename": "aid_station_congestion.png"
    },
    "dot_animation": {
      "output_filename": "dot_animation.html",
      "time_step_minutes": 15,
      "max_runners_to_display": 500
    }
  }
}
```

**実行ワークフロー**

1.  **シミュレーションの実行**
    ```shell
    python src/single_track_simulation.py [course.csv] [project.json] -o [simulation_results.csv]
    ```
2.  **分析の実行**
    ```shell
    # ランナー分布
    python src/runner_distribution_analysis.py [simulation_results.csv] [course.csv] [project.json]
    
    # エイドステーション渋滞
    python src/aid_station_analysis.py [simulation_results.csv] [project.json]
    
    # ドットアニメーション
    python src/create_dot_animation.py [simulation_results.csv] [course.csv] [project.json]
    ```

**実行例**

```shell
# 1. コースデータを作成
python src/gpx_parser.py your_race.gpx -o my_course.csv

# 2. シミュレーションを実行
python src/single_track_simulation.py my_course.csv project_params.json -o my_simulation.csv

# 3. すべての分析を実行
python src/runner_distribution_analysis.py my_simulation.csv my_course.csv project_params.json
python src/aid_station_analysis.py my_simulation.csv project_params.json
python src/create_dot_animation.py my_simulation.csv my_course.csv project_params.json

# 出力
project_params.jsonの`analysis`セクションで指定されたファイル名で、各分析結果が保存されます。
```

## **ライセンス**

このプロジェクトは[MITライセンス](https://www.google.com/search?q=LICENSE)の下で公開されています。
