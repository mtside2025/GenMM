"""
Apply foot contact fixing to velocity-constrained motion.

This script detects foot contact and applies contact constraints to prevent foot sliding.
"""

import torch
import numpy as np
import argparse
from pathlib import Path
from dataset.bvh_motion import BVHMotion
from dataset.bvh.bvh_parser import BVH_file
from utils.contact import foot_contact, constrain_from_contact


def detect_foot_contact(bvh_file, threshold=0.018):
    """
    Detect foot contact frames based on foot velocity.
    
    Args:
        bvh_file: BVH_file object
        threshold: Velocity threshold for contact detection (m/frame)
    
    Returns:
        contact: (T, num_feet) binary contact labels
    """
    glb = bvh_file.joint_position()  # (T, J, 3)
    cid = bvh_file.skeleton.contact_id  # Foot joint indices
    
    foot_pos = glb[:, cid, :]  # (T, num_feet, 3)
    contact = foot_contact(foot_pos, threshold=threshold)
    
    return contact.numpy()


def apply_contact_constraint(bvh_file, contact=None, threshold=0.018, output_path=None):
    """
    Apply contact constraints to fix foot sliding.
    
    Args:
        bvh_file: BVH_file object
        contact: Pre-computed contact labels, or None to auto-detect
        threshold: Velocity threshold for contact detection
        output_path: Path to save fixed BVH file
    
    Returns:
        Fixed joint positions and rotations
    """
    device = torch.device('cpu')  # Use CPU for stability
    
    # Get original data
    glb = bvh_file.joint_position()  # (T, J, 3)
    rotation = bvh_file.get_rotation(repr='quat')  # (T, J, 4)
    position = bvh_file.get_position()  # (T, 3)
    cid = bvh_file.skeleton.contact_id  # Foot joint indices
    
    # Detect contact if not provided
    if contact is None:
        foot_pos = glb[:, cid, :]
        contact = foot_contact(foot_pos, threshold=threshold).numpy()
    
    contact = contact > 0.5
    
    print(f"Contact frames detected: {contact.sum()} / {contact.size}")
    print(f"Left foot: {contact[:, 0].sum()} frames")
    print(f"Right foot: {contact[:, 1].sum()} frames")
    
    # Apply contact constraint
    print("Applying contact constraints...")
    fixed_glb = constrain_from_contact(contact, glb, cid, L=5)
    
    # For now, return the fixed positions with original rotations
    # A more sophisticated approach would use IK to update rotations
    # but that requires optimization which might be slow
    
    if output_path:
        print(f"Saving fixed motion to {output_path}")
        bvh_file.writer.write(
            output_path,
            rotation,
            position,
            names=bvh_file.skeleton.names,
            repr='quat'
        )
        
        # Also save contact labels for reference
        contact_path = str(output_path) + '.contact.npy'
        np.save(contact_path, contact)
        print(f"Contact labels saved to {contact_path}")
    
    return fixed_glb, rotation, position


def main():
    parser = argparse.ArgumentParser(description='Apply foot contact fixing to BVH motion')
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='Input BVH file path')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output BVH file path (default: input_fixed.bvh)')
    parser.add_argument('--threshold', type=float, default=0.018,
                       help='Velocity threshold for contact detection (default: 0.018)')
    parser.add_argument('--no-fix', action='store_true',
                       help='Only detect and save contact, do not apply fix')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_fixed.bvh"
    
    print(f"Loading BVH file: {input_path}")
    from dataset.bvh_motion import skeleton_confs
    bvh_file = BVH_file(str(input_path), skeleton_conf=skeleton_confs['mixamo'], 
                       requires_contact=True, joint_reduction=False, auto_scale=False)
    
    if args.no_fix:
        # Only detect and save contact
        print("Detecting contact only (no fix applied)...")
        contact = detect_foot_contact(bvh_file, threshold=args.threshold)
        contact_path = str(input_path) + '.contact.npy'
        np.save(contact_path, contact)
        print(f"Contact labels saved to {contact_path}")
        print(f"Total contact frames: {contact.sum()}")
    else:
        # Apply fix
        apply_contact_constraint(
            bvh_file,
            threshold=args.threshold,
            output_path=str(output_path)
        )
        print("Done!")


if __name__ == '__main__':
    main()
