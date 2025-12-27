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
        
        # Get target speeds
        target_speed = self.profile_constraint.target_speeds[:synthesized.shape[-1]].to(synthesized.device)
        
        # Compute average speed to normalize the loss
        avg_speed = current_speed.mean()
        if avg_speed < 1e-6:
            return torch.tensor(0.0, device=synthesized.device)
        
        # Compute relative speed error
        # target_speed represents desired multipliers (e.g., 1.5 = 1.5x original speed)
        # We want to penalize deviations from these multipliers
        speed_ratio = current_speed / (avg_speed + 1e-6)
        target_ratio = target_speed / target_speed.mean()
        
        # MSE loss between current and target speed ratios
        loss = torch.mean((speed_ratio - target_ratio) ** 2)
        
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
