# Motion Analysis and Fixing Tools

This directory contains general-purpose tools for analyzing and fixing motion data.

## Tool List

### analyze_foot_contact.py
Foot contact detection and foot sliding analysis tool

**Features:**
- Velocity-based contact detection
- Foot sliding detection during contact phases
- Foot sliding correction (optional)

**Usage:**
```bash
python tools/analyze_foot_contact.py input.bvh -o output_fixed.bvh --threshold 0.020
```

**Parameters:**
- `--threshold`: Velocity threshold for contact detection (m/frame), default: 0.020

---

### analyze_pose_quality.py
Pose quality and trajectory analysis tool

**Features:**
- Measure pose change magnitude
- Analyze root motion trajectory
- Quality evaluation per segment
- Frame-level detailed analysis

**Usage:**
```bash
python tools/analyze_pose_quality.py input.bvh
```

**Output:**
- Pose change per segment
- Root velocity statistics
- Stationary segment detection
- Abnormal frame identification

---

### apply_contact_fix.py
Contact constraint application tool

**Features:**
- Automatic contact detection
- Apply contact constraints
- Fix foot sliding

**Usage:**
```bash
python tools/apply_contact_fix.py input.bvh -o output_fixed.bvh --threshold 0.018
```

**Parameters:**
- `--threshold`: Velocity threshold for contact detection (m/frame), default: 0.018
- `-o, --output`: Output file path

---

## Common Dependencies

These tools depend on the following modules:

- `dataset.bvh_motion.BVHMotion`: BVH file loading
- `dataset.bvh.bvh_parser.BVH_file`: BVH parser
- `utils.contact`: Contact detection utilities

## Notes

- All tools are standalone executable
- Adjust velocity thresholds according to motion scale
- Contact detection accuracy heavily depends on threshold settings
