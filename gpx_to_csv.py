import gpxpy
import pandas as pd
import numpy as np
import argparse
import os

def parse_gpx(file_path):
    """
    GPXファイルを解析し、コース情報をDataFrameとして返す。

    Args:
        file_path (str): GPXファイルへのパス

    Returns:
        pandas.DataFrame: コース情報を含むDataFrame
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        return None
    except Exception as e:
        print(f"GPXファイルの解析中にエラーが発生しました: {e}")
        return None

    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # GPXファイル内のdistance拡張タグから距離を取得
                distance_extension = [ext for ext in point.extensions if 'distance' in ext.tag]
                distance = float(distance_extension[0].text) if distance_extension else 0
                points.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'distance': distance # スタートからの累積距離
                })

    if not points:
        print("警告: GPXファイルからトラックポイントが見つかりませんでした。")
        return pd.DataFrame()

    df = pd.DataFrame(points)
    
    # 各区間の距離と標高差、勾配を計算
    df['segment_distance'] = df['distance'].diff().fillna(0)
    df['elevation_diff'] = df['elevation'].diff().fillna(0)
    
    # 距離が0の区間でのゼロ除算を避ける
    df['gradient'] = np.where(df['segment_distance'] > 0, (df['elevation_diff'] / df['segment_distance']) * 100, 0)

    return df

def main(gpx_filepath):
    """
    メイン処理。GPXファイルを解析し、CSVとして保存する。
    """
    print(f"'{gpx_filepath}' を解析しています...")
    course_df = parse_gpx(gpx_filepath)

    if course_df is not None and not course_df.empty:
        # 出力ファイル名を生成 (例: my_race.gpx -> my_race_course_data.csv)
        base_filename = os.path.splitext(os.path.basename(gpx_filepath))[0]
        output_csv_path = f"{base_filename}_course_data.csv"
        
        # 結果をCSVファイルとして保存
        course_df.to_csv(output_csv_path, index=False)

        # 最初の数行を表示して確認
        print("\nコースデータの最初の5行:")
        print(course_df.head())
        print(f"\nコース全長: {course_df['distance'].iloc[-1] / 1000:.2f} km")
        print(f"データは '{output_csv_path}' に保存されました。")

if __name__ == '__main__':
    # コマンドライン引数を解析するための設定
    parser = argparse.ArgumentParser(
        description='Parse a GPX file and save its track data as a CSV file.'
    )
    # 必須の引数としてGPXファイルのパスを追加
    parser.add_argument(
        'gpx_filepath', 
        type=str, 
        help='Path to the GPX file to be parsed.'
    )
    
    # 引数を解析
    args = parser.parse_args()
    
    # メイン処理を呼び出し
    main(args.gpx_filepath)
