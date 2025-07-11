
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
from AutomatedL89Mapping import L89MosaicClassification
from AutomatedS2Mapping import S2MosaicClassification
import MosaicL89S2
import ClipRasterByShp
import RemapTable
import ColorTable
import ColorTool
import ErdasConvert

# Path to your downloaded JSON key
SERVICE_ACCOUNT = 'automatedmapping@ee-huil7073.iam.gserviceaccount.com'
KEY_FILE = '../KEY/ee-huil7073-0802b07b2350.json'
# KEY_FILE = os.path.join("..","KEY",'ee-huil7073-81b7212a3bd2.json')

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
mosaicfolder_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic/'
l89_name = month + "_L89mosaic.tif"
s2_name = month + "_S2mosaic.tif"
mosaiced_raster_name = month + "_L89_S2_merged.tif"
shpfile_path  = "../ShapeFile/CONUS_boundary_5070.shp"

# # Define a geometry to cover Conterminous U.S.
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
# print('CONUSBoundary.type()',CONUSBoundary.type().getInfo())
# CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
#                     .filter(ee.Filter.eq('NAME', 'Nebraska'))).geometry()

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
    
    # ========== FUNCTIONS ==========

    # mosaic L89 and S2 mosaiced images
    # try:
    #     MosaicL89S2.mosaic_L89_S2_gdal(mosaicfolder_path, l89_name, s2_name, mosaiced_raster_name)
    # except Exception as e:
    #     print(f"Mosaicking failed: {e}")

    # clip mosaiced image by using CONUS shapefile
    # try:
    #     ClipRasterByShp.clip_raster_with_shapefile_warp(mosaicfolder_path,mosaiced_raster_name, shpfile_path, cliped_raster_name)
    # except Exception as e:
    #     print(f"Clipping failed: {e}")
    # ========== CONFIGURATION ==========

    # Remap table
    # remap_dict = RemapTable.remap_values()

    # # Color table
    # color_table = ColorTable.color_table_Arc()
    
    # #  remap and add color to clipped image
    # cliped_raster_name = mosaicfolder_path + month + "_L89_S2_clipped.tif"  
    # mosaicedFilePath = mosaicfolder_path +  mosaiced_raster_name
    # outcolor_tif = mosaicfolder_path + f'{month}_L89_S2_color.tif'
    
    # try:
    #     # output color image to folderPath+f'/{month}_L89_S2_remapcolor.tif'
    #     ColorTool.add_color_table(cliped_raster_name, color_table)
    # except Exception as e:
    #     print(f"Post-processing failed: {e}")

   
    # output_erdas_path = mosaicfolder_path + f'/{month}_L89_S2_erdas.img'
    # try:
    #     ErdasConvert.convert_tiff_to_erdas(outcolor_tif, output_erdas_path)
    # except Exception as e:
    #     print(f"Post-processing failed: {e}")
 

