# Processing Time Profiling Feature

## Overview

A comprehensive profiling feature has been added to measure processing times. This feature allows you to measure overall processing time, time per iteration, time per generated frame, and detailed breakdowns for each processing step.

## Usage

### Command Line Usage

Add the `--profile` option to enable profiling:

```bash
python run_random_generation.py -i input.bvh -o ./output --profile
```

### Output

Profiling results are output in two ways:

1. **Console Output**
   - Results are automatically displayed in the console after processing (English)
   - Includes total time, normalized iteration counts, and detailed breakdowns

2. **File Output**
   - Saved as `*_profile.csv` in the same directory as the generated BVH file
   - CSV format, can be opened and analyzed in Excel or other tools
   - Metadata is encoded in the filename for easy identification

## Output Content

The profiling results include the following information:

### 1. Total Processing Time
- Total time from start to finish

### 2. Processing Information
- `total_frames`: Number of generated frames
- `iterations_per_level`: Number of optimization iterations per pyramid level
- `num_pyramid_levels`: Number of pyramid levels
- `Time per iteration`: Processing time per iteration (normalized by steps/level)
- `Time per frame`: Processing time per generated frame

### 3. Time by Process
Detailed timing information for each processing step:

- **Total (sec)**: Total time for that process
- **Count**: Number of times executed
- **Avg (sec)**: Average time per execution
- **%**: Percentage of total time

## Measured Processes

The following processes are measured individually:

1. **build_target_pyramid**: Building target pyramid
2. **get_initial_motion**: Generating initial motion
3. **setup_velocity_profile**: Setting up velocity profile
4. **pyramid_level_N**: Processing for each pyramid level
5. **interpolate_level_N**: Interpolation for each level
6. **match_and_blend_level_N**: Match and blend processing
7. **iteration_step**: Each iteration step
8. **criteria_evaluation**: Criteria evaluation
9. **keyframe_fixing**: Keyframe fixing
10. **velocity_constraint**: Applying velocity constraints

## Example Output

### Console Output (English)
```
================================================================================
Processing Time Profile
================================================================================

[Total Processing Time]
  Total: 1.789 seconds

[Processing Info]
  >>> Iterations: 3 steps/level × 4 levels = 12 total
  >>> Time per iteration: 0.596 sec/iter
  total_frames: 300
  >>> Time per frame: 0.006 sec/frame

[Time by Process]
  Process Name                             Total (sec)     Count      Avg (sec)       %
  ---------------------------------------- --------------- ---------- --------------- ----------
  iteration_step                                  0.356        12          0.030     19.9%
  criteria_evaluation                             0.351        12          0.029     19.6%
  build_target_pyramid                            0.349         1          0.349     19.5%
  match_and_blend_level_0                         0.308         1          0.308     17.2%
  ...
================================================================================
```

### CSV File Format
```csv
Process Name,Total Time (sec),Count,Average Time (sec),Percentage (%)
iteration_step,0.356,12,0.030,19.9
criteria_evaluation,0.351,12,0.029,19.6
build_target_pyramid,0.349,1,0.349,19.5
match_and_blend_level_0,0.308,1,0.308,17.2
...
```

### File Naming Convention
Profile CSV files include metadata in the filename:
- Format: `*_profile_f{frames}_i{steps}x{levels}.csv`
- Example: `motion_syn_seed12345_profile_f300_i3x4.csv`
  - `f300`: 300 frames generated
  - `i3x4`: 3 steps per level × 4 pyramid levels

## Web Server Usage

Profiling is also available for the web server:

```bash
python run_web_server.py --profile
```

When profiling is enabled, a `profile` field is added to the returned JSON data.

## Notes

- Enabling profiling introduces a small overhead (typically less than 1%, negligible)
- Profiling is useful for debugging and performance analysis
- Consider disabling in production environments unless needed
- Time per iteration is normalized by steps/level for consistent comparison across different pyramid sizes
