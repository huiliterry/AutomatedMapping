import ColorTable
import ColorTool
from osgeo import gdal
gdal.UseExceptions()


def resample(input_path,output_path,format,cell_size):
    resampled_img = gdal.Warp(
        destNameOrDestDS=output_path,
        srcDSOrSrcDSTab=input_path,
        format=f'{format}',
        xRes=cell_size,
        yRes=cell_size,
        resampleAlg='Nearest Neighbor',
        creationOptions=[
            'COMPRESS=LZW'
        ]
    )
    
    # add Color table to image
    try:
        color_table = ColorTable.color_table_Arc()
        ColorTool.apply_color_table_as_new_cog(output_path, color_table, nodata_val=0)
    except Exception as e:
        print(f"Add color failed: {e}")


# input_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic/June_18_33_2025-07-01COG10m.tif'
# output_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic/June_18_33_2025-07-01COG30m.tif'
# output_color_path  = '../DownloadClassifications/AutoInseasonL89S2_Mosaic/June_18_33_2025-07-01COG30m_color.tif'
# resample(input_path,output_path,'COG',30)