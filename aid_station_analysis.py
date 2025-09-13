import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

def analyze_aid_station_congestion(csv_filepath, output_filename):
    """
    シミュレーション結果から、指定した地点のランナー通過時刻を分析し、
    混雑状況をヒストグラムで可視化する。

    Args:
        csv_filepath (str): シミュレーション結果のCSVファイルへのパス
        output_filename (str): 出力するグラフの画像ファイル名
    """
    try:
        df = pd.read_csv(csv_filepath)
        print(f"'{csv_filepath}' を正常に読み込みました。")
    except FileNotFoundError:
        print(f"エラー: ファイル '{csv_filepath}' が見つかりません。")
        return

    # --- 定点観測地点（エイドステーション）をkm単位で設定 ---
    # このリストを編集することで、分析したい地点を自由に変更できます。
    aid_stations_km = [17, 26, 46, 63, 80, 96]
    
    # --- グラフ描画の準備 ---
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(len(aid_stations_km), 1, figsize=(14, 16), sharex=True)
    fig.suptitle('Aid Station Passage Time Distribution', fontsize=20, fontweight='bold')

    # --- 各エイドステーションの通過時刻を計算・描画 ---
    for i, distance_km in enumerate(aid_stations_km):
        distance_m = distance_km * 1000
        passage_times_sec = []
        
        # runner_1, runner_2, ... の列をループ
        runner_columns = [col for col in df.columns if col.startswith('runner_')]
        for runner_col in runner_columns:
            # ランナーが指定距離を最初に超えた時点のデータを取得
            passage_event = df[df[runner_col] >= distance_m]
            
            if not passage_event.empty:
                # 最初の通過時刻（秒）を取得
                passage_time = passage_event['time_sec'].iloc[0]
                passage_times_sec.append(passage_time)
        
        if not passage_times_sec:
            print(f"{distance_km}km地点を通過したランナーはいませんでした。")
            continue

        # 秒を時間に変換
        passage_times_hours = [t / 3600 for t in passage_times_sec]
        
        # ヒストグラムを描画
        ax = axes[i]
        ax.hist(passage_times_hours, bins=50, color='teal', edgecolor='black', alpha=0.8)
        
        # 混雑のピーク時刻に線を引く
        # ヒストグラムの最頻値（最もバーが高い位置）を取得
        counts, bin_edges = np.histogram(passage_times_hours, bins=50)
        peak_time = bin_edges[np.argmax(counts)]
        ax.axvline(peak_time, color='magenta', linestyle='--', linewidth=2, label=f'Peak Time: ~{peak_time:.1f} h')

        ax.set_title(f'Congestion at {distance_km}km Point', fontsize=16)
        ax.set_ylabel('Number of Runners', fontsize=12)
        ax.legend()

    axes[-1].set_xlabel('Time Since Race Start (hours)', fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # --- グラフを画像ファイルとして保存 ---
    plt.savefig(output_filename)
    print(f"\n分析が完了しました。")
    print(f"結果のグラフを '{output_filename}' という名前で保存しました。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze aid station congestion from a race simulation CSV file.'
    )
    parser.add_argument(
        'csv_filepath', 
        type=str, 
        help='Path to the simulation result CSV file.'
    )
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='aid_station_congestion.png', 
        help='Output image file name. (default: aid_station_congestion.png)'
    )
    
    args = parser.parse_args()
    analyze_aid_station_congestion(args.csv_filepath, args.output)
