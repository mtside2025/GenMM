---
name: Feature - Temporal Coherence Loss
about: Add temporal coherence loss to improve motion smoothness
title: '[Feature] Add Temporal Coherence Loss for Smoother Motion'
labels: enhancement, loss-function
assignees: ''
---

## Problem Statement

Patch-based optimization independently processes each patch, potentially leading to:
- Jittery motion transitions
- Unnatural acceleration changes
- Discontinuities at patch boundaries

## Proposed Solution

Implement a **Temporal Coherence Loss** that penalizes abrupt changes between adjacent frames.

### Key Features

1. **Multi-Order Smoothness:**
   - First-order: Penalize velocity changes (frame-to-frame differences)
   - Second-order: Penalize acceleration changes (jerk minimization)

2. **Velocity-Aware Weighting:**
   - Higher weight on velocity channels (ΔX, ΔZ)
   - Preserves natural motion dynamics while ensuring smoothness

3. **Configurable Parameters:**
   - `weight`: Overall temporal loss weight
   - `smoothness_weight`: Balance between velocity and acceleration smoothness

### Implementation Plan

**Files to Create/Modify:**

1. **New File:** `nearest_neighbor/temporal_loss.py`
   - `TemporalCoherenceLoss` class
   - `CombinedLoss` class (patch + temporal)
   - Smoothness computation methods

2. **Modify:** `GenMM.py`
   - Add `temporal_coherence_weight` parameter
   - Use `CombinedLoss` when temporal loss is enabled

3. **Modify:** `run_random_generation.py`
   - Add `--temporal_coherence_weight` argument (default: 0.0 for backward compatibility)

### Mathematical Formulation

**Total Loss:**
```
L_total = L_patch + λ_temporal * L_temporal
```

**Temporal Loss:**
```
L_temporal = w1 * ||Δv||² + w2 * ||Δa||² + w3 * ||Δv_velocity||²
where:
  Δv = x[t+1] - x[t]           (first-order difference)
  Δa = Δv[t+1] - Δv[t]          (second-order difference)
  Δv_velocity = velocity[t+1] - velocity[t]  (velocity channel smoothness)
```

### Expected Outcome

**Before:**
```
Frame differences: [0.1, 0.3, 0.05, 0.4, 0.08, ...]  ← Jittery
```

**After:**
```
Frame differences: [0.1, 0.12, 0.13, 0.14, 0.15, ...]  ← Smooth
```

### Usage Example

```bash
# Enable temporal coherence loss
python run_random_generation.py -i input.bvh -o output \
    --temporal_coherence_weight 0.1

# Stronger smoothness (may reduce naturalness)
python run_random_generation.py -i input.bvh -o output \
    --temporal_coherence_weight 0.2
```

### Technical Details

- **Loss Computation:** Differentiable, GPU-accelerated
- **Integration Point:** Inside `match_and_blend()` loop
- **Performance Impact:** ~5-10% overhead per iteration
- **Trade-off:** Smoothness vs. Match Quality (controlled by weight)

### Priority

**Medium** - Complements velocity profile constraint, provides additional smoothness.

---

### Checklist

- [ ] Implement `TemporalCoherenceLoss` class
- [ ] Implement `CombinedLoss` wrapper
- [ ] Add first-order and second-order smoothness
- [ ] Integrate into GenMM pipeline
- [ ] Add command-line argument
- [ ] Test optimal weight ranges (0.05-0.2)
- [ ] Compare motion quality with/without temporal loss
- [ ] Update documentation
