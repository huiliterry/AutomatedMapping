import glob
import os
from osgeo import gdal
gdal.UseExceptions()


# Function - S2 mosaic
def mosaicoutputVRT(inputfolder_path,outputfolder_path,file_name):
    """
    Mosaics multiple GeoTIFF files from a specified input folder into a single GeoTIFF.

    This function scans a given input folder for all `.tif` files, builds a 
    temporary Virtual Raster Tile (VRT) to mosaic them, and then translates 
    the VRT into a compressed, tiled GeoTIFF. The resulting mosaic is saved 
    in the specified output folder with the given file name.

    Parameters
    ----------
    inputfolder_path : str
        Path to the folder containing the input `.tif` files to be mosaicked.
    outputfolder_path : str
        Path to the folder where the final mosaic GeoTIFF will be saved. 
        The folder will be created if it does not exist.
    file_name : str
        Name of the output GeoTIFF file (including `.tif` extension).

    Processing Steps
    ----------------
    1. Search the `inputfolder_path` for all `.tif` files.
    2. Build a temporary `.vrt` mosaic using `gdal.BuildVRT` with `srcNodata=0`.
    3. Translate the `.vrt` to a GeoTIFF with:
       - LZW compression
       - Internal tiling
       - BigTIFF support
       - Multi-threaded processing
    4. Save the mosaic to `outputfolder_path` under the provided `file_name`.
    5. Remove the temporary `.vrt` file after processing.

    Notes
    -----
    - NoData values are set to `0` for both source and output.
    - This function uses all available CPU threads for faster translation.
    - Suitable for mosaicking large raster datasets.

    Example
    -------
    >>> mosaicoutputVRT(
    ...     inputfolder_path="/path/to/input_tifs",
    ...     outputfolder_path="/path/to/output",
    ...     file_name="final_mosaic.tif"
    ... )
    Found 10 files for mosaicking.
    Mosaic written to: /path/to/output/final_mosaic.tif

    Dependencies
    ------------
    - GDAL (Python bindings)
    - glob
    - os
    """
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
    # outputfolder_path = os.path.join('/content/drive/MyDrive', outputfolder)
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
