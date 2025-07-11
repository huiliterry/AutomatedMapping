import glob
import os
from osgeo import gdal

# Function - S2 mosaic
def mosaicoutputVRT(inputfolder_path,outputfolder_path,file_name):
    # Build full folder path
    tif_files = glob.glob(os.path.join(inputfolder_path, '*.tif'))
    print(f"Found {len(tif_files)} files for mosaicking.")

    if not tif_files:
        print("No .tif files found.")
        return

    # Create temporary VRT (Virtual Raster Tile)
    vrt_path = os.path.join(inputfolder_path, "temp_mosaic.vrt")
    vrt_options = gdal.BuildVRTOptions(srcNodata=0, VRTNodata=0)
    vrt = gdal.BuildVRT(vrt_path, tif_files, options=vrt_options)
    if vrt is None:
        print("VRT build failed.")
        return
    vrt = None  # Close the VRT handle

    # Define output mosaic path
    os.makedirs(outputfolder_path, exist_ok=True)
    out_fp = os.path.join(outputfolder_path, file_name)

    # Translate VRT to compressed GeoTIFF using tiling and LZW compression
    translate_options = gdal.TranslateOptions(
        format='GTiff',
        creationOptions=[
            'TILED=YES',
            'COMPRESS=LZW',
            'BIGTIFF=YES',  # Use for large outputs
            'NUM_THREADS=ALL_CPUS'
        ]
    )
    gdal.Translate(out_fp, vrt_path, options=translate_options)
    print(f"Mosaic written to: {out_fp}")

    # Optional: remove temporary VRT
    os.remove(vrt_path)
