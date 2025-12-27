"""
Utility functions for converting between velocity and position representations
"""

import torch


def velocity_to_position(motion_data):
    """
    Convert velocity representation to position representation.
    
    Args:
        motion_data: (batch, channels, frames) tensor with velocity representation
                    Last 3 channels are: [ΔX, Y, ΔZ]
                    BVH velocity format:
                        velo[0] = pos[1] (stored for reconstruction)
                        velo[i] = pos[i] - pos[i-1] for i > 0
    
    Returns:
        Position representation where last 3 channels are: [X, Y, Z]
        Reconstruction:
            pos[0] = 0 (origin, stored separately as begin_pos in BVH)
            pos = cumsum([0, velo[0], velo[1], ...])
            => pos[0] = 0, pos[1] = velo[0], pos[2] = velo[0] + velo[1], ...
    """
    result = motion_data.clone()
    
    # Last 3 channels: ΔX, Y, ΔZ
    vel_x = motion_data[:, -3, :]  # ΔX (horizontal velocity)
    pos_y = motion_data[:, -2, :]  # Y (already position, vertical)
    vel_z = motion_data[:, -1, :]  # ΔZ (horizontal velocity)
    
    # Reconstruct position using BVH's to_position logic:
    # Set pos[0] = 0 (begin_pos), then cumsum
    pos_x = vel_x.clone()
    pos_z = vel_z.clone()
    pos_x[:, 0] = 0  # begin_pos
    pos_z[:, 0] = 0
    pos_x = torch.cumsum(pos_x, dim=-1)
    pos_z = torch.cumsum(pos_z, dim=-1)
    
    # Update last 3 channels with positions
    result[:, -3, :] = pos_x
    result[:, -2, :] = pos_y  # Already position
    result[:, -1, :] = pos_z
    
    return result


def position_to_velocity(motion_data):
    """
    Convert position representation to velocity representation.
    
    Args:
        motion_data: (batch, channels, frames) tensor with position representation
                    Last 3 channels are: [X, Y, Z]
                    Position[0] = 0 (origin)
    
    Returns:
        Velocity representation where last 3 channels are: [ΔX, Y, ΔZ]
        BVH velocity format:
            velo[0] = pos[1]
            velo[i] = pos[i] - pos[i-1] for i > 0
    """
    result = motion_data.clone()
    
    # Last 3 channels: X, Y, Z
    pos_x = motion_data[:, -3, :]  # X (horizontal position)
    pos_y = motion_data[:, -2, :]  # Y (vertical position)
    pos_z = motion_data[:, -1, :]  # Z (horizontal position)
    
    # Convert positions to velocities
    vel_x = torch.zeros_like(pos_x)
    vel_z = torch.zeros_like(pos_z)
    
    vel_x[:, 0] = pos_x[:, 1]  # velo[0] = pos[1]
    vel_x[:, 1:] = pos_x[:, 1:] - pos_x[:, :-1]  # velo[i] = pos[i] - pos[i-1]
    
    vel_z[:, 0] = pos_z[:, 1]  # velo[0] = pos[1]
    vel_z[:, 1:] = pos_z[:, 1:] - pos_z[:, :-1]
    
    # Update last 3 channels with velocities
    result[:, -3, :] = vel_x
    result[:, -2, :] = pos_y  # Keep Y as position
    result[:, -1, :] = vel_z
    
    return result
