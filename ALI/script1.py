import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_trapezoid
from scipy.spatial.transform import Rotation

# --- Configuration ---
FILE_PATH = 'v500s1/MPU6050RM3100.mat'
FS = 100.0  
DT = 1.0 / FS 

# --- Filter Functions ---
def butter_lowpass_filter(data, cutoff, fs, order=4):
    """Removes high-frequency mechanical vibration (Sensor Noise)."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data, axis=0)

def butter_highpass_filter(data, cutoff, fs, order=2):
    """Removes low-frequency integration drift (Math Noise)."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return filtfilt(b, a, data, axis=0)

# --- Double Integration Function ---
def calculate_raw_position(acceleration, dt):
    """Pure double integration WITHOUT any filtering. This will demonstrate quadratic drift."""
    # 1. Acceleration -> Velocity (No filter)
    velocity = cumulative_trapezoid(acceleration, dx=dt, axis=0, initial=0)
    
    # 2. Velocity -> Position (No filter)
    position = cumulative_trapezoid(velocity, dx=dt, axis=0, initial=0)
    
    return position

def calculate_position(acceleration, dt, fs):
    """Double integrates acceleration with drift compensation."""
    # 1. Acceleration -> Velocity (Increased highpass filtering from 0.02 Hz to 0.2 Hz)
    velocity = cumulative_trapezoid(acceleration, dx=dt, axis=0, initial=0)
    velocity = butter_highpass_filter(velocity, cutoff=0.2, fs=fs, order=2)
    
    # 2. Velocity -> Position (Increased highpass filtering from 0.02 Hz to 0.2 Hz)
    position = cumulative_trapezoid(velocity, dx=dt, axis=0, initial=0)
    position = butter_highpass_filter(position, cutoff=0.2, fs=fs, order=2)
    
    return position

