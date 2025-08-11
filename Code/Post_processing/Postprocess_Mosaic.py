

# %% mosaic L89 and S2 mosaiced images
import os
from osgeo import gdal
import ColorTable
import ColorTool
gdal.UseExceptions()


def mosaic_L89_S2_gdal_multi(output_path,input_files,mosaic_name):
  vrt_path = os.path.join(output_path, 'temp_mosaic.vrt')
  mosaic_output = os.path.join(output_path, mosaic_name)

  # 1. Build virtual mosaic
  vrt_options = gdal.BuildVRTOptions(srcNodata=0, VRTNodata=0)  # if 0 is NoData
  gdal.BuildVRT(vrt_path, input_files, options=vrt_options)

  # 2. Translate VRT to GeoTIFF using parallel write
  translate_options = gdal.TranslateOptions(format='GTiff', creationOptions=[
      'TILED=YES',
      'COMPRESS=LZW',
      'BIGTIFF=YES',
      'NUM_THREADS=ALL_CPUS'
  ])
  gdal.Translate(mosaic_output, vrt_path, options=translate_options)
  print(f'Mosaiced raster of L89 and S2 has been saved at {mosaic_output}')
  # 3. Cleanup
  os.remove(vrt_path)

  # 4. Color table
  color_table = ColorTable.color_table_Arc()
  ColorTool.add_color_table(mosaic_output,color_table)



year, startDate, endDate, month = 2025, "2025-05-01","2025-08-01", "July"
mosaicfolder_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/'
result_path = '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/'
mosaic_name_10m = f"{month}{year}CropMapMosaicedAgain.tif"
clip_name_10m = f"{month}{year}CropMap10m.tif"
erdas_name_10m = f'{month}{year}CropMap10m.img'
shapefile = "/home/hli47/InseasonMapping/ShapeFile/CONUS_boundary_5070.shp"

mosaicedFilePath_10m = mosaicfolder_path +  mosaic_name_10m
l89_name = f"{month}{year}_L89mosaic.tif"
s2_name = f"{month}{year}_S2mosaic.tif"

input_files = ['/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/July2025CropMapMosaicedL89S2.tif',
               '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/July2025CropMap10m.tif']
mosaic_L89_S2_gdal_multi(mosaicfolder_path, input_files, mosaicedFilePath_10m)

#  '/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/July2025CropMap10mGray.tif',