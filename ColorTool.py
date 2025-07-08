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