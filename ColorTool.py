import os
from osgeo import gdal

def add_color_table(tif_path, color_table_dict, nodata_val=0):
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
    
    # Open source raster
    src_ds = gdal.Open(input_output_tif)
    src_band = src_ds.GetRasterBand(1)
    xsize = src_ds.RasterXSize
    ysize = src_ds.RasterYSize
    geotransform = src_ds.GetGeoTransform()
    projection = src_ds.GetProjection()

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
