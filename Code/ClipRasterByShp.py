from osgeo import gdal

def clip_raster_to_cog(input_raster_path, shapefile_path, output_cog_path,
                       compression="LZW", nodata_value=0):
    """
    Clips a raster using a vector shapefile boundary and saves it as a 
    Cloud-Optimized GeoTIFF (COG).

    This function uses GDAL's Warp functionality to:
    1. Clip an input raster to the extent of a shapefile.
    2. Apply a NoData value to areas outside the cutline.
    3. Save the output as a COG with specified compression and tiling.

    Args:
        input_raster_path (str): Path to the input raster (.tif or other GDAL-readable format).
        shapefile_path (str): Path to the vector shapefile used for clipping.
        output_cog_path (str): Path to save the output Cloud-Optimized GeoTIFF.
        compression (str, optional): Compression method for output (default: "LZW").
        nodata_value (int or float, optional): NoData value to assign to clipped areas 
            (default: 0). If None, the value is read from the input raster.

    Notes:
        - Uses GDAL's `Warp` with the COG driver.
        - By default, uses `NearestNeighbour` resampling (recommended for categorical data).
        - For continuous data, consider using `GRA_Bilinear`.
        - Requires GDAL 3.1+ for direct COG output.
        - Sets GDAL cache to 5 GB to optimize performance.

    Example:
        clip_raster_to_cog(
            input_raster_path="data/input.tif",
            shapefile_path="data/boundary.shp",
            output_cog_path="output/clipped_cog.tif"
        )
    """
    
    gdal.UseExceptions()
    # Set GDAL cache to 5 GB
    gdal.SetCacheMax(5120 * 1024 * 1024)  # 5120 MB = 5 GB

    # Determine nodata value if not provided
    if nodata_value is None:
        try:
            with gdal.Open(input_raster_path) as ds:
                band = ds.GetRasterBand(1)
                nodata_value = band.GetNoDataValue()
        except Exception:
            print("Warning: Could not retrieve NoData value from input raster. Using default -9999.0.")
            nodata_value = -9999.0

    # Creation options for a COG
    # These options are automatically handled by the COG driver in GDAL 3.1+
    # but explicitly stating them can ensure the desired configuration.
    cog_creation_options = [
        f"COMPRESS={compression}",
        "BIGTIFF=YES",
        "NUM_THREADS=ALL_CPUS",
        "BLOCKSIZE=1024"#,
        # "OPTIMIZE_SIZE=TRUE"
    ]
    # Setup warp
    warp_options = gdal.WarpOptions(
        format="COG",
        cutlineDSName=shapefile_path,
        cropToCutline=True,
        dstNodata=nodata_value,
        creationOptions=cog_creation_options,
        resampleAlg=gdal.GRA_NearestNeighbour  # or GRA_Bilinear for continuous data
    )

    # conduct clip processing
    try:
        gdal.Warp(output_cog_path, input_raster_path, options=warp_options)
        print(f"Clipping-Raster '{input_raster_path}' clipped and saved as COG successfully to '{output_cog_path}'.")
    except Exception as e:
        print(f"Error clipping raster to COG: {e}")




