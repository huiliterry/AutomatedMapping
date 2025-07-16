# Processing - Erdas IMAGE convert
from osgeo import gdal
import ColorTable
import ColorTool
gdal.UseExceptions()



def convert_tiff_to_erdas(input_tiff_path, output_erdas_path):
    """
    Converts a TIFF image to ERDAS Imagine (.img) format.

    Args:
        input_tiff_path (str): Path to the input TIFF file.
        output_erdas_path (str): Path for the output ERDAS Imagine file.
    """
    try:
        # Set GDAL cache to 5 GB
        gdal.SetCacheMax(5120 * 1024 * 1024)  # 5120 MB = 5 GB
        # Open the input TIFF dataset
        src_ds = gdal.Open(input_tiff_path)
        if src_ds is None:
            print(f"Error: Could not open input TIFF file: {input_tiff_path}")
            return

        # Get the ERDAS Imagine driver
        driver = gdal.GetDriverByName('HFA') # 'HFA' is the driver for ERDAS Imagine (.img)
        if driver is None:
            print("Error: HFA (ERDAS Imagine) driver not found.")
            return

        # Create the output dataset in ERDAS Imagine format
        # The CreateCopy method handles copying all georeferencing and band information
        dst_ds = driver.CreateCopy(output_erdas_path, src_ds, 0, options=["COMPRESS=YES"])

        # Close the datasets to release resources
        src_ds = None
        dst_ds = None

        print(f"Conversion successful: {input_tiff_path} converted to {output_erdas_path}")
        

    except Exception as e:
        print(f"An error occurred during conversion: {e}")

