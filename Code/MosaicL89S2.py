# %% mosaic L89 and S2 mosaiced images
import os
from osgeo import gdal
import ColorTable
import ColorTool
gdal.UseExceptions()


def mosaic_L89_S2_gdal(output_path,L89name,S2name,mosaic_name):
  """
  Mosaic Landsat 8/9 and Sentinel-2 classification rasters into a single GeoTIFF
  and apply a predefined color table.

  This function:
    1. Checks for the existence of the two input raster classification files.
    2. Creates a virtual raster (VRT) mosaic from the two inputs with NoData set to 0.
    3. Converts the VRT to a compressed, tiled GeoTIFF using multi-threaded writing.
    4. Removes the temporary VRT file.
    5. Applies a predefined ArcGIS-style color table to the final mosaic.

  Parameters
  ----------
  output_path : str
      Directory containing the input raster files and where the output mosaic will be saved.
  L89name : str
      Filename of the Landsat 8/9 classification raster (GeoTIFF format).
  S2name : str
      Filename of the Sentinel-2 classification raster (GeoTIFF format).
  mosaic_name : str
      Filename for the output mosaic GeoTIFF.

  Raises
  ------
  FileNotFoundError
      If either the Landsat 8/9 or Sentinel-2 raster is missing in the output_path.
  RuntimeError
      If GDAL processing fails during VRT building, translation, or color table application.

  Notes
  -----
  - This function assumes the NoData value for both inputs is 0.
  - Uses LZW compression, tiling, and BigTIFF support for large file handling.
  - Requires `ColorTable.color_table_Arc()` and `ColorTool.add_color_table()` 
    functions to be available in the environment.

  Example
  -------
  >>> mosaic_L89_S2_gdal(
  ...     output_path="/data/mosaics",
  ...     L89name="landsat89_classified.tif",
  ...     S2name="sentinel2_classified.tif",
  ...     mosaic_name="mosaic_L89_S2.tif"
  ... )
  Mosaiced raster of L89 and S2 has been saved at /data/mosaics/mosaic_L89_S2.tif
  """
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
  print(f'Mosaiced raster of L89 and S2 has been saved at {mosaic_output}')
  # 3. Cleanup
  os.remove(vrt_path)

  # 4. Color table
  color_table = ColorTable.color_table_Arc()
  ColorTool.add_color_table(mosaic_output,color_table)