import os
import os.path as osp
import argparse
from GenMM import GenMM
from nearest_neighbor.losses import PatchCoherentLoss
from dataset.bvh_motion import BVHMotion, load_multiple_dataset
from utils.base import ConfigParser, set_seed

args = argparse.ArgumentParser(
    description='Random shuffle the input motion sequence')
args.add_argument('-m', '--mode', default='run',
                  choices=['run', 'eval', 'debug'], type=str, help='current run mode.')
args.add_argument('-i', '--input', required=True,
                  type=str, help='exemplar motion path.')
args.add_argument('-o', '--output_dir', default='./output',
                  type=str, help='output folder path for saving results.')
args.add_argument('-c', '--config', default='./configs/default.yaml',
                  type=str, help='config file path.')
args.add_argument('-s', '--seed', default=None,
                  type=int, help='random seed used.')
args.add_argument('-d', '--device', default="cuda:0",
                  type=str, help='device to use.')
args.add_argument('--post_precess', action='store_true',
                  help='whether to use IK post-process to fix foot contact.')

# Use argsparser to overwrite the configuration
# for dataset
args.add_argument('--skeleton_name', type=str,
                  help='(used when joint_reduction==True or contact==True) skeleton name to load pre-defined joints configuration.')
args.add_argument('--use_velo', type=int,
                  help='whether to use velocity rather than global position of each joint.')
args.add_argument('--repr', choices=['repr6d', 'quat', 'euler'], type=str,
                  help='rotation representation, support [epr6d, quat, reuler].')
args.add_argument('--requires_contact', type=int,
                  help='whether to use contact label.')
args.add_argument('--keep_up_pos', type=int,
                  help='whether to do not use velocity and keep the y(up) position.')
args.add_argument('--up_axis', type=str, choices=['X_UP', 'Y_UP', 'Z_UP'],
                  help='up axis of the motion.')
args.add_argument('--padding_last', type=int,
                  help='whether to pad the last position channel to match the rotation dimension.')
args.add_argument('--joint_reduction', type=int,
                  help='whether to simplify the skeleton using provided skeleton config.')
args.add_argument('--skeleton_aware', type=int,
                  help='whether to enable skeleton-aware component.')
args.add_argument('--joints_group', type=str,
                  help='joints spliting group for using skeleton-aware component.')
# for synthesis
args.add_argument('--num_frames', type=str, 
                  help='number of synthesized frames, supported Nx(N times) and int input.')
args.add_argument('--duration', type=float, default=None,
                  help='duration in seconds for synthesized motion (alternative to --num_frames). Will be converted to frames based on input motion framerate.')
args.add_argument('--alpha', type=float,
                  help='completeness/diversity trade-off alpha value.')
args.add_argument('--num_steps', type=int,
                  help='number of optimization steps at each pyramid level.')
args.add_argument('--noise_sigma', type=float,
                  help='standard deviation of the zero mean normal noise added to the initialization.')
args.add_argument('--coarse_ratio', type=float,
                  help='downscale ratio of the coarse level.')
args.add_argument('--coarse_ratio_factor', type=float,
                  help='downscale ratio of the coarse level.')
args.add_argument('--pyr_factor', type=float,
                  help='upsample ratio of each pyramid level.')
args.add_argument('--num_stages_limit', type=int,
                  help='limit of the number of stages.')
args.add_argument('--patch_size', type=int, help='patch size for generation.')
args.add_argument('--loop', type=int, help='whether to loop the sequence.')
args.add_argument('--keyframe_first_n', type=int, default=None,
                  help='fix first N frames to match input motion (e.g., 5 for first 5 frames).')
args.add_argument('--keyframe_last_n', type=int, default=None,
                  help='fix last N frames to match input motion (e.g., 5 for last 5 frames).')
args.add_argument('--fix_final_position', action='store_true',
                  help='adjust cumulative position to match final position when using --keyframe_last_n (may cause foot sliding in locomotion).')
args.add_argument('--keyframe_start', type=int, default=None,
                  help='[Advanced] start frame index for keyframe fixing (e.g., 0 for first frames, -5 for last 5 frames).')
args.add_argument('--keyframe_end', type=int, default=None,
                  help='[Advanced] end frame index for keyframe fixing (e.g., 10 for first 10 frames, use -1 for None when using negative start).')
# velocity profile arguments
args.add_argument('--velocity_profile', type=str, default=None,
                  choices=['linear_decel', 'linear_accel', 'smooth_decel', 'smooth_accel', 'constant', 'ease_in_out'],
                  help='velocity profile type for temporal consistency.')
