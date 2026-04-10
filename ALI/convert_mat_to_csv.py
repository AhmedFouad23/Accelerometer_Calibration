import os
import glob
import numpy as np
import pandas as pd
from scipy.io import loadmat

def convert_mat_to_csv(base_dir):
    mat_files = glob.glob(os.path.join(base_dir, '**', '*.mat'), recursive=True)
    
    for mat_file in mat_files:
        try:
            print(f"Loading {mat_file}...")
            mat_data = loadmat(mat_file)
            
            # Extract data
            raw_accel = mat_data.get('SENSacc', np.array([]))
            ground_truth_pos = mat_data.get('ABBposition', np.array([]))
            quats = mat_data.get('ABBquaternion', np.array([]))
            
            if raw_accel.size == 0 or ground_truth_pos.size == 0 or quats.size == 0:
                print(f"Skipping {mat_file}: Missing expected arrays.")
                continue
            
            # Transpose if necessary (as seen in script1.py)
            if raw_accel.shape[0] == 3: raw_accel = raw_accel.T
            if ground_truth_pos.shape[0] == 3: ground_truth_pos = ground_truth_pos.T
            if quats.shape[0] == 4: quats = quats.T
                
            # Replace NaNs
            raw_accel = np.nan_to_num(raw_accel)
            ground_truth_pos = np.nan_to_num(ground_truth_pos)
            quats = np.nan_to_num(quats)
            
            # It relies on the length of data being the same across these 3
            min_len = min(len(raw_accel), len(ground_truth_pos), len(quats))
            
            # Create a dataframe
            df = pd.DataFrame({
                'Accel_X': raw_accel[:min_len, 0],
                'Accel_Y': raw_accel[:min_len, 1],
                'Accel_Z': raw_accel[:min_len, 2],
                'Pos_X': ground_truth_pos[:min_len, 0],
                'Pos_Y': ground_truth_pos[:min_len, 1],
                'Pos_Z': ground_truth_pos[:min_len, 2],
                'Quat_W': quats[:min_len, 0], # Assuming W is first based on script1
                'Quat_X': quats[:min_len, 1],
                'Quat_Y': quats[:min_len, 2],
                'Quat_Z': quats[:min_len, 3]
            })
            
            csv_path = mat_file.replace('.mat', '.csv')
            df.to_csv(csv_path, index=False)
            print(f"Successfully converted to {csv_path}")
            
        except Exception as e:
            print(f"Failed to process {mat_file}: {e}")

if __name__ == '__main__':
    base_directory = '/home/ahmedfathy0-0/Documents/my_projects/Accelerometer_Calibration/ALI'
    convert_mat_to_csv(base_directory)
    print("Done!")
