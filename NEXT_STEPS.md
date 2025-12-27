# Next Steps for Temporal Consistency Features

## What Has Been Done ✅

### 1. Documentation and Templates Created
- ✅ Issue templates for all 3 features (`.github/ISSUE_TEMPLATE/`)
- ✅ PR template (`.github/pull_request_template.md`)
- ✅ Project overview document (`TEMPORAL_CONSISTENCY_PROJECT.md`)
- ✅ Committed to `main` branch and pushed

### 2. Feature 1: Velocity Profile Constraint - IMPLEMENTED ✅
- ✅ Branch: `feature/velocity-profile-constraint` created
- ✅ Implemented `utils/velocity_profile.py`
  - VelocityProfileConstraint class
  - 6 profile types: linear_decel, smooth_decel, linear_accel, smooth_accel, constant, ease_in_out
  - Speed scaling for horizontal velocities
- ✅ Modified `GenMM.py` to integrate velocity constraint
- ✅ Modified `run_random_generation.py` with CLI arguments
- ✅ Unit tests created (`tests/test_velocity_profile.py`)
- ✅ **Pushed to fork: `https://github.com/mtside2025/GenMM`**

## What You Need to Do 📋

### Step 1: Create GitHub Issue for Feature 1

1. Go to: `https://github.com/mtside2025/GenMM/issues/new/choose`
2. Select "Feature - Velocity Profile Constraint" template
3. Review and create the issue
4. Note the issue number (e.g., #1)

### Step 2: Create Pull Request for Feature 1

1. Go to: `https://github.com/mtside2025/GenMM/pull/new/feature/velocity-profile-constraint`
   (Or use the link from the push output)
2. Fill in the PR template:
   - Related Issue: #[number from Step 1]
   - Description: Copy from issue or summarize
   - Test results: (optional for now, can be filled after testing)
3. Create the pull request
4. Review the changes
5. **Test the feature** (see testing section below)
6. Merge when satisfied

### Step 3: Testing Feature 1 (Before Merging)

```bash
# Switch to feature branch
git checkout feature/velocity-profile-constraint

# Test 1: Linear deceleration
python run_random_generation.py -i path/to/walking.bvh -o output/test1 \
    --velocity_profile linear_decel \
    --start_speed 1.5 \
    --end_speed 0.0

# Test 2: Smooth deceleration
python run_random_generation.py -i path/to/walking.bvh -o output/test2 \
    --velocity_profile smooth_decel \
    --start_speed 2.0 \
    --end_speed 0.2

# Test 3: Run unit tests
python -m pytest tests/test_velocity_profile.py -v

# Visualize velocity profile (optional, requires matplotlib)
python -c "
from utils.velocity_profile import VelocityProfileConstraint
c = VelocityProfileConstraint(100, 'smooth_decel', 1.5, 0.0)
c.visualize_profile('velocity_profile_test.png')
"
```

## Next Features (To Be Implemented)

### Feature 2: Temporal Coherence Loss
**Status:** Not yet implemented
**Branch:** Will create `feature/temporal-coherence-loss`
**Priority:** Medium

After Feature 1 is merged, I can implement this next.

### Feature 3: Adaptive Velocity-Aware Search
**Status:** Not yet implemented
**Branch:** Will create `feature/adaptive-velocity-search`
**Priority:** Low-Medium
**Depends on:** Feature 1 (velocity profile)

This will be implemented after Features 1 and optionally 2.

## Quick Reference: Git Commands

```bash
# View all branches
git branch -a

# Switch to main
git checkout main

# Switch to feature branch
git checkout feature/velocity-profile-constraint

# Pull latest from fork
git pull fork feature/velocity-profile-constraint

# Merge feature into main (after PR is approved)
git checkout main
git merge feature/velocity-profile-constraint
git push fork main
```

## Questions to Answer Before Next Implementation

1. **Should I proceed with Feature 2 now?**
   - If yes, I'll create the branch and implement temporal coherence loss
   
2. **Any adjustments needed to Feature 1?**
   - Profile types to add/remove?
   - Parameter defaults to change?
   - Additional functionality?

3. **Testing feedback?**
   - Does Feature 1 work as expected?
   - Any issues or bugs found?

## Links

- **Your Fork:** https://github.com/mtside2025/GenMM
- **Feature 1 Branch:** https://github.com/mtside2025/GenMM/tree/feature/velocity-profile-constraint
- **Issue Template Location:** `.github/ISSUE_TEMPLATE/01_velocity_profile_constraint.md`

---

**Ready for your review and testing!** Let me know when you want to proceed with Features 2 and 3.
