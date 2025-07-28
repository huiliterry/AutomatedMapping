from osgeo import gdal

def clip_raster_to_cog(input_raster_path, shapefile_path, output_cog_path,
                       compression="LZW", nodata_value=0):
    """
    Clips a large raster using a shapefile and outputs a Cloud Optimized GeoTIFF (COG).

    Args:
        input_raster_path (str): Path to the input raster file (e.g., .tif).
        shapefile_path (str): Path to the shapefile to use for clipping (e.g., .shp).
        output_cog_path (str): Path to the desired output COG file.
        compression (str, optional): Compression method for the output raster. Defaults to "LZW".
                                     Common options: LZW, DEFLATE, JPEG, ZSTD.
        nodata_value (int or float, optional): Value to use for pixels outside the clip area.
                                               If None, the input raster's nodata value is used
                                               or a default is applied if not present.
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




