# %%
import numpy as np
from osgeo import gdal



def remap_and_color_large_raster(input_path, output_path, remap_dict, color_table_dict):
    # gdal.SetCacheMax(4069 * 1024 * 1024) # Set to 512 MB, adjust based on your RAM
    # Open input
    src_ds = gdal.Open(input_path)
    band = src_ds.GetRasterBand(1)

    # Create output with same metadata and compression options
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(
        output_path,
        src_ds.RasterXSize,
        src_ds.RasterYSize,
        1,
        gdal.GDT_Byte,  # Assumes classified data is within 0–255
        options=["TILED=YES", "COMPRESS=LZW", "BIGTIFF=YES", "NUM_THREADS=ALL_CPUS"]
    )
    out_ds.SetGeoTransform(src_ds.GetGeoTransform())
    out_ds.SetProjection(src_ds.GetProjection())

    in_band = src_ds.GetRasterBand(1)
    out_band = out_ds.GetRasterBand(1)

    block_xsize, block_ysize = in_band.GetBlockSize()
    xsize, ysize = src_ds.RasterXSize, src_ds.RasterYSize

    # Define NoData value
    nodata_val = 255  # Must be within 0–255 for GDT_Byte
    out_band.SetNoDataValue(nodata_val)

    # Apply color table
    ct = gdal.ColorTable()
    for val, rgb in color_table_dict.items():
      if val != 0:  # 0 is now NoData
        ct.SetColorEntry(val, (*rgb, 255))
    ct.SetColorEntry(nodata_val, (255, 255, 255, 0))  # Transparent for NoData
    
    out_band.SetRasterColorTable(ct)
    out_band.SetRasterColorInterpretation(gdal.GCI_PaletteIndex)


    print(f"Processing in blocks: {block_xsize} x {block_ysize}")
    for y in range(0, ysize, block_ysize):
        rows = min(block_ysize, ysize - y)
        for x in range(0, xsize, block_xsize):
            cols = min(block_xsize, xsize - x)
            data = in_band.ReadAsArray(x, y, cols, rows)

            if data is None:
                continue

            # Convert 0s to NoData first
            data[data == 0] = nodata_val

            # Apply pixel value remapping
            out_data = np.copy(data)
            for old_val, new_val in remap_dict.items():
                out_data[data == old_val] = new_val

            out_band.WriteArray(out_data, x, y)

    out_band.FlushCache()


    # Cleanup
    src_ds = None
    out_ds = None
    out_band = None
    print(f"Remap and color table assignment complete and saved to: {output_path}")
