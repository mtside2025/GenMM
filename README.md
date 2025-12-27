# Example-based Motion Synthesis via Generative Motion Matching, ACM Transactions on Graphics (Proceedings of SIGGRAPH 2023)

#####  <p align="center"> [Weiyu Li*](https://wyysf-98.github.io/), [Xuelin Chen*†](https://xuelin-chen.github.io/), [Peizhuo Li](https://peizhuoli.github.io/), [Olga Sorkine-Hornung](https://igl.ethz.ch/people/sorkine/), [Baoquan Chen](https://cfcs.pku.edu.cn/baoquan/)</p>
 
#### <p align="center">[Project Page](https://wyysf-98.github.io/GenMM) | [ArXiv](https://arxiv.org/abs/2306.00378) | [Paper](https://wyysf-98.github.io/GenMM/paper/Paper_high_res.pdf) | [Video](https://youtu.be/lehnxcade4I)</p>

<p align="center">
  <img src="https://wyysf-98.github.io/GenMM/assets/images/teaser.png"/>
</p>

<p align="center"> All Code and demo will be released in this week(still ongoing...) 🏗️ 🚧 🔨</p>

- [x] Release main code
- [x] Release blender addon
- [x] Detailed README and installation guide
- [ ] Release skeleton-aware component, WIP as we need to split the joints into groups manually.
- [ ] Release codes for evaluation

## Prerequisite

<details> <summary>Setup environment</summary>

