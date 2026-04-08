import serial
import csv
import time

# --- CONFIGURE THESE ---
# Windows: 'COM3', 'COM4', etc.
# Mac/Linux: '/dev/tty.usbmodem...' or '/dev/ttyUSB0'
COM_PORT = 'COM11' 
BAUD_RATE = 115200
FILE_NAME = 'raw_data.csv'
COLLECTION_TIME = 3 # How many seconds of data do you want to record?

try:
    # Connect to the Arduino
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Give Arduino a moment to reset after connecting

    print(f"Connected to {COM_PORT}. Get ready...")

    # --- ADDED: 3, 2, 1 Countdown ---
    for i in range(3, 0, -1):
        print(i)
        time.sleep(1)
        
    print(f"GO! Recording data for {COLLECTION_TIME} seconds...")

    # Clear out any old data that piled up during the countdown
    ser.reset_input_buffer()

    # Create a list to store rows of numbers for averaging later
    all_numeric_data = []

    with open(FILE_NAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        start_time = time.time()
        
        while (time.time() - start_time) < COLLECTION_TIME:
            if ser.in_waiting > 0:
                # Read a line, decode it, and strip extra whitespace
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue # Skip empty lines
                
                # Split the comma-separated string into a list
                data = line.split(',')
                
                # Write to the CSV file
                writer.writerow(data)
                print(line) # Optional: print to console so you can see it working
                
                # --- ADDED: Store numeric data for averaging ---
                try:
                    # Convert the string list to a float list
                    numeric_values = [float(val) for val in data]
                    all_numeric_data.append(numeric_values)
                except ValueError:
                    # If it fails (e.g., it's a text header like "time,ax,ay"), just skip it
                    pass

    print(f"\nFinished! Data saved to {FILE_NAME}")

    # --- ADDED: Calculate and print averages ---
    if len(all_numeric_data) > 0:
        print("\n--- Column Averages ---")
        num_columns = len(all_numeric_data[0])
        
        # Column names to make the printout look nice (adjust if you use gyro)
        col_names = ["Time", "Ax", "Ay", "Az", "Gx", "Gy", "Gz"]
        
        for col_index in range(num_columns):
            # Sum up all the values in this specific column
            col_sum = sum(row[col_index] for row in all_numeric_data)
            col_avg = col_sum / len(all_numeric_data)
            
            # Pick a name for the console printout
            name = col_names[col_index] if col_index < len(col_names) else f"Column {col_index+1}"
            
            print(f"{name} Average: {col_avg:.5f}")
    else:
        print("\nNo valid numeric data was collected to average.")

except Exception as e:
    print(f"Error: {e}")
    print("Did you remember to close the Arduino Serial Monitor?")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()