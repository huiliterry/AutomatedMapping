from osgeo import gdal
import numpy as np
import os

def reset_pixel_values_to_cog(input_path, cog_path, old_values, new_values, nodata_value=0):
    """
    Reset specified pixel values in a raster and save the result as a 
    Cloud-Optimized GeoTIFF (COG).

    This function reads the input raster in blocks to avoid memory overload, 
    replaces specified pixel values according to the `old_values` → `new_values` mapping, 
    writes the modified data to a temporary GeoTIFF, and then converts it to 
    a Cloud-Optimized GeoTIFF (COG).

    Parameters
    ----------
    input_path : str
        Path to the input raster file (GeoTIFF or similar format).
    cog_path : str
        Path where the final Cloud-Optimized GeoTIFF will be saved.
    old_values : list or tuple of numeric
        List of pixel values in the raster that need to be replaced.
    new_values : list or tuple of numeric
        List of replacement pixel values corresponding to `old_values`. 
        Must be the same length as `old_values`.
    nodata_value : numeric, optional
        The NoData value to set in the output raster. Defaults to 0.

    Notes
    -----
    - The function processes the raster block-by-block (default 512×512 pixels) to 
      minimize memory usage.
    - Intermediate results are stored in a temporary file (`temp_reset.tif`), 
      which is deleted after conversion to COG.
    - Output COG is LZW compressed, internally tiled, and supports BigTIFF if needed.
    - By default, the function handles 8-bit (`GDT_Byte`) rasters, but this can be 
      changed to `GDT_Float32` or `GDT_UInt16` depending on the data type.

    Example
    -------
    >>> reset_pixel_values_to_cog(
    ...     input_path='input.tif',
    ...     cog_path='output_cog.tif',
    ...     old_values=[1, 2, 3],
    ...     new_values=[10, 20, 30],
    ...     nodata_value=0
    ... )
    Cloud-Optimized COG created at: output_cog.tif
    """
    # Create a temporary file to hold modified raster
    temp_path = 'temp_reset.tif'

    # Step 1: Open input raster (read-only)
    src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
    if src_ds is None:
        raise RuntimeError("Failed to open input raster.")

    # Get raster metadata
    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    projection = src_ds.GetProjection()
    geotransform = src_ds.GetGeoTransform()
    band = src_ds.GetRasterBand(1)

    # Create temporary output GeoTIFF to write modified pixel values
    driver = gdal.GetDriverByName('GTiff')
    temp_ds = driver.Create(
        temp_path,
        xsize,
        ysize,
        1,
        gdal.GDT_Byte   # Change to GDT_Float32 or GDT_UInt16 if needed
    )
    temp_ds.SetProjection(projection)
    temp_ds.SetGeoTransform(geotransform)

    out_band = temp_ds.GetRasterBand(1)
    out_band.SetNoDataValue(nodata_value)  # Set NoData value to 0

    # Process the image block by block to avoid memory overload
    block_size = 512
    for y in range(0, ysize, block_size):
        rows = min(block_size, ysize - y)
        for x in range(0, xsize, block_size):
            cols = min(block_size, xsize - x)

            # Read a block from input raster
            data = band.ReadAsArray(xoff=x, yoff=y, xsize=cols, ysize=rows)

            # Loop through each old → new mapping
            for o_val, n_val in zip(old_values, new_values):
                data[data == o_val] = n_val

            # Write the block to the temporary output raster
            out_band.WriteArray(data, xoff=x, yoff=y)

    # Flush changes and close temporary dataset
    out_band.FlushCache()
    del temp_ds

    # Step 2: Convert the temporary file to a Cloud-Optimized GeoTIFF (COG)
    translate_options = gdal.TranslateOptions(
        format='COG',
        creationOptions=[
            'COMPRESS=LZW',        # Use LZW compression
            'BIGTIFF=YES',         # Use BigTIFF if needed
            'BLOCKSIZE=512'        # Block size (for internal tiling)
        ],
        noData=nodata_value        # Set NoData in COG output too
    )
    gdal.Translate(cog_path, temp_path, options=translate_options)

    # Step 3: Clean up temporary file
    os.remove(temp_path)
    print(f"Cloud-Optimized COG created at: {cog_path}")