:smiley: We also provide a Dockerfile for easy installation, see [Setup using Docker](./docker/README.md).

 - Python 3.8
 - PyTorch 1.12.1
 - [unfoldNd](https://github.com/f-dangel/unfoldNd)

Clone this repository.

```sh
git clone git@github.com:wyysf-98/GenMM.git
```

Install the required packages.

```sh
conda create -n GenMM python=3.8
conda activate GenMM
conda install -c pytorch pytorch=1.12.1 torchvision=0.13.1 cudatoolkit=11.3 && \
pip install -r docker/requirements.txt
pip install torch-scatter==2.1.1
```

</details>

## Quick inference demo
For local quick inference demo using .bvh file, you can use

```sh
python run_random_generation.py -i './data/Malcolm/Gangnam-Style.bvh'
```
More configuration can be found in the `run_random_generation.py`.
We use an Apple M1 and NVIDIA Tesla V100 with 32 GB RAM to generate each motion, which takes about ~0.2s and ~0.05s as mentioned in our paper.

### Keyframe-Guided Generation
You can fix specific frames from the input motion to guide the generation. This is useful for creating motion variations while preserving start/end poses or creating loopable animations.

**Duration control:**

Specify the desired output length in seconds using `--duration`:
```sh
# Generate 5 seconds of motion
python run_random_generation.py -i input.bvh --duration 5.0

# Generate 10 seconds with keyframe constraints
python run_random_generation.py -i input.bvh --duration 10.0 --keyframe_first_n 5 --keyframe_last_n 5
```

The duration is automatically converted to frames based on the input motion's framerate (typically 30fps or 60fps).

**Basic usage:**
```sh
# Fix first 5 frames
python run_random_generation.py -i input.bvh --keyframe_first_n 5

# Fix last 5 frames
python run_random_generation.py -i input.bvh --keyframe_last_n 5

# Fix both first and last 5 frames
python run_random_generation.py -i input.bvh --keyframe_first_n 5 --keyframe_last_n 5
```

**Final position adjustment:**

By default, fixing the last frames only matches the pose. To also match the final position exactly (important for looping or connecting motions), use `--fix_final_position`:

```sh
python run_random_generation.py -i input.bvh --keyframe_last_n 5 --fix_final_position
```

⚠️ **Note:** Using `--fix_final_position` may cause foot sliding in locomotion animations (walking, running). Only use it for stationary animations (dance, gestures) or when creating loops.

**Advanced usage:**

For custom frame ranges, use `--keyframe_start` and `--keyframe_end`:
```sh
# Fix frames 10-20
python run_random_generation.py -i input.bvh --keyframe_start 10 --keyframe_end 20

# Fix last 10 frames (using negative index)
python run_random_generation.py -i input.bvh --keyframe_start -10 --keyframe_end -1
```

### Velocity Profile Control (NEW!)
Control the speed of generated motion with velocity profile constraints. This allows you to generate faster or slower variations of the input motion while preserving its style and character.

**Basic usage:**
```sh
# Generate motion at 1.5x speed
python run_random_generation.py -i input.bvh \
    --velocity_profile constant \
    --start_speed 1.5 --end_speed 1.5 \
    --velocity_loss_weight 0.1

# Generate motion that decelerates from 2x to 0.5x speed
python run_random_generation.py -i input.bvh \
    --velocity_profile linear_decel \
    --start_speed 2.0 --end_speed 0.5 \
    --velocity_loss_weight 0.1
```

**Available velocity profiles:**
- `constant`: Uniform speed throughout the motion
- `linear_accel`: Linear acceleration from start_speed to end_speed
- `linear_decel`: Linear deceleration from start_speed to end_speed  
- `ease_in_out`: Smooth acceleration and deceleration with ease curves

**Parameters:**
- `--velocity_profile`: Type of velocity profile (required)
- `--start_speed`: Speed multiplier at the start (e.g., 1.5 = 1.5x original speed)
- `--end_speed`: Speed multiplier at the end
- `--velocity_loss_weight`: How strongly to enforce the speed constraint (default: 0.1, range: 0.01-1.0)

**Combining with keyframes:**
```sh
# OK: Fix start pose and control speed
python run_random_generation.py -i input.bvh \
    --velocity_profile constant --start_speed 1.5 --end_speed 1.5 \
    --keyframe_first_n 5 \
    --velocity_loss_weight 0.1
```

⚠️ **Important:** You **cannot** use `--velocity_profile` with `--keyframe_last_n` because velocity constraints modify the total distance traveled, which conflicts with fixing the end position. Use `--keyframe_first_n` only.

**Weight tuning tips:**
- Low weight (0.01-0.1): Gentle guidance, better preserves motion quality
- Medium weight (0.1-0.3): Balanced (recommended for most cases)
- High weight (0.5-1.0): Strong enforcement, may reduce motion naturalness

See [HISTORY.md](HISTORY.md) for detailed implementation notes.

### Additional Options

**Output configuration:**
```sh
# Specify output directory
# Default: same directory as input file
python run_random_generation.py -i input.bvh -o ./my_output

# Set random seed for reproducibility
python run_random_generation.py -i input.bvh -s 42

# Use specific device (default: cuda:0)
python run_random_generation.py -i input.bvh -d cpu
python run_random_generation.py -i input.bvh -d cuda:1

# Use config file (default: ./configs/default.yaml)
python run_random_generation.py -i input.bvh -c ./configs/ganimator.yaml

# Enable debug mode to save intermediate results
python run_random_generation.py -i input.bvh -m debug
```

**Motion representation:**
```sh
# Rotation representation (default: repr6d)
python run_random_generation.py -i input.bvh --repr quat    # quaternion
python run_random_generation.py -i input.bvh --repr euler   # euler angles

# Use velocity representation (default: 1)
python run_random_generation.py -i input.bvh --use_velo 0   # use positions instead

# Keep Y-axis position when using velocity (default: 0)
python run_random_generation.py -i input.bvh --keep_up_pos 1

# Specify up axis (default: Y_UP)
python run_random_generation.py -i input.bvh --up_axis Z_UP
```

**Generation parameters:**
```sh
# Output length specification
# Default: same length as input
python run_random_generation.py -i input.bvh --num_frames 200    # exact frame count
python run_random_generation.py -i input.bvh --num_frames 2x     # 2x input length
python run_random_generation.py -i input.bvh --duration 5.0      # 5 seconds

# Completeness/diversity trade-off (default: 0.01, higher = more diverse)
python run_random_generation.py -i input.bvh --alpha 0.05

# Patch size for matching (default: 11)
python run_random_generation.py -i input.bvh --patch_size 15

# Optimization steps per pyramid level (default: 3)
python run_random_generation.py -i input.bvh --num_steps 5

# Noise level for initialization (default: 10.0)
python run_random_generation.py -i input.bvh --noise_sigma 5.0

# Pyramid upsampling factor (default: 0.75)
python run_random_generation.py -i input.bvh --pyr_factor 0.8

# Create looping animation
python run_random_generation.py -i input.bvh --loop 1
```

**Skeleton configuration:**
```sh
# Use predefined skeleton (mixamo, xia, crab_dance)
python run_random_generation.py -i input.bvh --skeleton_name mixamo

# Enable joint reduction to simplify skeleton
python run_random_generation.py -i input.bvh --joint_reduction 1 --skeleton_name mixamo

# Add contact labels for feet
python run_random_generation.py -i input.bvh --requires_contact 1 --skeleton_name mixamo

# Post-process with IK to fix foot contact
python run_random_generation.py -i input.bvh --post_precess
```

## Blender add-on
You can install and use the blender add-on with easy installation as our method is efficient and you do not need to install CUDA Toolkit.
We test our code using blender 3.22.0, and will support 2.8.0 in the future.

Step 1: Find yout blender python path. Common paths are as follows
```sh
(Windows) 'C:\Program Files\Blender Foundation\Blender 3.2\3.2\python\bin'
(Linux) '/path/to/blender/blender-path/3.2/python/bin'
(Windows) '/Applications/Blender.app/Contents/Resources/3.2/python/bin'
```

Step 2: Install required packages. Open your shell(Linux) or powershell(Windows), 
```sh
cd {your python path} && pip3 install -r docker/requirements.txt && pip3 install torch-scatter==2.1.0 -f https://data.pyg.org/whl/torch-1.12.0+${CUDA}.html
```
, where ${CUDA} should be replaced by either cpu, cu117, or cu118 depending on your PyTorch installation.
On my MacOS with M1 cpu,

```sh
cd /Applications/Blender.app/Contents/Resources/3.2/python/bin && pip3 install -r docker/requirements_blender.txt && pip3 install torch-scatter==2.1.0 -f https://data.pyg.org/whl/torch-1.12.0+cpu.html
```

Step 3: Install add-on in blender. [Blender Add-ons Official Tutorial](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html). `edit -> Preferences -> Add-ons -> Install -> Select the downloaded .zip file`

Step 4: Have fun! Click the armature and you will find a `GenMM` tag.

(GPU support) If you have GPU and CUDA Toolskits installed, we automatically dectect the running device.

Feel free to submit an issue if you run into any issues during the installation :)

## Acknowledgement

We thank [@stefanonuvoli](https://github.com/stefanonuvoli/skinmixer) for the help for the discussion of implementation about `Motion Reassembly` part (we eventually manually merged the meshes of different characters). And [@Radamés Ajna](https://github.com/radames) for the help of a better huggingface demo. 


## Citation

If you find our work useful for your research, please consider citing using the following BibTeX entry.

```BibTeX
@article{10.1145/weiyu23GenMM,
    author     = {Li, Weiyu and Chen, Xuelin and Li, Peizhuo and Sorkine-Hornung, Olga and Chen, Baoquan},
    title      = {Example-Based Motion Synthesis via Generative Motion Matching},
    journal    = {ACM Transactions on Graphics (TOG)},
    volume     = {42},
    number     = {4},
    year       = {2023},
    articleno  = {94},
    doi = {10.1145/3592395},
    publisher  = {Association for Computing Machinery},
}
```
