# %% mosaic L89 and S2 mosaiced images
import os
from osgeo import gdal


def mosaic_L89_S2_gdal(output_path,L89name,S2name,mosaic_name):
  l89_path = os.path.join(output_path, L89name)
  s2_path = os.path.join(output_path, S2name)
  # print("l89s2 mosaiced images",l89_path,l89_path)
  if not os.path.exists(l89_path) or not os.path.exists(s2_path):
    raise FileNotFoundError("One or both classification TIFFs are missing. Mosaic step aborted.")

  input_files = [
      l89_path,
      s2_path
  ]

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

  # 3. Cleanup
  os.remove(vrt_path)

  print("Mosaic saved to:", mosaic_output)