args.add_argument('--start_speed', type=float, default=None,
                  help='starting velocity in m/s (used with --velocity_profile).')
args.add_argument('--end_speed', type=float, default=None,
                  help='ending velocity in m/s (used with --velocity_profile).')
cfg = ConfigParser(args)


def generate(cfg):
    # seet seed for reproducible
    set_seed(cfg.seed)

    # set save path and prepare data for generation
    if cfg.input.endswith('.bvh'):
        # Get input directory and filename
        input_dir = osp.dirname(cfg.input) if cfg.output_dir == './output' else cfg.output_dir
        input_name = osp.splitext(osp.basename(cfg.input))[0]
        motion_data = [BVHMotion(cfg.input, skeleton_name=cfg.skeleton_name, repr=cfg.repr,
                                 use_velo=cfg.use_velo, keep_up_pos=cfg.keep_up_pos, up_axis=cfg.up_axis, padding_last=cfg.padding_last,
                                 requires_contact=cfg.requires_contact, joint_reduction=cfg.joint_reduction)]
    elif cfg.input.endswith('.txt'):
        input_dir = osp.dirname(cfg.input) if cfg.output_dir == './output' else cfg.output_dir
        input_name = osp.splitext(osp.basename(cfg.input))[0]
        motion_data = load_multiple_dataset(name_list=cfg.input, skeleton_name=cfg.skeleton_name, repr=cfg.repr,
                                            use_velo=cfg.use_velo, keep_up_pos=cfg.keep_up_pos, up_axis=cfg.up_axis, padding_last=cfg.padding_last,
                                            requires_contact=cfg.requires_contact, joint_reduction=cfg.joint_reduction)
    else:
        raise ValueError('exemplar must be a bvh file or a txt file')
    
    # Convert duration to num_frames if specified
    num_frames_to_use = cfg.num_frames
    if cfg.duration is not None:
        # Get frametime from the first motion data
        if cfg.input.endswith('.bvh'):
            from dataset.bvh.bvh_parser import BVH_file
            bvh = BVH_file(cfg.input, skeleton_conf=None, requires_contact=False, joint_reduction=False)
            frametime = bvh.frametime
        else:
            # For txt files, use the first motion
            frametime = motion_data[0].frametime
        
        num_frames_to_use = str(int(cfg.duration / frametime))
        print(f"Duration {cfg.duration}s at {frametime}s/frame = {num_frames_to_use} frames")
    
    # Determine output directory and filename
    # For debug mode, create a subdirectory with detailed parameters
    if cfg.mode == 'debug':
        prefix = f"s{cfg.seed}+{num_frames_to_use}+{cfg.repr}+use_velo_{cfg.use_velo}+kypose_{cfg.keep_up_pos}+padding_{cfg.padding_last}" \
                 f"+contact_{cfg.requires_contact}+jredu_{cfg.joint_reduction}+n{cfg.noise_sigma}+pyr{cfg.pyr_factor}" \
                 f"+r{cfg.coarse_ratio}_{cfg.coarse_ratio_factor}+itr{cfg.num_steps}+ps_{cfg.patch_size}+alpha_{cfg.alpha}" \
                 f"+loop_{cfg.loop}"
        output_dir = osp.join(input_dir, input_name, prefix)
        output_filename = "syn.bvh"
        debug_dir = output_dir
    else:
        # Normal mode: simple filename in input directory
        if cfg.seed is not None:
            output_filename = f"{input_name}_syn_seed{cfg.seed:06d}.bvh"
        else:
            output_filename = f"{input_name}_syn.bvh"
        output_dir = input_dir
        debug_dir = None
    
    output_path = osp.join(output_dir, output_filename)

    # perform the generation
    model = GenMM(device=cfg.device, silent=True if cfg.mode == 'eval' else False)
    
    # Set keyframe indices if specified
    keyframe_slices = []
    
    # Simple interface: first/last N frames
    if cfg.keyframe_first_n is not None:
        keyframe_slices.append(slice(0, cfg.keyframe_first_n))
        print(f"Keyframe fixing enabled: first {cfg.keyframe_first_n} frames")
    
    if cfg.keyframe_last_n is not None:
        keyframe_slices.append(slice(-cfg.keyframe_last_n, None))
        print(f"Keyframe fixing enabled: last {cfg.keyframe_last_n} frames")
    
    # Advanced interface: custom start/end
    if cfg.keyframe_start is not None:
        end_idx = None if cfg.keyframe_end == -1 else cfg.keyframe_end
        keyframe_slices.append(slice(cfg.keyframe_start, end_idx))
        if end_idx is None:
            print(f"Keyframe fixing enabled: frames from {cfg.keyframe_start} to end")
        else:
            print(f"Keyframe fixing enabled: frames {cfg.keyframe_start} to {end_idx}")
    
    # Set KEYFRAME_INDICES: single slice or list of slices
    if len(keyframe_slices) == 0:
        GenMM.KEYFRAME_INDICES = None
    elif len(keyframe_slices) == 1:
        GenMM.KEYFRAME_INDICES = keyframe_slices[0]
    else:
        GenMM.KEYFRAME_INDICES = keyframe_slices
    
    criteria = PatchCoherentLoss(patch_size=cfg.patch_size, alpha=cfg.alpha, loop=cfg.loop, cache=True)
    
    # Parse velocity profile configuration
    from utils.velocity_profile import parse_velocity_profile_args
    velocity_profile_config = parse_velocity_profile_args(
        cfg.velocity_profile, 
        cfg.start_speed, 
        cfg.end_speed
    )
    
    syn = model.run(motion_data, criteria,
                    num_frames=num_frames_to_use,
                    num_steps=cfg.num_steps,
                    noise_sigma=cfg.noise_sigma,
                    patch_size=cfg.patch_size, 
                    coarse_ratio=cfg.coarse_ratio,
                    pyr_factor=cfg.pyr_factor,
                    debug_dir=debug_dir,
                    velocity_profile=velocity_profile_config)
    
    # Post-process: adjust final position if last frames are fixed
    if cfg.keyframe_last_n is not None and cfg.use_velo and cfg.fix_final_position:
        print(f"Adjusting final position to match input motion...")
        
        # Get velocity mask (which axes are converted to velocity)
        velo_mask = motion_data[0].motion_data.velo_mask
        num_velo_axes = len(velo_mask)
        
        # Get the original input data in position form
        input_motion_obj = BVHMotion(cfg.input, skeleton_name=cfg.skeleton_name, repr=cfg.repr,
                                     use_velo=False, keep_up_pos=cfg.keep_up_pos, up_axis=cfg.up_axis, 
                                     padding_last=cfg.padding_last,
                                     requires_contact=cfg.requires_contact, joint_reduction=cfg.joint_reduction)
        
        input_pos_data = input_motion_obj.motion_data.data
        target_final_pos = input_pos_data[:, -3:, -1].to(syn.device)  # Last frame's XYZ position
        
        # Convert synthesized velocity to position for adjustment
        syn_begin_pos_backup = motion_data[0].motion_data.begin_pos.clone()
        syn_pos = motion_data[0].motion_data.to_position(syn.clone())
        current_final_pos = syn_pos[:, -3:, -1]
        
        # Calculate position offset needed
        pos_offset = target_final_pos - current_final_pos
        
        # Apply offset gradually from start to end of non-fixed region
        start_frame = cfg.keyframe_first_n if cfg.keyframe_first_n is not None else 0
        end_frame = syn_pos.shape[-1] - cfg.keyframe_last_n
        
        if end_frame > start_frame:
            # Gradually apply offset
            for i in range(start_frame, end_frame):
                alpha = (i - start_frame) / (end_frame - start_frame)
                syn_pos[:, -3:, i] += pos_offset * alpha
            
            # Apply full offset to remaining frames before the fixed last frames
            if end_frame < syn_pos.shape[-1]:
                for i in range(end_frame, syn_pos.shape[-1]):
                    syn_pos[:, -3:, i] += pos_offset
        
        # Convert back to velocity
        motion_data[0].motion_data.begin_pos = None  # Reset before converting to velocity
        syn = motion_data[0].motion_data.to_velocity(syn_pos)
        motion_data[0].motion_data.begin_pos = syn_begin_pos_backup  # Restore for future use
        print(f"Position adjusted. Offset applied: {pos_offset.squeeze().cpu().numpy()}")
    
    # save the generated results
    print(f"Saving results to: {output_path}")
    os.makedirs(output_dir, exist_ok=True)
    motion_data[0].write(output_path, syn)
    print(f"File saved: {output_path}")

    if cfg.post_precess:
        # Note: post_precess requires skeleton_name
        output_basename = osp.splitext(osp.basename(output_path))[0]
        cmd = f"python fix_contact.py --prefix {osp.abspath(output_dir)} --name {output_basename} --skeleton_name={cfg.skeleton_name}"
        os.system(cmd)

if __name__ == '__main__':
    generate(cfg)
