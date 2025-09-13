import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse # コマンドライン引数を扱うために追加

def analyze_snapshot(simulation_csv, course_data_csv, snapshot_times_hours):
    """
    シミュレーション結果のCSVファイルを読み込み、
    特定の時刻におけるランナーの分布をヒストグラムで可視化する。
    ゴールしたランナーは分布の計算から除外する。

    Args:
        simulation_csv (str): シミュレーション結果のCSVファイルへのパス
        course_data_csv (str): コース情報（GPXから生成）のCSVファイルへのパス
        snapshot_times_hours (list): スナップショットを取得する時間（時）のリスト
    """
    try:
        df_sim = pd.read_csv(simulation_csv)
        print(f"'{simulation_csv}' を正常に読み込みました。")
    except FileNotFoundError:
        print(f"エラー: ファイル '{simulation_csv}' が見つかりません。")
        return

    try:
        df_course = pd.read_csv(course_data_csv)
        # コースの最終距離（ゴール地点）を取得
        finish_line_m = df_course['distance'].iloc[-1]
        print(f"コース全長を {finish_line_m / 1000:.2f} km に設定しました。")
    except FileNotFoundError:
        print(f"エラー: ファイル '{course_data_csv}' が見つかりません。")
        return

    # --- グラフ描画の準備 ---
    num_plots = len(snapshot_times_hours)
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(num_plots, 1, figsize=(14, 5 * num_plots), sharex=True)
    if num_plots == 1:
        axes = [axes]

    num_runners = len([col for col in df_sim.columns if col.startswith('runner_')])
    fig.suptitle(f'Snapshot of Active Runner Distribution ({num_runners} Total Runners)', fontsize=20, fontweight='bold')


    for i, time_h in enumerate(snapshot_times_hours):
        time_sec = time_h * 3600
        closest_time_index = (df_sim['time_sec'] - time_sec).abs().idxmin()
        snapshot_row = df_sim.loc[[closest_time_index]]
        
        if snapshot_row.empty:
            print(f"{time_h}時間後のデータが見つかりませんでした。")
            continue
            
        runner_positions = snapshot_row.drop(columns='time_sec').values.flatten()
        
        # --- ★★★ ここでゴールしたランナーを除外 ★★★ ---
        active_runner_positions = runner_positions[runner_positions < finish_line_m]
        num_finishers = len(runner_positions) - len(active_runner_positions)
        
        active_runner_positions_km = active_runner_positions / 1000
        
        # --- ヒストグラムの描画 ---
        ax = axes[i]
        ax.hist(active_runner_positions_km, bins=60, color='skyblue', edgecolor='black', alpha=0.8, range=(0, finish_line_m/1000))
        
        mean_pos = np.mean(active_runner_positions_km) if len(active_runner_positions_km) > 0 else 0
        ax.axvline(mean_pos, color='red', linestyle='--', linewidth=2, label=f'Average (Active): {mean_pos:.1f} km')
        
        # --- ★★★ 完走者数をグラフに表示 ★★★ ---
        ax.text(0.98, 0.95, f'Finishers: {num_finishers}',
                transform=ax.transAxes, fontsize=12,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.5', fc='gold', alpha=0.7))
        
        ax.set_title(f'Distribution After {time_h} Hours (Active Runners Only)', fontsize=16)
        ax.set_ylabel('Number of Runners', fontsize=12)
        ax.legend()
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    axes[-1].set_xlabel('Distance from Start (km)', fontsize=12)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    output_filename = f'runner_distribution_snapshot_{num_runners}runners_active.png'
    plt.savefig(output_filename)
    print(f"\n分析が完了しました。")
    print(f"結果のグラフを '{output_filename}' という名前で保存しました。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze active runner distribution from a race simulation CSV file.'
    )
    # --- 引数を2つに変更 ---
    parser.add_argument(
        'simulation_csv', 
        type=str, 
        help='Path to the simulation result CSV file.'
    )
    parser.add_argument(
        'course_data_csv', 
        type=str, 
        help='Path to the course data CSV file (generated from GPX).'
    )
    parser.add_argument(
        '-t', '--times',
        nargs='+',
        type=float,
        default=[3, 10],
        help='A list of snapshot times in hours (e.g., -t 2.5 5 12).'
    )
    
    args = parser.parse_args()
    
    # --- 引数を3つ渡すように変更 ---
    analyze_snapshot(args.simulation_csv, args.course_data_csv, args.times)

