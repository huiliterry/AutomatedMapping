import os
from osgeo import gdal


#add color table to a Geotiff image
def add_color_table(tif_path, color_table_dict, nodata_val=0):
    """
    Apply a color table to a single-band raster in place.

    This function updates an existing GeoTIFF file by assigning a color
    table (palette) to its first raster band. It also sets a NoData value
    and makes the NoData pixels transparent.

    Parameters
    ----------
    tif_path : str
        Path to the GeoTIFF file to update. The file must be writable.
    color_table_dict : dict[int, tuple[int, int, int]]
        A mapping from integer pixel values to RGB colors.
        Example: {1: (0, 255, 0), 2: (255, 0, 0)}.
        Alpha (transparency) is automatically set to 255 for all values
        except the NoData value.
    nodata_val : int, optional
        Pixel value to be treated as NoData (default is 0).
        This value will be assigned a fully transparent color.

    Raises
    ------
    RuntimeError
        If the GeoTIFF file cannot be opened in update mode.

    Notes
    -----
    - This function modifies the raster file **in place**.
    - The color table is applied to the first raster band only.
    - No reprojection, resampling, or band changes are performed.
    - Works for paletted (Indexed Color) rasters, not continuous rasters.

    Example
    -------
    >>> color_map = {
    ...     1: (0, 255, 0),    # Green
    ...     2: (255, 0, 0),    # Red
    ...     3: (0, 0, 255)     # Blue
    ... }
    >>> add_color_table("landcover.tif", color_map, nodata_val=0)
    Color table applied in place to: landcover.tif
    """

    # Open raster in update mode
    ds = gdal.Open(tif_path, gdal.GA_Update)
    if ds is None:
        raise RuntimeError(f"Cannot open file for update: {tif_path}")

    band = ds.GetRasterBand(1)

    # Set NoData value
    band.SetNoDataValue(nodata_val)

    # Define color table
    ct = gdal.ColorTable()
    for val, rgb in color_table_dict.items():
        ct.SetColorEntry(val, (*rgb, 255))  # RGBA
    ct.SetColorEntry(nodata_val, (255, 255, 255, 0))  # Transparent for NoData

    # Apply color table and interpretation
    band.SetColorTable(ct)
    band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)

    band.FlushCache()
    ds = None
    print(f"Color table applied in place to: {tif_path}")


#add color table to a COG image
def apply_color_table_as_new_cog(input_output_tif, color_table_dict, nodata_val=0):
    """
    Apply a color table to a raster and save it as a new Cloud Optimized GeoTIFF (COG).

    This function converts an existing raster into a palette-based GeoTIFF,
    applies a color table (with transparency for NoData values), and then
    rewrites it as a compressed COG file in place.

    Parameters
    ----------
    input_output_tif : str
        Path to the raster file to process. The file will be overwritten
        with the new COG containing the applied color table.
    color_table_dict : dict[int, tuple[int, int, int]]
        A mapping from integer pixel values to RGB colors.
        Example: {1: (0, 255, 0), 2: (255, 0, 0)}.
        Alpha (transparency) is automatically set to 255 for all values
        except the NoData value.
    nodata_val : int, optional
        Pixel value to be treated as NoData (default is 0).
        This value will be assigned a fully transparent color.

    Raises
    ------
    RuntimeError
        If the input file cannot be opened.
    PermissionError
        If the temporary file cannot be deleted after processing.

    Notes
    -----
    - The process creates an intermediate temporary GeoTIFF (`temp_palette.tif`)
      before writing the final COG.
    - The output COG is compressed using LZW.
    - The color table is applied only to the first raster band.
    - Uses nearest-neighbor resampling to preserve categorical raster values.

    Workflow
    --------
    1. Open the input raster and read metadata.
    2. Create a temporary palette-based GeoTIFF.
    3. Apply the provided color table and set transparency for NoData.
    4. Translate the intermediate file into a compressed COG format.
    5. Delete the temporary file.

    Example
    -------
    >>> color_map = {
    ...     1: (0, 255, 0),    # Green
    ...     2: (255, 0, 0),    # Red
    ...     3: (0, 0, 255)     # Blue
    ... }
    >>> apply_color_table_as_new_cog("landcover_cog.tif", color_map, nodata_val=0)
    Color table successfully applied and saved to COG: landcover_cog.tif
    """
    # Open source raster
    src_ds = gdal.Open(input_output_tif)
    # src_band = src_ds.GetRasterBand(1)
    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    geotransform = src_ds.GetGeoTransform()
    projection = src_ds.GetProjection()

    print("Source data type:", src_ds.GetRasterBand(1).DataType)

    # Create intermediate palette-based GeoTIFF
    temp_path = "temp_palette.tif"
    driver = gdal.GetDriverByName("GTiff")
    dst_ds = driver.Create(temp_path, xsize, ysize, 1, gdal.GDT_Byte, ['PHOTOMETRIC=PALETTE'])
    dst_ds.SetGeoTransform(geotransform)
    dst_ds.SetProjection(projection)
    
    # Copy data using nearest-neighbor to preserve classes
    gdal.ReprojectImage(src_ds, dst_ds, projection, projection, gdal.GRA_NearestNeighbour)

    # Apply color table
    band = dst_ds.GetRasterBand(1)
    band.SetNoDataValue(nodata_val)
    ct = gdal.ColorTable()
    for val, rgb in color_table_dict.items():
        ct.SetColorEntry(val, (*rgb, 255))  # RGBA
    ct.SetColorEntry(nodata_val, (255, 255, 255, 0))  # Transparent for NoData
    band.SetColorTable(ct)
    band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)

    dst_ds.FlushCache()
    dst_ds = None
    src_ds = None

    # Now convert to COG
    cog_ds = gdal.Translate(
        input_output_tif,
        temp_path,
        format='COG',
        creationOptions=['COMPRESS=LZW']
    )
    cog_ds = None
    # Delete temporary file
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except PermissionError:
        print(f"Warning: Could not delete {temp_path} due to permission error.")

    print(f"Color table successfully applied and saved to COG: {input_output_tif}")
