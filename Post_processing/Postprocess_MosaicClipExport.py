import ee

# Trigger the authentication flow.
ee.Authenticate()
# Initialize the library.
ee.Initialize(project='ee-huil7073')

from datetime import datetime
import os
import shutil
import time
import TrustedPixel
import MosaicL89S2
import ClipRasterByShp
import ErdasConvert
import ResampleTool
import DeleteDriveFiles

 
year, month = 2025, "June"
L89tileFolder = 'AutoInseasonL89_Mapping'
S2tileFolder = 'AutoInseasonS2_Mapping'
local_root_folder = '/home/hli47/InseasonMapping/Results/'
# mosaicfolder_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/'
result_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/'

l89_name = f"{month}{year}_L89mosaic.tif"
s2_name = f"{month}{year}_S2mosaic.tif"

# ===========10m in-season crop map processing (mosaic, clip, color, Erdas)==============
# pre-set file's name and path for 10m
mosaic_name_10m = f"{year}{month}CropMapMosaiced.tif"
clip_name_10m = f"{year}{month}CropMap10m.tif"
erdas_name_10m = f'{year}{month}CropMap10m.img'
shapefile = "/home/hli47/InseasonMapping/ShapeFile/CONUS_boundary_5070.shp"

mosaicedFilePath_10m = result_path +  mosaic_name_10m

# # clip mosaiced image by using CONUS shape file, output COG with color tabel
clippedFilePath_10m = result_path +  clip_name_10m
output_erdas_path_10m = result_path + erdas_name_10m
# try:
#     print('Ready to clip 10m raster by CONUS shp_file')
#     ClipRasterByShp.clip_raster_to_cog(mosaicedFilePath_10m, shapefile, clippedFilePath_10m)
# except Exception as e:
#     print(f"ClipRaster failed: {e}")

# # convert 10m COG to 10m ERDAS IMG
try:
    print('Ready to convert 10m COG raster to Erdas IMG')
    ErdasConvert.convert_tiff_to_erdas(clippedFilePath_10m, output_erdas_path_10m)
except Exception as e:
    print(f"Convert ERDAS IMG failed: {e}")

# ===========30m in-season crop map resample from 10m maps==============
# pre-set file's name and path for 30m
resample30mCOG_name = f'{year}{month}CropMap30m.tif'
erdas_name30m = f'{year}{month}CropMap30m.img'
resample30mCOG_path = result_path + resample30mCOG_name
output_erdas_path30m = result_path + erdas_name30m

# resample 10m COG to 30m COG, output COG with color tabel
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

print(f'All in-season maps in {month} have been produced, please access data via path: {result_path}')