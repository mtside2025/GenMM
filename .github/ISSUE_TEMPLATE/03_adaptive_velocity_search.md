---
name: Feature - Adaptive Velocity Patch Search
about: Implement velocity-aware patch search for better temporal consistency
title: '[Feature] Add Adaptive Velocity-Aware Patch Search'
labels: enhancement, advanced, performance
assignees: ''
---

## Problem Statement

Current nearest-neighbor search treats all target patches equally, regardless of their velocity characteristics. This can lead to:
- Selecting patches with incompatible speeds for a given frame position
- Breaking velocity continuity in generated motion
- Inconsistent motion flow

## Proposed Solution

Implement **Adaptive Velocity-Aware Patch Search** that filters and prioritizes patches based on the target velocity profile.

### Key Features

1. **Position-Based Velocity Filtering:**
   - Each patch position has a target velocity range
   - Filter candidate patches by their average speed
   - Only search within velocity-compatible patches

2. **Dynamic Speed Range:**
   - Tolerance parameter controls range width
   - Tighter at motion start/end, looser in middle
   - Prevents empty filter results

3. **Multi-Level Search:**
   - Coarse levels: Wider velocity tolerance
   - Fine levels: Stricter velocity matching
   - Progressive refinement through pyramid

### Implementation Plan

**Files to Create/Modify:**

1. **New File:** `nearest_neighbor/velocity_aware_loss.py`
   - `AdaptiveVelocityPatchLoss` class
   - Velocity extraction and filtering methods
   - Per-patch speed computation

2. **Modify:** `nearest_neighbor/utils.py`
   - Add `filter_patches_by_speed()` function
   - Add `compute_patch_velocity()` function

3. **Modify:** `GenMM.py`
   - Support velocity-aware loss as alternative criteria
   - Pass velocity profile to loss function

4. **Modify:** `run_random_generation.py`
   - Add `--use_velocity_aware_search` flag
   - Add `--velocity_tolerance` parameter (default: 0.2 = ±20%)

### Algorithm Overview

```
For each query patch at position i:
  1. Determine center frame position
  2. Get target speed from velocity profile
  3. Calculate acceptable speed range: [speed*(1-tol), speed*(1+tol)]
  4. Filter target patches by average speed
  5. Search nearest neighbor only in filtered set
  6. Fallback to full search if no matches
```

### Expected Outcome

**Traditional Search:**
```
Frame 0-20:   Targets with speed 0.5-2.5 m/s
Frame 21-40:  Targets with speed 0.5-2.5 m/s  ← All speeds mixed
Frame 41-60:  Targets with speed 0.5-2.5 m/s
```

**Adaptive Search:**
```
Frame 0-20:   Targets with speed 1.4-1.6 m/s  ← Filtered for ~1.5 m/s
Frame 21-40:  Targets with speed 0.9-1.1 m/s  ← Filtered for ~1.0 m/s
Frame 41-60:  Targets with speed 0.0-0.2 m/s  ← Filtered for ~0.1 m/s
```

### Usage Example

```bash
# Enable velocity-aware search with velocity profile
python run_random_generation.py -i walking.bvh -o output \
    --velocity_profile smooth_decel \
    --start_speed 1.5 --end_speed 0.0 \
    --use_velocity_aware_search \
    --velocity_tolerance 0.15

# Stricter velocity matching (may reduce patch diversity)
python run_random_generation.py -i input.bvh -o output \
    --velocity_profile linear_decel \
    --start_speed 2.0 --end_speed 0.5 \
    --use_velocity_aware_search \
    --velocity_tolerance 0.1
```

### Technical Details

- **Search Complexity:** O(N_filtered × D) where N_filtered << N_total
- **Performance:** 30-50% faster when filtering significantly reduces candidates
- **Trade-off:** Stricter filtering = fewer candidates = less visual variety
- **Fallback Strategy:** Use full search if filtered set is empty

### Advantages

✅ **Quality:** Better velocity consistency
✅ **Speed:** Fewer patches to search (when filtered)
✅ **Control:** Fine-grained velocity matching

### Disadvantages

⚠️ **Complexity:** More complex implementation
⚠️ **Risk:** Over-filtering may limit motion variety
⚠️ **Tuning:** Requires careful tolerance parameter tuning

### Priority

**Low-Medium** - Advanced feature, provides best results but requires careful tuning.

---

### Checklist

- [ ] Implement `AdaptiveVelocityPatchLoss` class
- [ ] Add velocity extraction from patches
- [ ] Implement speed-based filtering
- [ ] Add per-patch nearest-neighbor search
- [ ] Implement fallback mechanism
- [ ] Add command-line arguments
- [ ] Benchmark performance vs. quality trade-offs
- [ ] Test with various tolerance values (0.1, 0.15, 0.2, 0.3)
- [ ] Compare with non-adaptive approach
- [ ] Document optimal parameter ranges
- [ ] Update documentation

### Dependencies

- Requires: Issue #1 (Velocity Profile Constraint)
- Optional: Issue #2 (Temporal Coherence Loss) for combined benefits
