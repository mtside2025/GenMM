"""
Velocity Profile Loss for temporal consistency.
Penalizes deviations from target velocity profile during optimization.
"""
import torch
import torch.nn as nn


class VelocityProfileLoss(nn.Module):
    """
    Loss function that penalizes deviations from a target velocity profile.
    
    This loss is added to the patch coherence loss to guide the optimization
    toward motions that match the desired velocity profile.
    """
    
    def __init__(self, profile_constraint, weight=1.0):
        """
        Args:
            profile_constraint: VelocityProfileConstraint instance
            weight: Weight of velocity loss relative to patch coherence loss
        """
        super(VelocityProfileLoss, self).__init__()
        self.profile_constraint = profile_constraint
        self.weight = weight
    
    def forward(self, synthesized, use_velo=True):
        """
        Compute velocity profile loss.
        
        Args:
            synthesized: (1, C, T) tensor of synthesized motion
            use_velo: Whether data uses velocity representation
        
        Returns:
            Scalar loss value
        """
        if not use_velo or self.profile_constraint is None:
            return torch.tensor(0.0, device=synthesized.device)
        
        # Extract velocity channels (last 3 channels: ΔX, Y, ΔZ)
        vel_x = synthesized[:, -3, :]  # ΔX (horizontal velocity)
        vel_z = synthesized[:, -1, :]  # ΔZ (horizontal velocity)
        
        # Compute current horizontal speed at each frame
        current_speed = torch.sqrt(vel_x**2 + vel_z**2)
        
        # Get target speeds and interpolate to current sequence length
        current_len = synthesized.shape[-1]
        full_target_speeds = self.profile_constraint.target_speeds.to(synthesized.device)
        
        if current_len != len(full_target_speeds):
            # Interpolate target speeds to match current sequence length
            target_speed = torch.nn.functional.interpolate(
                full_target_speeds.unsqueeze(0).unsqueeze(0),
                size=current_len,
                mode='linear',
                align_corners=True
            ).squeeze()
        else:
            target_speed = full_target_speeds[:current_len]
        
        # Compute average speed to normalize
        avg_speed = current_speed.mean()
        if avg_speed < 1e-6:
            return torch.tensor(0.0, device=synthesized.device)
        
        # Simple MSE loss: encourage each frame's speed to match target
        # Normalize by average speed to make loss scale-invariant
        normalized_current = current_speed / (avg_speed + 1e-6)
        normalized_target = target_speed / (target_speed.mean() + 1e-6)
        
        loss = torch.mean((normalized_current - normalized_target) ** 2)
        
        return self.weight * loss


class CombinedLoss(nn.Module):
    """
    Combines patch coherence loss with velocity profile loss.
    """
    
    def __init__(self, patch_loss, velocity_loss=None):
        """
        Args:
            patch_loss: PatchCoherentLoss instance
            velocity_loss: VelocityProfileLoss instance or None
        """
        super(CombinedLoss, self).__init__()
        self.patch_loss = patch_loss
        self.velocity_loss = velocity_loss
    
    def forward(self, X, Ys, dist_wrapper=None, ext=None, return_blended_results=False, use_velo=True):
        """
        Forward pass combining both losses.
        
        Args:
            X: Input motion tensor
            Ys: Target motion tensors
            dist_wrapper: Distance function wrapper
            ext: Extra configurations
            return_blended_results: Whether to return blended results
            use_velo: Whether data uses velocity representation
        
        Returns:
            If return_blended_results: (blended_motion, total_loss)
            Else: total_loss
        """
        if return_blended_results:
            blended, patch_loss_val = self.patch_loss(X, Ys, dist_wrapper, ext, return_blended_results=True)
            
            # Compute velocity loss on blended result
            if self.velocity_loss is not None:
                vel_loss_val = self.velocity_loss(blended, use_velo=use_velo)
                total_loss = patch_loss_val + vel_loss_val
            else:
                total_loss = patch_loss_val
            
            return blended, total_loss
        else:
            patch_loss_val = self.patch_loss(X, Ys, dist_wrapper, ext, return_blended_results=False)
            
            # Compute velocity loss on current X
            if self.velocity_loss is not None:
                vel_loss_val = self.velocity_loss(X, use_velo=use_velo)
                total_loss = patch_loss_val + vel_loss_val
            else:
                total_loss = patch_loss_val
            
            return total_loss
    
    def clean_cache(self):
        """Clean cached data in patch loss."""
        if hasattr(self.patch_loss, 'clean_cache'):
            self.patch_loss.clean_cache()
