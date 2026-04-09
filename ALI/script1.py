import numpy as np
import matplotlib.pyplot as plt
from scipy.io import loadmat
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_trapezoid
from scipy.spatial.transform import Rotation

# --- Configuration ---
FILE_PATH = 'v300s3/MPU6050RM3100.mat'
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
def calculate_position(acceleration, dt, fs):
    """Double integrates acceleration with drift compensation."""
    # 1. Acceleration -> Velocity
    velocity = cumulative_trapezoid(acceleration, dx=dt, axis=0, initial=0)
    velocity = butter_highpass_filter(velocity, cutoff=0.02, fs=fs, order=2)
    
    # 2. Velocity -> Position
    position = cumulative_trapezoid(velocity, dx=dt, axis=0, initial=0)
    position = butter_highpass_filter(position, cutoff=0.02, fs=fs, order=2)
    
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
    
    # 3. Denoise and Calculate Positions
    filtered_accel = butter_lowpass_filter(world_accel_mm, cutoff=5.0, fs=FS, order=4)
    
    raw_position = calculate_position(world_accel_mm, DT, FS)
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
    
    # 5. Plotting the 2D Error Graph
    time_axis = np.arange(len(raw_error)) * DT
    
    plt.figure(figsize=(10, 6))
    
    plt.plot(time_axis, raw_error, label=f'Raw Error (RMSE: {raw_rmse:.0f}mm)', color='red', alpha=0.6, linewidth=1.5)
    plt.plot(time_axis, filtered_error, label=f'Denoised Error (RMSE: {filtered_rmse:.0f}mm)', color='green', linewidth=2.5)
    
    plt.title('Position Estimation Error Over Time\n(Distance from Ground Truth)', fontsize=14)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Error Distance (millimeters)', fontsize=12)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()