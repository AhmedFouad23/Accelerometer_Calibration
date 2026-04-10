import numpy as np
from scipy.io import loadmat
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_trapezoid
from scipy.spatial.transform import Rotation

FILE_PATH = 'v1500s1/MPU6050RM3100.mat'
FS = 100.0  
DT = 1.0 / FS 

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

scipy_quats = np.column_stack((quats[:, 1], quats[:, 2], quats[:, 3], quats[:, 0]))
rotations = Rotation.from_quat(scipy_quats)
world_accel = rotations.apply(raw_accel)
world_accel[:, 2] -= 1.0 

SCALE_FACTOR = 9810.0 
world_accel_mm = world_accel * SCALE_FACTOR

def butter_lowpass_filter(data, cutoff, fs, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype='low', analog=False)
    return filtfilt(b, a, data, axis=0)

def butter_highpass_filter(data, cutoff, fs, order=2):
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype='high', analog=False)
    return filtfilt(b, a, data, axis=0)

def calculate_position(acceleration, dt, fs, hp_cutoff):
    velocity = cumulative_trapezoid(acceleration, dx=dt, axis=0, initial=0)
    velocity = butter_highpass_filter(velocity, cutoff=hp_cutoff, fs=fs, order=2)
    position = cumulative_trapezoid(velocity, dx=dt, axis=0, initial=0)
    position = butter_highpass_filter(position, cutoff=hp_cutoff, fs=fs, order=2)
    return position

best_rmse = float('inf')
best_lp = 0
best_hp = 0

for lp in [1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0]:
    filtered_accel = butter_lowpass_filter(world_accel_mm, cutoff=lp, fs=FS, order=4)
    for hp in [0.005, 0.01, 0.02, 0.05, 0.1, 0.2]:
        pos = calculate_position(filtered_accel, DT, FS, hp)
        pos += ground_truth_pos[0]
        rmse = np.sqrt(np.mean(np.linalg.norm(pos - ground_truth_pos, axis=1)**2))
        print(f"LP: {lp}, HP: {hp}, RMSE: {rmse}")
        if rmse < best_rmse:
            best_rmse = rmse
            best_lp = lp
            best_hp = hp

print(f'Best LP: {best_lp}, Best HP: {best_hp}, Best RMSE: {best_rmse}')