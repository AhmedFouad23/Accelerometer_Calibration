# Calibrating and Denoising the MPU6050: A Step-by-Step Guide

## 1. The Assignment Objective
The goal of this assignment is to take raw, noisy accelerometer data from an MPU6050 sensor, apply a denoising technique, and prove that the technique works by double-integrating the data to track the sensor's 3D position over time. We validate our math by comparing our estimated path against a known "Ground Truth" trajectory recorded by a high-precision industrial robot.

## 2. The Journey: Solving the Double-Integration Problem
Tracking position purely from accelerometer data is notoriously difficult. Our script evolved through several phases to tackle the physics and math challenges:

### Phase 1: The Raw Integration Trap
Initially, we attempted to simply double-integrate the raw $X, Y, Z$ acceleration data to get velocity and then position. 
* **The Result:** The estimated path instantly drifted millions of units away from reality. 
* **The Cause:** Accelerometers pick up high-frequency mechanical vibration and static noise. Integrating this noise causes mathematical errors to compound exponentially over time.

### Phase 2: Data Cleaning and Scaling
Real-world datasets are messy.
* **Sanitization:** We added `np.nan_to_num()` to clean out missing or infinite data points that crashed the script.
* **Scaling:** We discovered the dataset recorded acceleration in $G$-forces, while the robot measured position in millimeters. We applied a scale factor of `9810.0` to convert $1G$ to $9810 \text{ mm/s}^2$.

### Phase 3: Fixing the "Gravity Leak"
Even after cleaning the data, our 3D path looked like a massive runaway curve. 
* **The Problem:** The sensor was rotating. When the robot tilted the sensor, gravity (which normally pulls down on the Z-axis) "leaked" into the X and Y axes. The script thought the sensor was accelerating sideways at $9.81 \text{ m/s}^2$.
* **The Fix:** We used the robot's known orientation (quaternions) to mathematically rotate the raw data into a stable "World Frame." Once Z was permanently pointing up, we cleanly subtracted `1.0 G` to remove gravity.

### Phase 4: The Ultimate Solution (Bandpass Filtering)
To finally lock our estimated path to the robot's real path, we implemented a dual-filter approach:
1.  **Low-Pass Filter (Sensor Denoising):** Applied to the raw acceleration to smooth out high-frequency mechanical vibrations.
2.  **High-Pass Filter (Math Denoising):** Applied during the integration steps (to velocity and position). This violently kills the low-frequency "drift" that causes the path to run away.

### Phase 5: Evaluation
To prove our enhancement, we stopped relying purely on 3D visuals. We calculated the **Root Mean Square Error (RMSE)**—the exact millimeter distance between our calculated path and the robot's true path. This allowed us to mathematically prove that the filtered data yielded a more accurate position than the raw data.

---

## 3. Hyperparameter Tuning Guide for Script 1
If you want to experiment with the script to generate different results or optimize the path, you must only adjust specific variables. 

### ✅ Variables You CAN Tune (Experiment with these)
These parameters change how aggressively the filters clean the data. Tweaking these will alter your final RMSE and the shape of your 3D plot.

* **`cutoff` in the `butter_lowpass_filter` (Currently `5.0` Hz)**
    * *What it does:* Controls how much mechanical vibration is allowed through. 
    * *How to tune:* Lowering this (e.g., to `2.0`) makes the acceleration data smoother but might cut out sudden, real movements. Raising it (e.g., to `10.0`) lets more raw vibration pass through.
* **`cutoff` in the `butter_highpass_filter` (Currently `0.02` Hz)**
    * *What it does:* Controls the "drift killing" during integration. 
    * *How to tune:* If you raise this (e.g., to `0.5`), the filter will act like a rubber band, aggressively snapping the path to the center and ruining wide, slow curves. If you lower it (e.g., to `0.005`), the filter becomes too weak, and the dreaded mathematical drift will return.

### ❌ Variables You MUST NOT Tune (Leave these fixed)
These are physical constants or hardware constraints. Changing them will break the math and invalidate your results.

* **`FS = 100.0`:** The sampling frequency. The sensor recorded data 100 times per second. Changing this breaks the time-step (`DT`) math.
* **`SCALE_FACTOR = 9810.0`:** This is the literal physics conversion of Earth's gravity to millimeters per second squared. 
* **`world_accel[:, 2] -= 1.0`:** This is the exact $1G$ of gravity we subtract from the Z-axis. Do not change this to `0.98` or `1.1`; you must handle residual static bias using the high-pass filter, not by hacking the gravity constant.