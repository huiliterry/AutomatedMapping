import ee

# Trigger the authentication flow.
ee.Authenticate()
# Initialize the library.
ee.Initialize(project='ee-huil7073')

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


# # Path to your downloaded JSON key
# SERVICE_ACCOUNT = 'automatedmapping@ee-huil7073.iam.gserviceaccount.com'
# KEY_FILE = '../KEY/ee-huil7073-0802b07b2350.json'
# # KEY_FILE = os.path.join("..","KEY",'ee-huil7073-81b7212a3bd2.json')

# credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_FILE)
# ee.Initialize(credentials)


start_time = datetime.now()
print(f"[{start_time}] Script started")
year = start_time.year
print("Year:", year)

startDate = f"{year}-05-01"
endDate = datetime.now().strftime('%Y-%m-%d') 

month_num = start_time.month
# Move to previous month
if month_num == 1:
    prev_month_num = 12
    prev_month_year = year - 1
else:
    prev_month_num = month_num - 1
    prev_month_year = year

month = datetime(prev_month_year, prev_month_num, 1).strftime("%B")
print("startDate:endDate:month", startDate,endDate,month)

# year, startDate, endDate, month = 2025, "2025-05-01","2025-07-17", "July"

S2cloudCover = 15
L89cloudCover = 20 
CONUStrainingLabel = TrustedPixel.trustedPixels(year,7)

root_path = '/content/drive/MyDrive/'
L89tileFolder = 'AutoInseasonL89_Mapping'
S2tileFolder = 'AutoInseasonS2_Mapping'
local_root_folder = '/home/hli47/InseasonMapping/Results/'
mosaicfolder_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/'

l89_name = f"{month}{year}_L89mosaic.tif"
s2_name = f"{month}{year}_S2mosaic.tif"

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

def run_landsat():
    # image title: month+"_L89mosaic_output.tif"
    L89MosaicClassification(startDate, endDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path,l89_name)

def run_sentinel():
    # image title: month+"_S2mosaic_output.tif"
    S2MosaicClassification(startDate, endDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path,s2_name)

if __name__ == '__main__':
    print("Starting mapping in Sentinel-2 and Landsat8/9 datasets")
    p1 = Process(target=run_landsat)
    p2 = Process(target=run_sentinel)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Both L89 and S2 classification processes completed.")

    # ===========10m in-season crop map processing (mosaic, clip, color, Erdas)==============
    # pre-set file's name and path for 10m
    mosaic_name_10m = f"{month}{year}CropMapMosaiced.tif"
    clip_name_10m = f"{month}{year}CropMap10m.tif"
    erdas_name_10m = f'{month}{year}CropMap10m.img'
    shapefile = "/home/hli47/InseasonMapping/ShapeFile/CONUS_boundary_5070.shp"

    mosaicedFilePath_10m = mosaicfolder_path +  mosaic_name_10m
    clippedFilePath_10m = mosaicfolder_path +  clip_name_10m
    output_erdas_path_10m = mosaicfolder_path + erdas_name_10m
    # Mosaic S2 and Landsat8/9 mosaiced image
    try:
        print('Ready to mosaic 10m L89mosaic and S2mosaic')
        MosaicL89S2.mosaic_L89_S2_gdal(mosaicfolder_path, l89_name, s2_name, mosaic_name_10m)
    except Exception as e:
        print(f"Mosaicking failed: {e}")


    # # clip mosaiced image by using CONUS shape file, output COG with color tabel
    try:
        print('Ready to clip 10m raster by CONUS shp_file')
        ClipRasterByShp.clip_raster_to_cog(mosaicedFilePath_10m, shapefile, clippedFilePath_10m)
    except Exception as e:
        print(f"ClipRaster failed: {e}")

    # # convert 10m COG to 10m ERDAS IMG
    try:
        print('Ready to convert 10m COG raster to Erdas IMG')
        ErdasConvert.convert_tiff_to_erdas(clippedFilePath_10m, output_erdas_path_10m)
    except Exception as e:
        print(f"Convert ERDAS IMG failed: {e}")

    # ===========30m in-season crop map resample from 10m maps==============
    # pre-set file's name and path for 30m
    resample30mCOG_name = f'{month}{year}CropMap30m.tif'
    erdas_name30m = f'{month}{year}CropMap30m.img'
    resample30mCOG_path = mosaicfolder_path + resample30mCOG_name
    output_erdas_path30m = mosaicfolder_path + erdas_name30m

    # resample 10m COG to 30m COG, output COG with color tabel
    try:
        print('Ready to resample 10m COG raster to 10m')
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
        
    # delete l89+s2 mosaic image       
    try:
        if os.path.exists(mosaicedFilePath_10m):
            os.remove(mosaicedFilePath_10m)
    except PermissionError:
        print(f"Warning: Could not delete {mosaicedFilePath_10m} due to permission error.")

    # delete folder of download classification  
    L89tilePath = local_root_folder + L89tileFolder
    S2tilePath = local_root_folder + S2tileFolder
    print('L89tilePath,S2tilePath', L89tilePath,S2tilePath)  
    try:
        if os.path.exists(L89tilePath):
            shutil.rmtree(L89tilePath)
        if os.path.exists(S2tilePath):
            shutil.rmtree(S2tilePath)
    except PermissionError:
        print(f"Warning: Could not delete {L89tilePath} or{S2tilePath} due to permission error.")


    # ===========Delete classification images from Google Drive==============
    time.sleep(30) # Wait for 30 seconds 
    print("Ready to delete files in Drive folder")
    DeleteDriveFiles.delete_drive_files(L89tileFolder)
    DeleteDriveFiles.delete_drive_files(S2tileFolder)
    print(f'All in-season maps in {endDate} have been produced, please access data via path: {mosaicfolder_path}')

    # calculate and return elapsed time at the end of script running
    end_time = datetime.now()
    print(f"[{end_time}] Script end")
    elapsed = end_time - start_time
    hh_mm_ss = str(elapsed).split('.')[0]
    print("Elapsed Time:", hh_mm_ss)