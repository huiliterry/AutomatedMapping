"""
In-Season Crop Mapping Automation Script
----------------------------------------

This script automates the generation of in-season crop classification maps 
for the Conterminous United States (CONUS) using Landsat 8/9 and Sentinel-2 data.

Main Features:
--------------
1. Authenticate and initialize Google Earth Engine.
2. Define temporal parameters based on the current date, focusing on the previous month.
3. Generate trusted training pixel labels using multi-year historical Crop Data Layer (CDL).
4. Run parallel classification pipelines for Landsat 8/9 and Sentinel-2 using multiprocessing:
   - Landsat 8/9 classification.
   - Sentinel-2 classification.
5. Mosaic Landsat and Sentinel-2 classification results into a 10-meter resolution mosaic.
6. Clip the mosaic to the CONUS boundary shapefile, outputting a Cloud-Optimized GeoTIFF (COG).
7. Convert the clipped COG raster to Erdas Imagine IMG format.
8. Resample the 10m COG mosaic to 30m resolution and convert to Erdas IMG format.
9. Clean up intermediate mosaic files and local classification tiles.
10. Delete processed classification files from Google Drive after a delay.
11. Log the script start time, end time, and total elapsed time.

Parameters and Paths:
---------------------
- Uses fixed file paths for shapefiles, local output directories, and Google Drive folders.
- Cloud cover thresholds for Sentinel-2 (default 10%) and Landsat 8/9 (default 15%) are defined.
- Output filenames are dynamically created using the current year and previous month.

Important Notes:
----------------
- Ensure all required Python packages are installed: `ee`, `osgeo.gdal`, `google-auth`, 
  `google-api-python-client`, `numpy`, `multiprocessing`, and custom modules 
  (TrustedPixel, ErdasConvert, MosaicL89S2, ClipRasterByShp, ResampleTool, DeleteDriveFiles).
- The script uses multiprocessing to speed up parallel execution of Landsat and Sentinel processing.
- Paths and parameters are currently hardcoded; consider parameterizing for reusability.
- The script waits 30 seconds before deleting files on Google Drive to ensure upload completion.
- Error handling uses try-except blocks to continue processing despite individual step failures.
- The CONUS boundary geometry excludes non-continental US states and territories.

Usage:
------
Run the script as a standalone Python program. The script will print status messages 
and elapsed processing time.

Example:
--------
$ python inseason_crop_mapping.py

Output:
- Mosaic, clipped, and resampled crop classification maps in both COG and Erdas IMG formats
  saved under the Results folder.
- Temporary files and Google Drive export folders cleaned up after processing.
"""

import ee

# Trigger the authentication flow.
ee.Authenticate()
# Initialize the library.
ee.Initialize(project='ee-huil7073') # replace by your cloud project name

from datetime import datetime
import os
from osgeo import gdal
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import numpy as np
from multiprocessing import Process
import TrustedPixel
import ErdasConvert
import MosaicL89S2
from AutomatedL89Mapping import L89MosaicClassification
from AutomatedS2Mapping import S2MosaicClassification
import ClipRasterByShp
import ResampleTool
import time
import DeleteDriveFiles
import shutil


# define the current time: year, month, date
# example: year, startDate, endDate, month = 2025, "2025-05-01","2025-07-17", "July"
start_time = datetime.now()
print(f"[{start_time}] Script started")
year = start_time.year
print("Year:", year)

startDate = f"{year}-05-01"
# endDate = datetime.now().strftime('%Y-%m-%d') 

month_num = start_time.month
# Move to previous month
if month_num == 1:
    prev_month_num = 12
    prev_month_year = year - 1
else:
    prev_month_num = month_num - 1
    prev_month_year = year

month = datetime(prev_month_year, prev_month_num, 1).strftime("%B")
print("startDate:month", startDate,month)


# cloud filter threshold for Sentinel-2 and Landsat 8/9
S2cloudCover = 10
L89cloudCover = 15 


# generate trusted pixel, using gap 7 (past 6 years CDL to predict current year's training labels)
CONUStrainingLabel = TrustedPixel.trustedPixels(year,7)


# define Drive export folder
root_path = '/content/drive/MyDrive/'
L89tileFolder = 'AutoInseasonL89_Mapping'
S2tileFolder = 'AutoInseasonS2_Mapping'

# define local saving folder and path
local_root_folder = '/home/hli47/InseasonMapping/Results/'
mosaicfolder_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/'
result_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/'


# define mosaic geotif image name for landsat8/9 and sentinel-2
l89_name = f"{year}{month}_L89mosaic.tif"
s2_name = f"{year}{month}_S2mosaic.tif"

# Define a geometry to cover Conterminous U.S.
CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
                    .filter(ee.Filter.neq('NAME', 'United States Virgin Islands'))
                    .filter(ee.Filter.neq('NAME', 'Puerto Rico'))
                    .filter(ee.Filter.neq('NAME', 'Alaska'))
                    .filter(ee.Filter.neq('NAME', 'Hawaii'))
                    .filter(ee.Filter.neq('NAME', 'Guam'))
                    .filter(ee.Filter.neq('NAME', 'Virgin Islands'))
                    .filter(ee.Filter.neq('NAME', 'American Samoa'))
                    .filter(ee.Filter.neq('NAME', 'Northern Mariana Islands'))
                    .filter(ee.Filter.neq('NAME', 'Commonwealth of the Northern Mariana Islands'))).union().geometry()
