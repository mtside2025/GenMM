"""
Velocity Profile Constraint for Temporal Motion Consistency

This module provides velocity profile constraints to maintain smooth
velocity transitions in generated motion sequences.
"""

import torch
import numpy as np


class VelocityProfileConstraint:
    """
    Enforces velocity profile constraints on generated motion.
    
    This class computes target velocity profiles and scales motion velocities
    to match the desired speed transitions (e.g., gradual deceleration from
    walking to stopping).
    
    Args:
        total_frames: Total number of frames in the motion
        profile_type: Type of velocity profile
            - 'linear_decel': Linear deceleration
            - 'smooth_decel': Smooth deceleration with ease-out curve
            - 'linear_accel': Linear acceleration
            - 'constant': Constant velocity
        start_speed: Starting velocity in m/s
        end_speed: Ending velocity in m/s
        device: torch device ('cuda' or 'cpu')
    
    Example:
        >>> constraint = VelocityProfileConstraint(
        ...     total_frames=100,
        ...     profile_type='smooth_decel',
        ...     start_speed=1.5,
        ...     end_speed=0.0
        ... )
        >>> # Apply to synthesized motion
        >>> synthesized = constraint.apply_constraint(synthesized, use_velo=True)
    """
    
    def __init__(self, total_frames, profile_type='linear_decel', 
                 start_speed=1.0, end_speed=0.0, device='cuda'):
        self.total_frames = total_frames
        self.profile_type = profile_type
        self.start_speed = start_speed
        self.end_speed = end_speed
        self.device = torch.device(device)
        
        # Compute target speed for each frame
        self.target_speeds = self._compute_profile()
        self.target_speeds = self.target_speeds.to(self.device)
    
    def _compute_profile(self):
        """Compute velocity profile based on profile type."""
        t = torch.linspace(0, 1, self.total_frames)
        
        if self.profile_type == 'linear_decel' or self.profile_type == 'linear_accel':
            # Linear interpolation: v(t) = v0 + (v1 - v0) * t
            speeds = self.start_speed + (self.end_speed - self.start_speed) * t
        
        elif self.profile_type == 'smooth_decel':
            # Smooth deceleration with ease-out curve
            # v(t) = v0 + (v1 - v0) * (1 - (1-t)^2)
            speeds = self.start_speed + (self.end_speed - self.start_speed) * (1 - (1 - t)**2)
        
        elif self.profile_type == 'smooth_accel':
            # Smooth acceleration with ease-in curve
            # v(t) = v0 + (v1 - v0) * t^2
            speeds = self.start_speed + (self.end_speed - self.start_speed) * (t**2)
        
        elif self.profile_type == 'constant':
            # Constant velocity
            speeds = torch.ones_like(t) * self.start_speed
        
        elif self.profile_type == 'ease_in_out':
            # Smooth acceleration and deceleration
            # v(t) = v0 + (v1 - v0) * (3t^2 - 2t^3)
            speeds = self.start_speed + (self.end_speed - self.start_speed) * (3 * t**2 - 2 * t**3)
        
        else:
            raise ValueError(f"Unknown profile type: {self.profile_type}. "
                           f"Supported types: linear_decel, linear_accel, smooth_decel, "
                           f"smooth_accel, constant, ease_in_out")
        
        return speeds
    
    def apply_constraint(self, synthesized, use_velo=True):
        """
        Apply velocity constraint to synthesized motion.
        
        Simple velocity scaling: multiply the horizontal velocity by the target speed profile.
        
        Args:
            synthesized: (1, C, T) tensor of synthesized motion
            use_velo: Whether the data uses velocity representation
        
        Returns:
            Constrained motion tensor with adjusted velocities
        """
        if not use_velo:
            # If using position representation, velocity constraint doesn't apply directly
            return synthesized
        
        # Clone to avoid modifying original
        constrained = synthesized.clone()
        
        # Extract velocity channels (last 3 channels: ΔX, Y, ΔZ)
        vel_x = constrained[:, -3, :]  # ΔX (horizontal velocity)
        vel_z = constrained[:, -1, :]  # ΔZ (horizontal velocity)
        
        # Get target speeds and interpolate to current sequence length (for pyramid optimization)
        current_len = synthesized.shape[-1]
        full_target_speeds = self.target_speeds.to(synthesized.device)
        
        if current_len != len(full_target_speeds):
            # Interpolate target speeds to match current sequence length
            import torch.nn.functional as F
            target_speed = F.interpolate(
                full_target_speeds.unsqueeze(0).unsqueeze(0),
                size=current_len,
                mode='linear',
                align_corners=True
            ).squeeze()
        else:
            target_speed = full_target_speeds
        
        # Apply scaling to horizontal velocity components
        # target_speed is a multiplier (e.g., 1.5 = 1.5x faster)
        constrained[:, -3, :] = vel_x * target_speed  # ΔX
        constrained[:, -1, :] = vel_z * target_speed  # ΔZ
        # Note: Y (vertical) is not scaled to preserve jumps/stairs
        
        return constrained
    
    def get_speed_range(self, frame_idx, tolerance=0.2):
        """
        Get acceptable speed range for a specific frame.
        
        Args:
            frame_idx: Frame index
            tolerance: Tolerance as fraction of target speed (0.2 = ±20%)
        
        Returns:
            (min_speed, max_speed) tuple
        """
        if frame_idx >= len(self.target_speeds):
            frame_idx = len(self.target_speeds) - 1
        
        target_speed = self.target_speeds[frame_idx].item()
        min_speed = max(0, target_speed * (1 - tolerance))
        max_speed = target_speed * (1 + tolerance)
        
        return (min_speed, max_speed)
    
    def visualize_profile(self, save_path=None):
        """
        Visualize the velocity profile.
        
        Args:
            save_path: Optional path to save the plot
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not available. Skipping visualization.")
            return
        
        speeds = self.target_speeds.cpu().numpy()
        frames = np.arange(len(speeds))
        
        plt.figure(figsize=(10, 6))
        plt.plot(frames, speeds, linewidth=2, label=f'{self.profile_type}')
        plt.xlabel('Frame')
        plt.ylabel('Speed (m/s)')
        plt.title(f'Velocity Profile: {self.profile_type}\n'
                 f'Start: {self.start_speed:.2f} m/s → End: {self.end_speed:.2f} m/s')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Velocity profile saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def __repr__(self):
        return (f"VelocityProfileConstraint("
                f"frames={self.total_frames}, "
                f"type='{self.profile_type}', "
                f"start={self.start_speed:.2f}, "
                f"end={self.end_speed:.2f})")


def parse_velocity_profile_args(velocity_profile, start_speed, end_speed, loss_weight=0.1):
    """
    Parse velocity profile arguments from command line.
    
    Args:
        velocity_profile: Profile type string or None
        start_speed: Starting speed multiplier or None
        end_speed: Ending speed multiplier or None
        loss_weight: Weight of velocity loss (default: 0.1)
    
    Returns:
        Dictionary with velocity profile configuration or None
    """
    if velocity_profile is None:
        return None
    
    config = {
        'type': velocity_profile,
        'start_speed': start_speed if start_speed is not None else 1.0,
        'end_speed': end_speed if end_speed is not None else 0.0,
        'loss_weight': loss_weight
    }
    
    return config

