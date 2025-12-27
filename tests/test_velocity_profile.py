"""
Unit tests for Velocity Profile Constraint

Run with: python -m pytest tests/test_velocity_profile.py -v
"""

import torch
import pytest
from utils.velocity_profile import VelocityProfileConstraint, parse_velocity_profile_args


class TestVelocityProfileConstraint:
    """Test cases for VelocityProfileConstraint class."""
    
    def test_linear_decel_profile(self):
        """Test linear deceleration profile computation."""
        constraint = VelocityProfileConstraint(
            total_frames=100,
            profile_type='linear_decel',
            start_speed=2.0,
            end_speed=0.0,
            device='cpu'
        )
        
        speeds = constraint.target_speeds
        assert len(speeds) == 100
        assert abs(speeds[0].item() - 2.0) < 1e-5
        assert abs(speeds[-1].item() - 0.0) < 1e-5
        # Check monotonic decrease
        assert torch.all(speeds[:-1] >= speeds[1:])
    
    def test_smooth_decel_profile(self):
        """Test smooth deceleration profile computation."""
        constraint = VelocityProfileConstraint(
            total_frames=50,
            profile_type='smooth_decel',
            start_speed=1.5,
            end_speed=0.5,
            device='cpu'
        )
        
        speeds = constraint.target_speeds
        assert len(speeds) == 50
        assert abs(speeds[0].item() - 1.5) < 1e-5
        assert abs(speeds[-1].item() - 0.5) < 1e-5
    
    def test_constant_profile(self):
        """Test constant velocity profile."""
        constraint = VelocityProfileConstraint(
            total_frames=100,
            profile_type='constant',
            start_speed=1.0,
            end_speed=0.0,  # Should be ignored for constant profile
            device='cpu'
        )
        
        speeds = constraint.target_speeds
        assert torch.all(torch.abs(speeds - 1.0) < 1e-5)
    
    def test_apply_constraint(self):
        """Test velocity constraint application to motion data."""
        constraint = VelocityProfileConstraint(
            total_frames=10,
            profile_type='linear_decel',
            start_speed=1.0,
            end_speed=0.0,
            device='cpu'
        )
        
        # Create synthetic motion data: (1, 99, 10)
        # Last 3 channels: ΔX, Y, ΔZ
        synthesized = torch.randn(1, 99, 10)
        synthesized[:, -3, :] = 1.0  # ΔX = 1.0 m/s
        synthesized[:, -2, :] = 0.5  # Y = 0.5 m
        synthesized[:, -1, :] = 0.5  # ΔZ = 0.5 m/s
        # Current horizontal speed = sqrt(1.0^2 + 0.5^2) ≈ 1.118 m/s
        
        constrained = constraint.apply_constraint(synthesized, use_velo=True)
        
        # Check that velocities are scaled
        vel_x = constrained[:, -3, :]
        vel_z = constrained[:, -1, :]
        speed = torch.sqrt(vel_x**2 + vel_z**2)
        
        # First frame should have speed close to 1.0
        assert abs(speed[0, 0].item() - 1.0) < 0.1
        # Last frame should have speed close to 0.0
        assert speed[0, -1].item() < 0.1
    
    def test_get_speed_range(self):
        """Test speed range calculation with tolerance."""
        constraint = VelocityProfileConstraint(
            total_frames=100,
            profile_type='linear_decel',
            start_speed=2.0,
            end_speed=0.0,
            device='cpu'
        )
        
        min_speed, max_speed = constraint.get_speed_range(0, tolerance=0.2)
        assert abs(min_speed - 1.6) < 1e-5  # 2.0 * 0.8
        assert abs(max_speed - 2.4) < 1e-5  # 2.0 * 1.2
        
        min_speed, max_speed = constraint.get_speed_range(99, tolerance=0.2)
        assert abs(min_speed - 0.0) < 1e-5  # max(0, 0.0 * 0.8)
        assert abs(max_speed - 0.0) < 1e-5  # 0.0 * 1.2
    
    def test_invalid_profile_type(self):
        """Test error handling for invalid profile type."""
        with pytest.raises(ValueError):
            VelocityProfileConstraint(
                total_frames=100,
                profile_type='invalid_type',
                start_speed=1.0,
                end_speed=0.0,
                device='cpu'
            )
    
    def test_repr(self):
        """Test string representation."""
        constraint = VelocityProfileConstraint(
            total_frames=100,
            profile_type='smooth_decel',
            start_speed=1.5,
            end_speed=0.3,
            device='cpu'
        )
        
        repr_str = repr(constraint)
        assert 'VelocityProfileConstraint' in repr_str
        assert 'smooth_decel' in repr_str
        assert '1.50' in repr_str
        assert '0.30' in repr_str


class TestParseVelocityProfileArgs:
    """Test cases for parse_velocity_profile_args function."""
    
    def test_parse_with_all_args(self):
        """Test parsing with all arguments provided."""
        config = parse_velocity_profile_args('linear_decel', 1.5, 0.2)
        
        assert config is not None
        assert config['type'] == 'linear_decel'
        assert config['start_speed'] == 1.5
        assert config['end_speed'] == 0.2
    
    def test_parse_with_defaults(self):
        """Test parsing with default values."""
        config = parse_velocity_profile_args('smooth_decel', None, None)
        
        assert config is not None
        assert config['type'] == 'smooth_decel'
        assert config['start_speed'] == 1.0  # Default
        assert config['end_speed'] == 0.0    # Default
    
    def test_parse_none(self):
        """Test parsing when velocity_profile is None."""
        config = parse_velocity_profile_args(None, 1.0, 0.0)
        assert config is None


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
