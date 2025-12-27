"""
簡易版: 速度ベースの接地検出と位置補正
"""

import torch
import numpy as np
import argparse
from pathlib import Path
from dataset.bvh_motion import BVHMotion


def detect_and_fix_foot_sliding(bvh_path, output_path, threshold=0.020):
    """
    接地中の足が滑っている箇所を検出して修正
    
    Args:
        bvh_path: 入力BVHファイルパス
        output_path: 出力BVHファイルパス
        threshold: 接地判定の速度閾値 (m/frame)
    """
    print(f"Loading: {bvh_path}")
    
    # Load BVH file directly to get joint positions
    from dataset.bvh.bvh_parser import BVH_file
    bvh_file = BVH_file(bvh_path, skeleton_conf=None, 
                       requires_contact=False, joint_reduction=False, auto_scale=True)
    
    # Get global joint positions
    joint_pos = bvh_file.joint_position()  # (T, J, 3)
    T, J, _ = joint_pos.shape
    print(f"Joint positions shape: {joint_pos.shape}")
    print(f"Joint names: {bvh_file.skeleton._names}")
    
    # 足のジョイントを特定
    foot_names = ['LeftFoot', 'RightFoot', 'LeftToeBase', 'RightToeBase']
    foot_indices = []
    for name in foot_names:
        for i, jname in enumerate(bvh_file.skeleton._names):
            if name in jname:
                foot_indices.append((i, name))
                break
    
    print(f"\n=== 足のジョイント ===")
    for idx, name in foot_indices:
        print(f"  {name}: インデックス {idx}")
    
    # 各足ジョイントの速度を計算
    for idx, name in foot_indices:
        foot_pos = joint_pos[:, idx, :]  # (T, 3)
        
        # 速度を計算
        vel = torch.zeros_like(foot_pos)
        vel[1:] = foot_pos[1:] - foot_pos[:-1]
        
        # 水平速度（XZ平面）
        horizontal_speed = torch.sqrt(vel[:, 0]**2 + vel[:, 2]**2)
        
        print(f"\n=== {name} の速度分析 ===")
        print(f"平均速度: {horizontal_speed.mean():.4f} m/frame")
        print(f"最小速度: {horizontal_speed.min():.4f} m/frame (フレーム {horizontal_speed.argmin()})")
        print(f"最大速度: {horizontal_speed.max():.4f} m/frame (フレーム {horizontal_speed.argmax()})")
        print(f"標準偏差: {horizontal_speed.std():.4f} m/frame")
        
        # 接地検出: 速度が閾値以下のフレーム
        is_contact = horizontal_speed < threshold
        contact_frames = is_contact.nonzero(as_tuple=True)[0]
        
        print(f"接地フレーム数: {contact_frames.shape[0]} / {T}")
        
        if contact_frames.shape[0] > 0:
            # 連続する接地区間を検出
            contact_segments = []
            start = contact_frames[0].item()
            for i in range(1, len(contact_frames)):
                if contact_frames[i] != contact_frames[i-1] + 1:
                    end = contact_frames[i-1].item()
                    contact_segments.append((start, end))
                    start = contact_frames[i].item()
            contact_segments.append((start, contact_frames[-1].item()))
            
            print(f"接地区間 ({len(contact_segments)}個):")
            for start, end in contact_segments:
                length = end - start + 1
                if length >= 2:  # 2フレーム以上
                    avg_speed = horizontal_speed[start:end+1].mean()
                    max_speed = horizontal_speed[start:end+1].max()
                    print(f"  フレーム {start:3d}-{end:3d} ({length:2d}フレーム): 平均速度={avg_speed:.4f}, 最大速度={max_speed:.4f}")
    
    print(f"\n注: 完全な接地修正にはIKが必要です")
    print(f"現在の実装は解析のみです")
    
    # 元のファイルをそのまま保存（解析のみ）
    if output_path and output_path != bvh_path:
        import shutil
        shutil.copy(bvh_path, output_path)
        print(f"\nコピー完了: {output_path}")
        print(f"(修正は適用されていません - 解析のみ)")


def main():
    parser = argparse.ArgumentParser(description='足の滑り検出と解析')
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='入力BVHファイルパス')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='出力BVHファイルパス')
    parser.add_argument('--threshold', type=float, default=0.020,
                       help='接地判定の速度閾値 (m/frame, default: 0.020)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return
    
    output_path = args.output if args.output else None
    
    detect_and_fix_foot_sliding(
        str(input_path),
        output_path,
        threshold=args.threshold
    )


if __name__ == '__main__':
    main()
