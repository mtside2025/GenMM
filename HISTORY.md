# Development History

This document tracks major algorithm updates and feature additions to the GenMM system.

## 2025-12-27: Velocity Profile Constraints

### Overview
Added velocity profile control functionality to the motion generation pipeline, allowing users to specify target speed multipliers for the generated motion (e.g., 1.5x faster than the original).

### Implementation Details

#### 1. Velocity Profile Constraint (`utils/velocity_profile.py`)

**Core Algorithm:**
The velocity profile constraint works in velocity space to modify the motion's speed while preserving its character:

```python
# For each frame, calculate target speed multiplier
target_speeds = profile_function(frame_index)  # e.g., linear_decel: 1.5 → 0.5

# Apply constraint:
current_speed = sqrt(vx² + vz²)  # Current horizontal speed
if current_speed > epsilon:
    scale_factor = target_speed / current_speed
    vx_new = vx * scale_factor
    vz_new = vz * scale_factor
```

**Supported Profiles:**
- `constant`: Uniform speed multiplier throughout
- `linear_accel`: Linear acceleration from start_speed to end_speed
- `linear_decel`: Linear deceleration from start_speed to end_speed
- `ease_in_out`: Smooth acceleration/deceleration with ease curves

**Key Features:**
- Works in velocity representation (`use_velo=True`)
- Preserves motion direction (only modifies magnitude)
- Applies per-frame speed multipliers
- Handles edge cases (zero velocity frames)

#### 2. Integration with Pyramid Optimization (`GenMM.py`)

**Pyramid-Based Multi-Scale Optimization:**
GenMM uses a coarse-to-fine pyramid approach for motion synthesis:

```
Level 5 (coarsest):  [.......]  ← Start here, low resolution
Level 4:             [...............]
Level 3:             [........................]
Level 2:             [...................................]
Level 1 (finest):    [...................................................] ← Final result, velocity constraint applied here
```

**Velocity Constraint Application:**
The velocity constraint is applied **only at the finest (final) pyramid level** during the optimization iterations:

```python
def match_and_blend(self, synthesized, pyramid_level):
    for iteration in range(n_steps):
        # 1. Patch-based coherence loss (spatial similarity)
        patches = extract_patches(synthesized)
        nn_patches = find_nearest_neighbors(patches, reference_motion)
        coherence_loss = compute_patch_loss(patches, nn_patches)
        
        # 2. Apply keyframe constraints (if specified)
        if keyframes:
            synthesized = apply_keyframes(synthesized, keyframes)
        
        # 3. Apply velocity profile constraint (ONLY at final level)
        if velocity_constraint and pyramid_level == total_levels - 1:
            synthesized = velocity_constraint.apply_constraint(
                synthesized, 
                use_velo=True
            )
        
        # 4. Optimize using combined losses
        optimizer.step()
```

**Why Only at Final Level?**
- Coarser pyramid levels focus on establishing the overall motion structure and style through patch matching alone
- Velocity constraints are intentionally **not applied** at coarser levels to avoid interfering with the coarse-to-fine refinement process
- At the finest level, the motion structure is already established, so velocity adjustments can be made without disrupting the patch coherence
- This design separates concerns: structure first (coarse levels), then speed adjustment (final level)

#### 3. Velocity Profile Loss (`nearest_neighbor/velocity_loss.py`)

**Loss Function:**
To encourage the optimization to respect the velocity profile, a dedicated loss term is added:

```python
def forward(synthesized, constraint):
    # Get target speeds from constraint
    target_speeds = constraint.target_speeds  # [T]
    
    # Compute actual speeds from synthesized motion
    vx = synthesized[:, -3, :]  # X velocity
    vz = synthesized[:, -1, :]  # Z velocity  
    actual_speeds = sqrt(vx² + vz²)  # [B, T]
    
    # MSE loss between actual and target
    loss = mean((actual_speeds - target_speeds)²)
    return loss
```

**Weight Tuning:**
The `--velocity_loss_weight` parameter controls how strongly the velocity profile is enforced:
- Low weight (0.01-0.1): Gentle guidance, preserves motion style
- High weight (1.0+): Strong enforcement, may compromise motion quality
- Recommended: 0.1-0.5 for most cases

#### 4. Interaction with Keyframe Constraints

**Mutual Exclusion:**
Velocity profile and keyframe constraints on the last frames are **mutually exclusive** because:
- Keyframe constraints fix the absolute positions of specified frames
- Velocity constraints modify the speed, which changes the distance traveled
- These two goals are fundamentally incompatible

**Validation:**
```python
if velocity_profile and keyframe_last_n > 0:
    raise ValueError(
        "Cannot use velocity_profile with keyframe_last_n. "
        "Velocity constraints modify motion speed, which conflicts "
        "with fixing the last frame positions."
    )
```

**Allowed Usage:**
- `--velocity_profile` + `--keyframe_first_n`: ✓ OK (only start frames fixed)
- `--velocity_profile` alone: ✓ OK
- `--velocity_profile` + `--keyframe_last_n`: ✗ ERROR

### Usage Examples

```bash
# Basic: 1.5x speed throughout
python run_random_generation.py -i input.bvh \
    --velocity_profile constant \
    --start_speed 1.5 --end_speed 1.5 \
    --velocity_loss_weight 0.1

# Linear deceleration with fixed start pose
python run_random_generation.py -i input.bvh \
    --velocity_profile linear_decel \
    --start_speed 2.0 --end_speed 0.5 \
    --velocity_loss_weight 0.2 \
    --keyframe_first_n 5

# Smooth ease-in-out
python run_random_generation.py -i input.bvh \
    --velocity_profile ease_in_out \
    --start_speed 0.5 --end_speed 1.5 \
    --velocity_loss_weight 0.15
```

### Technical Notes

**Coordinate System:**
- X and Z are horizontal motion (forward/sideways)
- Y is vertical (up/down, not modified by velocity constraints)
- Speed = sqrt(vx² + vz²)

**Velocity vs Position Representation:**
- This feature requires `use_velo=True` (velocity representation)
- In velocity space, each frame stores the displacement from the previous frame
- This makes speed modification straightforward and local

**Optimization Trade-offs:**
- Higher velocity loss weight → closer to target speed, but may compromise motion realism
- Lower weight → more natural motion, but speed target less accurate
- The pyramid optimization naturally balances these competing goals

### Performance

- Minimal overhead: ~5-10% increase in generation time
- Memory: Negligible additional memory usage
- Quality: Motion style generally preserved with appropriate weight tuning (0.1-0.3)

---

## Future Improvements

Potential areas for enhancement:
1. Automatic weight tuning based on motion type
2. Speed-aware patch matching (find patches with similar speeds)
3. Support for velocity profiles in position representation
4. Per-limb velocity control (e.g., fast arms, slow legs)
