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
    print(f'The 30m COG image has been saved at {output_path}')
