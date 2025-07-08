# %% mosaic L89 and S2 mosaiced images
import os
import ee
import json
from osgeo import gdal

def clip_raster_with_shapefile_warp(clip_folder,input_raster, input_shapefile, output_raster):
    # ... (error checking for file existence) ...
    input_raster_path = os.path.join(clip_folder,input_raster)
    output_raster_path = os.path.join(clip_folder,output_raster)
    if not os.path.exists(input_raster_path) or not os.path.exists(input_shapefile):
        raise FileNotFoundError("One or both (Input raster and shape file) are missing. Clipping step aborted.")


    warp_options = gdal.WarpOptions(
        format="GTiff",
        cutlineDSName=input_shapefile,
        cropToCutline=True,
        dstNodata=0,                       # pick a real NoData value
        creationOptions=[
            "COMPRESS=DEFLATE",            # or LZW / JPEG / ZSTD
            "PREDICTOR=2",                 # helps DEFLATE & LZW on imagery
            "TILED=YES",
            "BLOCKXSIZE=512",
            "BLOCKYSIZE=512",
            "SPARSE_OK=YES",               # skip empty tiles
            "BIGTIFF=IF_SAFER"
        ],
        warpOptions=[
            "NUM_THREADS=ALL_CPUS",
            "OPTIMIZE_SIZE=YES"            # tile‑aligned I/O → smaller file
        ]
    )
    try:
        print("Ready to clip raster by shap file.")
        gdal.Warp(output_raster_path, 
                  input_raster_path, 
                  options=warp_options,
                  multithread=True)
        print(f"Successfully clipped and saved to '{output_raster_path}'")
    except Exception as e:
        print(f"An error occurred during clipping: {e}")


# shp_path  = "../ShapeFile/CONUS_boundary_5070.shp"
# mosaiced_name = "June_L89_S2_merged.tif"
# cliped_name = "June_L89_S2_clip.tif"
# raster_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'
# output_cliped_raster = os.path.join(raster_path, cliped_name)
# input_cliped_raster = os.path.join(raster_path, mosaiced_name)

# clip_raster_with_shapefile_warp(
#     input_cliped_raster,
#     shp_path,
#     output_cliped_raster
# )