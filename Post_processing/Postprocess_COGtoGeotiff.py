import os
from osgeo import gdal
gdal.UseExceptions()


def convert_cog_to_geotiff(input_path, output_path):
    # Open the input COG
    src_ds = gdal.Open(input_path, gdal.GA_ReadOnly)
    if src_ds is None:
        raise RuntimeError(f"Failed to open input file: {input_path}")

    # Set creation options: disable tiling and overviews, optional compression
    creation_options = [
        "TILED=NO",
        "COPY_SRC_OVERVIEWS=NO",
        "BIGTIFF=YES",
        "COMPRESS=LZW",  # Optional: remove if you don't want compression
        "NUM_THREADS=ALL_CPUS"
    ]

    # Use gdal.Translate to write to standard GeoTIFF
    gdal.Translate(
        destName=output_path,
        srcDS=src_ds,
        options=gdal.TranslateOptions(format='GTiff', outputType=gdal.GDT_Byte, expand='gray', creationOptions=creation_options)
    )

    print(f"Converted: {input_path} -> {output_path}")

def convert_to_grayscale(input_file, output_file):
    """
    Converts a color GeoTIFF to a grayscale GeoTIFF using gdal.Translate.

    Args:
        input_file (str): Path to the input color GeoTIFF (e.g., a COG).
        output_file (str): Path to the output grayscale GeoTIFF.
    """
    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    # Set up the options for gdal.Translate
    translate_options = gdal.TranslateOptions(
        format='GTiff',
        options=['-expand', 'gray'],
        creationOptions=['COMPRESS=LZW', 'TILED=YES', 'BIGTIFF=YES']
    )

    # Perform the translation
    try:
        gdal.Translate(output_file, input_file, options=translate_options)
        print(f"Successfully converted '{input_file}' to grayscale '{output_file}'.")
    except Exception as e:
        print(f"Error during conversion: {e}")
# Example usage
if __name__ == "__main__":
    input_file = "/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Result/July2025CropMap10m.tif"
    output_file = "/home/hli47/InseasonMapping/Results/AutoInseasonL89S2_Mosaic/July2025CropMap10mGray.tif"
    convert_to_grayscale(input_file, output_file)
