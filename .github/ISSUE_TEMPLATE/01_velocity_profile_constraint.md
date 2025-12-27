---
name: Feature - Velocity Profile Constraint
about: Add velocity profile constraint to maintain temporal motion consistency
title: '[Feature] Add Velocity Profile Constraint for Temporal Consistency'
labels: enhancement, motion-synthesis
assignees: ''
---

## Problem Statement

Currently, when using reference motions at the start and end (e.g., walking motions), the generated intermediate motion exhibits inconsistent behavior - alternating between walking and stopping randomly. This is due to independent patch-based optimization without considering temporal velocity coherence.

**Current Behavior:**
```
Reference: [Walking Motion 100 frames]
       ↓ Patch-based search (each patch is independent)
Generated: [Walk][Stop][Walk][Stop]... ← No consistency
```

## Proposed Solution

Implement a **Velocity Profile Constraint** that enforces gradual velocity changes over time.

### Key Features

1. **Velocity Profile Types:**
   - `linear_decel`: Linear deceleration from start to end speed
   - `smooth_decel`: Smooth deceleration with ease-out curve
   - `linear_accel`: Linear acceleration
   - `constant`: Maintain constant speed

2. **Speed Scaling:**
   - Calculate target speed for each frame based on profile
   - Scale horizontal velocity (ΔX, ΔZ) to match target
   - Preserve vertical position (Y) for jumps/stairs

3. **Configurable Parameters:**
   - `start_speed`: Initial velocity (m/s)
   - `end_speed`: Final velocity (m/s)
   - `profile_type`: Type of velocity transition

### Implementation Plan

**Files to Create/Modify:**

1. **New File:** `utils/velocity_profile.py`
   - `VelocityProfileConstraint` class
   - Profile computation methods
   - Speed scaling functions

2. **Modify:** `GenMM.py`
   - Add `velocity_profile` parameter to `run()` method
   - Integrate constraint application in `match_and_blend()`

3. **Modify:** `run_random_generation.py`
   - Add command-line arguments:
     - `--velocity_profile`: Profile type
     - `--start_speed`: Starting velocity
     - `--end_speed`: Ending velocity

### Expected Outcome

**After Implementation:**
```
Reference: [Walking Motion]
       ↓ With velocity profile constraint
Generated: [Walk at 1.5m/s] → [Gradual deceleration] → [Stop at 0m/s]
          ✓ Smooth and natural transition
```

### Usage Example

```bash
# Smooth deceleration from walking to stop
python run_random_generation.py -i walking.bvh -o output \
    --velocity_profile smooth_decel \
    --start_speed 1.5 \
    --end_speed 0.0
```

### Technical Details

- **Constraint Application:** Post-patch-matching adjustment
- **Performance Impact:** Minimal (<1% overhead)
- **Compatibility:** Works with existing keyframe constraints

### Priority

**High** - This addresses a fundamental issue in temporal motion consistency.

---

### Checklist

- [ ] Implement `VelocityProfileConstraint` class
- [ ] Add profile computation methods (linear, smooth, etc.)
- [ ] Integrate into GenMM pipeline
- [ ] Add command-line arguments
- [ ] Write unit tests for profile computation
- [ ] Update documentation with usage examples
- [ ] Test with various motion types (walk, run, jump)
