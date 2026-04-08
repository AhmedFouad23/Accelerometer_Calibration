# MPU6050 Accelerometer Calibration and Denoising

This repository contains the hardware and software implementation for capturing, calibrating, and filtering raw accelerometer data from an MPU6050 (GY-521) sensor. It also includes a validation step that demonstrates how denoising improves position estimation by reducing sensor drift during double integration.

## 📌 Project Overview
Estimating position purely from accelerometer data is notoriously difficult due to sensor bias and high-frequency noise. A tiny error in acceleration exponentially grows into massive positional drift when double-integrated. 

This project tackles this problem by:
1. **Data Logging:** Capturing real-world raw data from an MPU6050 via Arduino.
2. **Calibration:** Calculating and removing the inherent baseline bias of the sensor.
3. **Denoising:** Applying a Moving Average filter to smooth out random signal noise and hand-jitter.
4. **Validation:** Performing double integration (Acceleration -> Velocity -> Position) on both the raw and denoised data to mathematically and visually prove the filter's effectiveness.

## 🛠️ Hardware & Software Requirements
* **Hardware:** Arduino (Uno/Nano/Mega), GY-521 MPU6050 Sensor, Jumper Wires.
* **Software:** Arduino IDE, Python 3.x.
* **Python Libraries:** `pyserial`, `pandas`, `numpy`, `scipy`, `matplotlib`, `csv`

## 📂 Repository Structure
* `/arduino_code/` - Contains the `.ino` sketch to configure the MPU6050 and stream raw data over I2C at 115200 baud.
* `/python_scripts/`
  * `logger.py` - Connects to the Arduino via USB, features a 3-second countdown, and saves the serial data directly into a `.csv` file. It also prints column averages for easy bias calibration.
  * `data_processing.py` - The core analysis script. It reads the CSV, removes the bias, applies the denoising filter, performs cumulative trapezoidal integration, and plots the comparative graphs.
* `/datasets/`
  * `stationary_data.csv` - Data captured while the sensor was completely flat and still (used for finding bias and variance).
  * `movement_data.csv` - Data captured during a physical 10cm slide (used for the validation step).

## 🚀 How to Run the Project

### 1. Collect Data
1. Wire the MPU6050 to the Arduino (VCC to 5V, GND to GND, SDA to A4, SCL to A5).
2. Upload the Arduino sketch to your board.
3. Close the Arduino Serial Monitor.
4. Update the `COM_PORT` variable in `logger.py` to match your Arduino's port.
5. Run `logger.py` to record your `stationary_data.csv` and `movement_data.csv`.

### 2. Process and Validate
1. Ensure your `.csv` files are in the same directory as `data_processing.py`.
2. Run `data_processing.py`.
3. The script will automatically calculate the position estimations and generate graphs comparing the Raw Position vs. the Denoised Position.

## 📊 Results
The final plots successfully demonstrate that applying a denoising filter significantly reduces the rapid exponential drift caused by double-integrating raw sensor noise, resulting in a much more stable and realistic position estimation.