import pandas as pd
import numpy as np
import argparse

def define_course_capacity(course_df, single_track_sections):
    """コースデータにキャパシティ列を追加する"""
    # デフォルトは広い道（キャパシティ大）
    course_df['capacity'] = 1000 
    
    for section in single_track_sections:
        start_km, end_km, capacity = section['range_km'][0], section['range_km'][1], section['capacity']
        start_m, end_m = start_km * 1000, end_km * 1000
        # 指定された区間のキャパシティを設定
        course_df.loc[(course_df['distance'] >= start_m) & (course_df['distance'] <= end_m), 'capacity'] = capacity
        print(f"コースの {start_km}km から {end_km}km 地点までをキャパシティ {capacity} のシングルトラックとして設定しました。")
    return course_df

def run_congestion_simulation(num_runners, avg_pace_min_per_km, std_dev_pace, time_limit_hours, course_df):
    """
    【渋滞モデル版】シングルトラックの混雑を考慮したシミュレーション
    """
    print("渋滞モデルを組み込んだシミュレーションを開始します...")
    
    # --- ランナーの準備 ---
    runners_pace_sec_per_meter = np.random.normal(
        loc=avg_pace_min_per_km * 60 / 1000, 
        scale=std_dev_pace * 60 / 1000, 
        size=num_runners
    )
    
    # --- シミュレーション設定 ---
    time_step_sec = 10
    total_steps = time_limit_hours * 3600 // time_step_sec
    
    # --- コースを小さな「セル」に分割 ---
    cell_size_m = 10  # 10mごとに区切る
    max_distance_m = course_df['distance'].iloc[-1]
    num_cells = int(np.ceil(max_distance_m / cell_size_m))
    
    # 各セルの現在の人数
    cell_occupancy = np.zeros(num_cells, dtype=int)
    
    # 各セルの最大人数（キャパシティ）
    cell_capacity = np.zeros(num_cells, dtype=int)
    for i in range(num_cells):
        cell_start_m = i * cell_size_m
        # セルの中間点の情報からキャパシティを代表させる
        point_in_cell = course_df.iloc[(course_df['distance'] - (cell_start_m + cell_size_m/2)).abs().argsort()[:1]]
        cell_capacity[i] = point_in_cell['capacity'].values[0]

    # --- シミュレーションデータ記録用 ---
    runner_positions = np.zeros((total_steps, num_runners))
    
    # --- シミュレーションループ ---
    for t in range(1, total_steps):
        runner_positions[t] = runner_positions[t-1]
        
        # セルの人数をリセット
        cell_occupancy.fill(0)
        # 現在の全ランナーの位置からセルの人数を更新
        current_cells = (runner_positions[t] / cell_size_m).astype(int)
        np.add.at(cell_occupancy, current_cells[current_cells < num_cells], 1)

        # ランナーを速い順にソートして処理（速い人が優先的に進む）
        sorted_runner_indices = np.argsort(runner_positions[t])[::-1]

        for r in sorted_runner_indices:
            current_pos = runner_positions[t, r]
            if current_pos >= max_distance_m: continue # ゴール済み

            # 1. 本来のペースで進める理想の距離を計算
            # ...（勾配によるペース調整は、ここでは簡略化のため省略）
            ideal_distance_moved = time_step_sec / runners_pace_sec_per_meter[r]
            ideal_next_pos = current_pos + ideal_distance_moved

            # 2. 進もうとする先のセルが空いているかチェック
            current_cell_idx = int(current_pos / cell_size_m)
            ideal_next_cell_idx = int(ideal_next_pos / cell_size_m)
            
            allowed_pos = ideal_next_pos

            # セルをまたぐ場合、先のセルのキャパシティをチェック
            for cell_idx in range(current_cell_idx + 1, ideal_next_cell_idx + 1):
                if cell_idx >= num_cells: break
                
                if cell_occupancy[cell_idx] >= cell_capacity[cell_idx]:
                    # 定員オーバーの場合、そのセルの手前までしか進めない
                    allowed_pos = cell_idx * cell_size_m - 0.01 # セルの境界ギリギリ
                    break
                else:
                    # 進める場合は、そのセルの人数を1人増やす
                    cell_occupancy[cell_idx] += 1
            
            # 3. 最終的な位置を更新
            runner_positions[t, r] = min(allowed_pos, max_distance_m)

    # --- 結果をDataFrameに変換 ---
    results_df = pd.DataFrame(runner_positions, columns=[f'runner_{i+1}' for i in range(num_runners)])
    results_df['time_sec'] = np.arange(total_steps) * time_step_sec
    return results_df


if __name__ == '__main__':
    # --- コマンドライン引数の設定 ---
    parser = argparse.ArgumentParser(description='Run a trail running simulation with a congestion model.')
    parser.add_argument('course_data_csv', type=str, help='Path to the course data CSV file (generated from GPX).')
    # --- ★★★ シミュレーションパラメータを引数として追加 ★★★ ---
    parser.add_argument('-n', '--runners', type=int, default=500, help='Number of runners. Default: 500')
    parser.add_argument('-p', '--avg_pace', type=float, default=10.0, help='Average pace in minutes per km. Default: 10.0')
    parser.add_argument('-s', '--std_dev', type=float, default=1.5, help='Standard deviation of pace. Default: 1.5')
    parser.add_argument('-t', '--time_limit', type=int, default=24, help='Time limit in hours. Default: 24')

    args = parser.parse_args()

    # --- ★★★ シングルトラック区間の設定 ★★★ ---
    # レースコースに合わせて、この部分を自由に定義してください
    single_track_definitions = [
        {'range_km': (5, 8), 'capacity': 2},    # 5km～8km地点は、定員2名
        {'range_km': (20, 22.5), 'capacity': 1}, # 20km～22.5km地点は、定員1名の激狭区間
    ]

    # --- 実行 ---
    # 1. GPXからコースデータを読み込む (引数で指定されたファイルを使用)
    try:
        course_data = pd.read_csv(args.course_data_csv)
    except FileNotFoundError:
        print(f"エラー: ファイル '{args.course_data_csv}' が見つかりません。")
        exit()

    # 2. コースにキャパシティ情報を追加
    course_data_with_capacity = define_course_capacity(course_data, single_track_definitions)
    # 3. 渋滞モデルでシミュレーションを実行
    simulation_results = run_congestion_simulation(
        args.runners, args.avg_pace, args.std_dev, args.time_limit, course_data_with_capacity
    )
    # 4. 結果を保存
    output_filename = f'congestion_sim_results_{args.runners}runners.csv'
    simulation_results.to_csv(output_filename, index=False)
    print(f"\nシミュレーションが完了しました。結果を '{output_filename}' に保存しました。")

