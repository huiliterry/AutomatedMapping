from osgeo import gdal
gdal.UseExceptions()


def resample(input_path,output_path,format,cell_size):
    """
    Resample a raster image to a specified cell size and save it in a given format.

    This function uses GDAL's Warp utility to resample an input raster using the
    Nearest Neighbor method, compress the output, and optionally create a BigTIFF.
    The output raster will have equal x and y resolution.

    Parameters
    ----------
    input_path : str
        Path to the input raster file.
    output_path : str
        Path to save the resampled raster file.
    format : str
        GDAL-supported output format (e.g., "GTiff", "COG").
    cell_size : float
        Desired output pixel size (resolution) in the units of the raster's coordinate system.

    Notes
    -----
    - Resampling method: Nearest Neighbor (fast, preserves class values).
    - Output compression: LZW.
    - BIGTIFF is enabled for large files.
    - Make sure GDAL is installed and imported before calling this function.

    Example
    -------
    >>> resample("input.tif", "output_30m.tif", "GTiff", 30)
    The 30m COG image has been saved at output_30m.tif
    """
    resampled_img = gdal.Warp(
        destNameOrDestDS=output_path,
        srcDSOrSrcDSTab=input_path,
        format=f'{format}',
        xRes=cell_size,
        yRes=cell_size,
        resampleAlg='Nearest Neighbor',
        creationOptions=[
            'COMPRESS=LZW',
            'BIGTIFF=YES'
        ]
    )
    print(f'The 30m COG image has been saved at {output_path}')