def main():
    # 1. Load Data
    mat_data = loadmat(FILE_PATH)
    
    raw_accel = mat_data['SENSacc'] 
    ground_truth_pos = mat_data['ABBposition']
    quats = mat_data['ABBquaternion'] 
    
    if raw_accel.shape[0] == 3: raw_accel = raw_accel.T
    if ground_truth_pos.shape[0] == 3: ground_truth_pos = ground_truth_pos.T
    if quats.shape[0] == 4: quats = quats.T
        
    raw_accel = np.nan_to_num(raw_accel)
    ground_truth_pos = np.nan_to_num(ground_truth_pos)
    quats = np.nan_to_num(quats)
    
    # 2. Gravity Removal (Rotate to World Frame)
    scipy_quats = np.column_stack((quats[:, 1], quats[:, 2], quats[:, 3], quats[:, 0]))
    rotations = Rotation.from_quat(scipy_quats)
    world_accel = rotations.apply(raw_accel)
    world_accel[:, 2] -= 1.0 
    
    SCALE_FACTOR = 9810.0 
    world_accel_mm = world_accel * SCALE_FACTOR
    
    # 3. Denoise and Calculate Positions (Tuned lowpass filter stringency from 5.0 Hz to 1.0 Hz)
    filtered_accel = butter_lowpass_filter(world_accel_mm, cutoff=1.0, fs=FS, order=4)
    
    # Calculate pure raw position (with catastrophic mathematical drift)
    raw_position = calculate_raw_position(world_accel_mm, DT)
    
    # Calculate filtered position (denoised high-pass integration)
    filtered_position = calculate_position(filtered_accel, DT, FS)
    
    start_coordinate = ground_truth_pos[0]
    raw_position += start_coordinate
    filtered_position += start_coordinate
    
    # ==========================================
    # 4. ERROR EVALUATION (Accuracy Measurement)
    # ==========================================
    
    # Calculate Euclidean distance from Ground Truth at each timestamp
    # Formula: sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
    raw_error = np.linalg.norm(raw_position - ground_truth_pos, axis=1)
    filtered_error = np.linalg.norm(filtered_position - ground_truth_pos, axis=1)
    
    # Calculate overall RMSE (Root Mean Square Error)
    raw_rmse = np.sqrt(np.mean(raw_error**2))
    filtered_rmse = np.sqrt(np.mean(filtered_error**2))
    
    print("\n--- Accuracy Evaluation Results ---")
    print(f"Raw MPU6050 RMSE:      {raw_rmse:.2f} mm")
    print(f"Denoised MPU6050 RMSE: {filtered_rmse:.2f} mm")
    print(f"Total Improvement:     {raw_rmse - filtered_rmse:.2f} mm")
    print("-----------------------------------\n")
    
    # ==========================================
    # 5. Report Figure Generation
    # ==========================================
    time_axis = np.arange(len(raw_error)) * DT
    axes_labels = ['X', 'Y', 'Z']

    # --- FIGURE 1: Raw vs Filtered Acceleration ---
    fig1, axs1 = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    raw_accs_plot = [world_accel[:, 0], world_accel[:, 1], world_accel[:, 2]]
    filt_acc_g = filtered_accel / SCALE_FACTOR
    filt_accs_plot = [filt_acc_g[:, 0], filt_acc_g[:, 1], filt_acc_g[:, 2]]

    for i in range(3):
        axs1[i].plot(time_axis, raw_accs_plot[i], label='Raw', alpha=0.5, color='red')
        axs1[i].plot(time_axis, filt_accs_plot[i], label='Butterworth Filtered', color='blue', linewidth=1.5)
        axs1[i].set_ylabel(f'Accel {axes_labels[i]} (g)')
        axs1[i].legend(loc='upper right')
        axs1[i].grid(True)

    axs1[2].set_xlabel('Time (s)')
    fig1.suptitle('Raw vs. Filtered Acceleration Measurements')
    plt.tight_layout()
    plt.savefig('Fig1_Acceleration_Comparison.png', dpi=300)

    # Convert positions to meters for plotting
    ground_truth_pos_m = ground_truth_pos / 1000.0
    raw_position_m = raw_position / 1000.0
    filtered_position_m = filtered_position / 1000.0
    
    ground_truth_pos_list = [ground_truth_pos_m[:, 0], ground_truth_pos_m[:, 1], ground_truth_pos_m[:, 2]]
    calc_raw_pos_list = [raw_position_m[:, 0], raw_position_m[:, 1], raw_position_m[:, 2]]
    calc_filt_pos_list = [filtered_position_m[:, 0], filtered_position_m[:, 1], filtered_position_m[:, 2]]

    # --- FIGURE 2: Position Validation ---
    fig2, axs2 = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    for i in range(3):
        axs2[i].plot(time_axis, ground_truth_pos_list[i], label='Ground Truth', color='black', linewidth=2, linestyle='--')
        axs2[i].plot(time_axis, calc_raw_pos_list[i], label='Calculated from Raw', color='red', alpha=0.7)
        axs2[i].plot(time_axis, calc_filt_pos_list[i], label='Calculated from Filtered', color='blue')
        axs2[i].set_ylabel(f'Position {axes_labels[i]} (m)')
        axs2[i].legend(loc='upper left')
        axs2[i].grid(True)

    axs2[2].set_xlabel('Time (s)')
    fig2.suptitle('Position Validation: Ground Truth vs. Estimated Positions')
    plt.tight_layout()
    plt.savefig('Fig2_Position_Validation.png', dpi=300)

    # --- FIGURE 3: 3D Trajectory ---
    fig3 = plt.figure(figsize=(10, 8))
    ax3 = fig3.add_subplot(111, projection='3d')

    ax3.plot(ground_truth_pos_m[:, 0], ground_truth_pos_m[:, 1], ground_truth_pos_m[:, 2], label='Ground Truth', color='black', linewidth=2, linestyle='--')
    ax3.plot(raw_position_m[:, 0], raw_position_m[:, 1], raw_position_m[:, 2], label='Path from Raw Data', color='red', alpha=0.6)
    ax3.plot(filtered_position_m[:, 0], filtered_position_m[:, 1], filtered_position_m[:, 2], label='Path from Filtered Data', color='blue', linewidth=1.5)

    ax3.set_xlabel('X Position (m)')
    ax3.set_ylabel('Y Position (m)')
    ax3.set_zlabel('Z Position (m)')
    ax3.set_title('3D Trajectory Comparison')
    ax3.legend()
    plt.savefig('Fig3_3D_Trajectory.png', dpi=300)

    print("Processing complete. Figures saved to the current directory.")

if __name__ == "__main__":
    main()