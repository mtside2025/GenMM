"""
モーションの品質を詳細に分析（ポーズの変化と移動軌跡）
"""

import torch
import numpy as np
import argparse
from pathlib import Path
from dataset.bvh_motion import BVHMotion
from dataset.bvh.bvh_parser import BVH_file


def analyze_pose_and_trajectory(bvh_path):
    """
    ポーズの変化と移動軌跡を分析
    """
    print(f"Loading: {bvh_path}")
    
    # Load BVH file
    bvh_file = BVH_file(bvh_path, skeleton_conf=None, 
                       requires_contact=False, joint_reduction=False, auto_scale=True)
    
    joint_pos = bvh_file.joint_position()  # (T, J, 3)
    T, J, _ = joint_pos.shape
    
    # ルートポジション（Hips）
    root_pos = joint_pos[:, 0, :]  # (T, 3)
    
    # ルートの移動速度
    root_vel = torch.zeros_like(root_pos)
    root_vel[1:] = root_pos[1:] - root_pos[:-1]
    root_speed = torch.sqrt(root_vel[:, 0]**2 + root_vel[:, 2]**2)
    
    # 各ジョイントの平均移動量（ポーズの変化を測定）
    # ルートからの相対位置
    relative_pos = joint_pos - root_pos.unsqueeze(1)  # (T, J, 3)
    
    # フレーム間でのポーズ変化
    pose_change = torch.zeros(T-1)
    for t in range(1, T):
        # 各ジョイントの相対位置の変化量
        diff = relative_pos[t] - relative_pos[t-1]
        # 全ジョイントの平均変化量
        pose_change[t-1] = torch.norm(diff, dim=-1).mean()
    
    print(f"\n=== ポーズと移動軌跡の分析 ===")
    print(f"総フレーム数: {T}")
    
    # 区間ごとの分析
    intervals = [
        (0, 20, "フレーム 0-20"),
        (20, 40, "フレーム 20-40"),
        (40, 60, "フレーム 40-60"),
        (60, 80, "フレーム 60-80"),
        (80, 100, "フレーム 80-100"),
        (100, 120, "フレーム 100-120"),
        (120, 140, "フレーム 120-140"),
        (140, 160, "フレーム 140-160"),
        (160, T-1, f"フレーム 160-{T-1}"),
    ]
    
    print(f"\n区間ごとの分析:")
    print(f"{'区間':<20} {'ルート速度':<15} {'ポーズ変化':<15} {'状態'}")
    print("-" * 70)
    
    for start, end, label in intervals:
        if start >= T-1 or end > T:
            continue
        
        avg_root_speed = root_speed[start:end].mean().item()
        avg_pose_change = pose_change[start:end].mean().item()
        
        # 判定基準
        # ポーズ変化が小さい（<0.001）= 静止ポーズ
        # ルート速度が大きい（>0.02）= 移動している
        
        if avg_pose_change < 0.001 and avg_root_speed > 0.02:
            status = "⚠ 静止ポーズで移動"
        elif avg_pose_change < 0.001:
            status = "静止"
        elif avg_root_speed < 0.01:
            status = "⚠ 移動なし"
        else:
            status = "正常"
        
        print(f"{label:<20} {avg_root_speed:>7.4f} m/frame {avg_pose_change:>7.4f}      {status}")
    
    # 移動方向の分析
    print(f"\n移動方向の分析:")
    print(f"{'区間':<20} {'X方向':<12} {'Z方向':<12} {'方向角度':<12} {'状態'}")
    print("-" * 70)
    
    for start, end, label in intervals:
        if start >= T or end > T:
            continue
        
        # この区間での移動ベクトル
        movement = root_pos[end-1] - root_pos[start]
        dx = movement[0].item()
        dz = movement[2].item()
        
        # 方向角度（度）
        angle = np.arctan2(dz, dx) * 180 / np.pi
        
        # 全体の主要な移動方向（最初から最後まで）
        total_movement = root_pos[-1] - root_pos[0]
        main_angle = np.arctan2(total_movement[2].item(), total_movement[0].item()) * 180 / np.pi
        
        # 方向のずれ
        angle_diff = abs(angle - main_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        if angle_diff > 30:
            status = "⚠ 方向ずれ大"
        elif angle_diff > 15:
            status = "⚠ 方向ずれ"
        else:
            status = "正常"
        
        print(f"{label:<20} {dx:>7.4f} m    {dz:>7.4f} m    {angle:>7.1f}°     {status}")
    
    print(f"\n全体の移動:")
    total_movement = root_pos[-1] - root_pos[0]
    total_dist = torch.sqrt(total_movement[0]**2 + total_movement[2]**2).item()
    print(f"  総移動距離: {total_dist:.4f} m")
    print(f"  X方向: {total_movement[0]:.4f} m")
    print(f"  Z方向: {total_movement[2]:.4f} m")
    print(f"  主要方向: {main_angle:.1f}°")
    
    # 問題のあるフレームを特定
    print(f"\n問題のあるフレーム:")
    problem_frames = []
    for t in range(len(pose_change)):
        if pose_change[t] < 0.001 and root_speed[t] > 0.02:
            problem_frames.append(t)
    
    if problem_frames:
        # 連続する区間を検出
        segments = []
        start = problem_frames[0]
        for i in range(1, len(problem_frames)):
            if problem_frames[i] != problem_frames[i-1] + 1:
                segments.append((start, problem_frames[i-1]))
                start = problem_frames[i]
        segments.append((start, problem_frames[-1]))
        
        print(f"  静止ポーズで移動している区間:")
        for start, end in segments:
            length = end - start + 1
            if length >= 3:
                print(f"    フレーム {start}-{end} ({length}フレーム)")
    else:
        print(f"  問題なし")


def main():
    parser = argparse.ArgumentParser(description='ポーズと移動軌跡の品質分析')
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='入力BVHファイルパス')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return
    
    analyze_pose_and_trajectory(str(input_path))


if __name__ == '__main__':
    main()
