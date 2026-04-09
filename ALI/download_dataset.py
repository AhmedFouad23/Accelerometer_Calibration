import os
import requests

# The base URL for raw files on GitHub
BASE_RAW_URL = "https://raw.githubusercontent.com/miguelrasteiro/IMU_dataset/master/DataSets"
FILE_NAME = "MPU6050RM3100.mat"

# The folders shown in your dataset structure
VELOCITIES = ['V1000', 'V1500', 'V_300', 'V_500', 'V_800', 'eV50p']
SEQUENCES = ['Sequencia1', 'Sequencia2', 'Sequencia3', 'Sequencia4']

def download_datasets():
    print("Starting dataset download...\n")
    
    for vel in VELOCITIES:
        for seq in SEQUENCES:
            # Construct the remote raw URL
            # Example: .../DataSets/V1000/Sequencia1/MPU6050RM3100.mat
            remote_url = f"{BASE_RAW_URL}/{vel}/{seq}/{FILE_NAME}"
            
            # Request the file header first to check if it exists (status 200)
            # This prevents downloading 404 HTML error pages
            response = requests.get(remote_url)
            
            if response.status_code == 200:
                # Format the local directory name
                # Example: V1000 + Sequencia1 -> v1000s1
                # Example: V_300 + Sequencia2 -> v300s2
                clean_vel = vel.lower().replace('_', '') 
                clean_seq = seq.replace('Sequencia', 's')
                local_dir_name = f"{clean_vel}{clean_seq}"
                
                # Create the local directory if it doesn't exist
                os.makedirs(local_dir_name, exist_ok=True)
                
                # Define local file path
                local_file_path = os.path.join(local_dir_name, FILE_NAME)
                
                # Save the file
                with open(local_file_path, 'wb') as file:
                    file.write(response.content)
                    
                print(f"[SUCCESS] Downloaded: {vel}/{seq} -> {local_file_path}")
            else:
                # Many combinations don't exist in the repo (e.g., V1000/Sequencia2)
                print(f"[SKIPPED] Does not exist: {vel}/{seq}/{FILE_NAME}")

    print("\nDownload process complete!")

if __name__ == "__main__":
    download_datasets()