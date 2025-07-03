# Delete specific folder# %%
def delete_folder(folder_path_to_delete):
  try:
      shutil.rmtree(folder_path_to_delete)
      print(f"Folder deleted successfully: {folder_path_to_delete}")
  except FileNotFoundError:
      print(f"Error: Folder not found at {folder_path_to_delete}")
  except Exception as e:
      print(f"Error deleting folder {folder_path_to_delete}: {e}")

# %%
# # Define a geometry to cover Conterminous U.S.
# CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
#                     .filter(ee.Filter.neq('NAME', 'United States Virgin Islands'))
#                     .filter(ee.Filter.neq('NAME', 'Puerto Rico'))
#                     .filter(ee.Filter.neq('NAME', 'Alaska'))
#                     .filter(ee.Filter.neq('NAME', 'Hawaii'))
#                     .filter(ee.Filter.neq('NAME', 'Guam'))
#                     .filter(ee.Filter.neq('NAME', 'Virgin Islands'))
#                     .filter(ee.Filter.neq('NAME', 'American Samoa'))
#                     .filter(ee.Filter.neq('NAME', 'Northern Mariana Islands'))
#                     .filter(ee.Filter.neq('NAME', 'Commonwealth of the Northern Mariana Islands'))).union().geometry()


# %%
# def mosaic_remap_collor_conver(startDate,endDate,month,L89cloudCover,S2cloudCover,CONUSBoundary,CONUStrainingLabel, L89tileFolder,S2tileFolder,local_root_folder,mosaicfolder_path):
#     def run_landsat():
#         # image title: month+"_L89mosaic_output.tif"
#         L89MosaicClassification(startDate, endDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path)

#     def run_sentinel():
#         # image title: month+"_S2mosaic_output.tif"
#         S2MosaicClassification(startDate, endDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path)

#     if __name__ == '__main__':
#         p1 = Process(target=run_landsat)
#         p2 = Process(target=run_sentinel)

#         p1.start()
#         p2.start()

#         p1.join()
#         p2.join()

#         print("Both L89 and S2 classification processes completed.")
#         try:
#           # output mosaiced image to folderPath+f'/{month}_L89_S2_merged.tif'
#           mosaic_L89_S2_gdal(mosaicfolder_path, month)
#           # Use shutil.rmtree() to delete the folder and its contents
#           # l89folder_path_to_delete = root_path + L89tileFolder
#           # s2folder_path_to_delete = root_path + S2tileFolder
#           # delete_folder(l89folder_path_to_delete)
#           # delete_folder(s2folder_path_to_delete)
#         except Exception as e:
#             print(f"Mosaicking failed: {e}")

#         # ========== CONFIGURATION ==========

#         mosaicedFilePath = mosaicfolder_path + f'/{month}_L89_S2_merged.tif'
#         outcolor_tif = mosaicfolder_path + f'/{month}_L89_S2_remapcolor.tif'
#         output_erdas_path = mosaicfolder_path + f'/{month}_L89_S2_erdas.img'

#         # ========== FUNCTIONS ==========

#         # Remap table
#         remap_dict = remap_values()

#         # Color table
#         color_table = color_table_Arc()

#         # ========== RUN ==========
#         try:
#             # output color image to folderPath+f'/{month}_L89_S2_remapcolor.tif'
#             remap_and_color_large_raster(mosaicedFilePath, outcolor_tif, remap_dict, color_table)
#         except Exception as e:
#             print(f"Post-processing failed: {e}")

#         try:
#             # output Erdas image to folderPath+f'/{month}_L89_S2_erdas.tif'
#             convert_tiff_to_erdas(outcolor_tif, output_erdas_path)
#         except Exception as e:
#             print(f"Post-processing failed: {e}")

# %%
import os
import glob
import time
from osgeo import gdal
import ee
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import shutil
import numpy as np
from multiprocessing import Process
import TrustedPixel
import RemapColorTool
import ErdasConvert
import RemapTable
import ColorTable
import MosaicL89S2

from AutomatedL89Mapping import L89MosaicClassification
from AutomatedS2Mapping import S2MosaicClassification

# Path to your downloaded JSON key
SERVICE_ACCOUNT = 'automatedmapping@ee-huil7073.iam.gserviceaccount.com'
KEY_FILE = 'ee-huil7073-81b7212a3bd2.json'

credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_FILE)
ee.Initialize(credentials)

year = 2025
startDate = str(year) + "-05-01"
endDate = str(year) + "-07-01"
month = "June"

S2cloudCover = 15
L89cloudCover = 20 
CONUStrainingLabel = TrustedPixel.trustedPixels(year,7)

root_path = '/content/drive/MyDrive/'
L89tileFolder = 'AutoInseasonL89_MappingTest'
S2tileFolder = 'AutoInseasonS2_MappingTest'
local_root_folder = '../DownloadClassifications'
mosaicfolder_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'
l89_name = month + "_L89mosaic.tif"
s2_name = month + "_S2mosaic.tif"
mosaic_name = month + "_L89_S2_merged.tif"
# folderPath = root_path + mosaicFolder # '/content/drive/MyDrive/' could be set to any root direction

CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
                    .filter(ee.Filter.eq('NAME', 'Nebraska'))).geometry()

# mosaic_remap_collor_conver(startDate,endDate,month,L89cloudCover,S2cloudCover,CONUSBoundary,CONUStrainingLabel, L89tileFolder,S2tileFolder,local_root_folder,mosaicfolder_path)
def run_landsat():
    # image title: month+"_L89mosaic_output.tif"
    L89MosaicClassification(startDate, endDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path,l89_name)

def run_sentinel():
    # image title: month+"_S2mosaic_output.tif"
    S2MosaicClassification(startDate, endDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path,s2_name)

if __name__ == '__main__':
    p1 = Process(target=run_landsat)
    p2 = Process(target=run_sentinel)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Both L89 and S2 classification processes completed.")
    try:
        # output mosaiced image to folderPath+f'/{month}_L89_S2_merged.tif'
        MosaicL89S2.mosaic_L89_S2_gdal(mosaicfolder_path, l89_name, s2_name, mosaic_name)
        # Use shutil.rmtree() to delete the folder and its contents
        # l89folder_path_to_delete = root_path + L89tileFolder
        # s2folder_path_to_delete = root_path + S2tileFolder
        # delete_folder(l89folder_path_to_delete)
        # delete_folder(s2folder_path_to_delete)
    except Exception as e:
        print(f"Mosaicking failed: {e}")

    # ========== CONFIGURATION ==========

    mosaicedFilePath = mosaicfolder_path + '/' + mosaic_name
    outcolor_tif = mosaicfolder_path + f'/{month}_L89_S2_remapcolor.tif'
    output_erdas_path = mosaicfolder_path + f'/{month}_L89_S2_erdas.img'

    # ========== FUNCTIONS ==========

    # Remap table
    remap_dict = RemapTable.remap_values()

    # Color table
    color_table = ColorTable.color_table_Arc()
    
    # ========== RUN ==========
    try:
        # output color image to folderPath+f'/{month}_L89_S2_remapcolor.tif'
        RemapColorTool.remap_and_color_large_raster(mosaicedFilePath, outcolor_tif, remap_dict, color_table)
    except Exception as e:
        print(f"Post-processing failed: {e}")

    try:
        # output Erdas image to folderPath+f'/{month}_L89_S2_erdas.tif'
        ErdasConvert.convert_tiff_to_erdas(outcolor_tif, output_erdas_path)
    except Exception as e:
        print(f"Post-processing failed: {e}")