print("Generating CONUS boundary")


# define the process functions in the Process event
def run_landsat():
    L89MosaicClassification(startDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path,l89_name)

def run_sentinel():
    S2MosaicClassification(startDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path,s2_name)


# the automated mapping production starts at multiprocess Landsat 8/9 and Sentinel-2 classification in the Cloud platform
if __name__ == '__main__':

    # start running the multiprocess functions 
    print("Starting mapping in Sentinel-2 and Landsat8/9 datasets")
    p1 = Process(target=run_landsat)
    p2 = Process(target=run_sentinel)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Both L89 and S2 classification processes completed.")

    # ===========10m in-season crop map processing (mosaic, clip, color, Erdas)==============
    # define mosaiced, clipped, converted file's name for 10m maps
    mosaic_name_10m = f"{year}{month}CropMapMosaiced.tif"
    clip_name_10m = f"{year}{month}CropMap10m.tif"
    erdas_name_10m = f'{year}{month}CropMap10m.img'

    # define mosaiced image path
    mosaicedFilePath_10m = mosaicfolder_path +  mosaic_name_10m

    # set the path of clipping shape file covering CONUS
    shapefile = "/home/hli47/InseasonMapping/ShapeFile/CONUS_boundary_5070.shp"


    # Mosaic S2 and Landsat8/9 mosaiced image, output Geotiff with color tabel
    try:
        print('Ready to mosaic 10m L89mosaic and S2mosaic')
        MosaicL89S2.mosaic_L89_S2_gdal(mosaicfolder_path, l89_name, s2_name, mosaic_name_10m)
    except Exception as e:
        print(f"Mosaicking failed: {e}")


    #  clip mosaiced image by using CONUS shape file, output COG 
    clippedFilePath_10m = result_path +  clip_name_10m
    output_erdas_path_10m = result_path + erdas_name_10m
    try:
        print('Ready to clip 10m raster by CONUS shp_file')
        ClipRasterByShp.clip_raster_to_cog(mosaicedFilePath_10m, shapefile, clippedFilePath_10m)
    except Exception as e:
        print(f"ClipRaster failed: {e}")

    # convert 10m COG to 10m ERDAS IMG
    try:
        print('Ready to convert 10m COG raster to Erdas IMG')
        ErdasConvert.convert_tiff_to_erdas(clippedFilePath_10m, output_erdas_path_10m)
    except Exception as e:
        print(f"Convert ERDAS IMG failed: {e}")

    # ===========30m in-season crop map resample from 10m maps (resample, convert)==============
    # define resampled and converted file names and pathes of 30m maps
    resample30mCOG_name = f'{year}{month}CropMap30m.tif'
    erdas_name30m = f'{year}{month}CropMap30m.img'
    resample30mCOG_path = result_path + resample30mCOG_name
    output_erdas_path30m = result_path + erdas_name30m

    # resample 10m COG to 30m COG, output COG
    try:
        print('Ready to resample 10m COG raster to 30m')
        ResampleTool.resample(clippedFilePath_10m,resample30mCOG_path,'COG',30)
    except Exception as e:
        print(f"Add color failed: {e}")

    # convert 30m COG to 30m ERDAS IMG
    try:
        print('Ready to convert 30m COG raster to Erdas IMG')
        ErdasConvert.convert_tiff_to_erdas(resample30mCOG_path, output_erdas_path30m)
    except Exception as e:
        print(f"Convert ERDAS IMG failed: {e}")


    # ===========Delete mosaiced files==============
    l89_path = mosaicfolder_path + l89_name
    s2_path = mosaicfolder_path + s2_name


    # delete l89 mosaic image
    try:
        if os.path.exists(l89_path):
            os.remove(l89_path)
    except PermissionError:
        print(f"Warning: Could not delete {l89_path} due to permission error.")


    # delete s2 mosaic image
    try:
        if os.path.exists(s2_path):
            os.remove(s2_path)
    except PermissionError:
        print(f"Warning: Could not delete {s2_path} due to permission error.")
        

    # delete folder of download landsat 8/9 and sentinel-2 classifications 
    L89tilePath = local_root_folder + L89tileFolder
    S2tilePath = local_root_folder + S2tileFolder
    print('L89tilePath,S2tilePath', L89tilePath,S2tilePath)  
    try:
        if os.path.exists(L89tilePath):
            shutil.rmtree(L89tilePath)
        if os.path.exists(S2tilePath):
            shutil.rmtree(S2tilePath)
    except PermissionError:
        print(f"Warning: Could not delete {L89tilePath} or {S2tilePath} due to permission error.")


    # ===========Delete classifications from Google Drive==============
    time.sleep(30) # Wait for 30 seconds 
    print("Ready to delete files in Drive folder")
    DeleteDriveFiles.delete_drive_files(L89tileFolder)
    DeleteDriveFiles.delete_drive_files(S2tileFolder)
    print(f'All in-season maps in {month} have been produced, please access data via path: {result_path}')

    # calculate and return elapsed time at the end of script running
    end_time = datetime.now()
    print(f"[{end_time}] Script end")
    elapsed = end_time - start_time
    hh_mm_ss = str(elapsed).split('.')[0]
    print("Elapsed Time:", hh_mm_ss)