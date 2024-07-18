# Multimodal Landmark Annotation GUI

This is a GUI for multimodal landmark annotation and binocular camera calibration for DJI UAV.

# 1. Usage Flow 

UI for dataset annotation for stereo camera calibration and multimodal registration

## 1.1 IR-RGB Stereo Camera Calibration
- Annotation - Run the main.py file
- IR Monocular Camera Calibration - Run the calibration_ir file 
- IR-RGB Stereo Calibration - Run the calibraton_binocular file 

## 1.2 Multimodal Registration Dataset Annotation
- Annotation - Run the main.py file
- Orderly select the landmarks in the RGB and IR image.
- Click prev or next to automatically move to the previous/next data and automatically save the annotation results
- Cannot save if the number of annotated landmarks does not match
- Select .mat as the data output format
- Single click the number on the right to highlight the landmark, double click to delete.


# 2. Instructions

## 2.0 DJI Data Preprocessing
- Copy the automove.bat file to the image directory and run it as administrator, it will automatically generate folders, IR images in the thermo folder, and RGB images in the vis folder.

If you need to calculate the temperature field data:
- Open the autorun14.bat file with Notepad and modify

   E:\Sudao-Project\Landmark-Annotation\dji_thermal_sdk_v1.4_20220929\utility\bin\windows\release_x64\dji_irp.exe
    
   to your own path

- Copy the autorun14.bat to the thermo folder and run it as administrator, the generated .raw file will be copied to the raw folder

## 2.1 Calibration UI

- Select the IR image folder, RGB image folder, and calibration file storage folder in order
- Click Add RGB Corners to automatically clear all points and annotate the RGB corners
- Click prev or next to automatically move to the previous/next data and automatically save the annotation results
- Cannot save if the number of annotated landmarks does not match
- Select .mat as the data output format
- Single click the number on the right to highlight the landmark, double click to delete.


## 2.2 IR Monocular Calibration (To be updated)
- Change **landmark_path** to your landmark path
- Change **check_path** to your somewhere you like, make sure it exists 
- Change **IR_path** to your raw file path
- **verbose**: True / False, whether to report the landmarks results
- **calibration**: True / False, whether to calibrate IR camera
- **distort**: True / False, whether to save undistorted IR images
- You may find **ir_inner.txt** and **ir_distort.txt** for your usage after it completes

## 2.3 Stereo Calibration
- Change **vis_dir** to your RGB image path
- Change **landmark_path** to your landmark path 
- Change **check_path** to your somewhere you like, make sure it exists
- Change **IR_path** to your raw file path
- You may find **cam_param.npz** for your usage after it completes

# 3. Matters need attention
- Zoom in is not available. Please feel free to contribute.

## Acknowledgement
In this project, we use parts of codes in:
- Landmark-Annotation(https://github.com/han-suyu/Landmark-Annotation)

