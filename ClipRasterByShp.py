import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import geometry_mask
from rasterio.windows import Window
from shapely.geometry import shape, box
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

def clip_block(src_path, dst_path, window, geom_shapes, nodata_val):
    with rasterio.open(src_path) as src:
        block_data = src.read(1, window=window)
        transform = src.window_transform(window)
        out_shape = (block_data.shape[0], block_data.shape[1])

        # Mask outside geometry
        mask = geometry_mask(geom_shapes, transform=transform, invert=True, out_shape=out_shape)
        block_data[~mask] = nodata_val

        # Reopen destination in write mode (update mode is thread-safe if tiles don't overlap)
        with rasterio.open(dst_path, "r+") as dst:
            dst.write(block_data, 1, window=window)

def parallel_clip_raster(input_raster, clip_geojson, output_raster, nodata_val=0, max_workers=8,block_size=1024):
    print("📍 Loading clipping geometry...")
    gdf = gpd.read_file(clip_geojson)
    geom_shapes = [shape(geom) for geom in gdf.geometry]

    with rasterio.open(input_raster) as src:
        meta = src.meta.copy()
        meta.update({
            "tiled": True,
            "compress": "lzw",
            "nodata": nodata_val
        })

        print("💾 Creating output raster...")
        with rasterio.open(output_raster, "w", **meta) as dst:
            # dst.write(np.full((src.count, src.height, src.width), nodata_val, dtype=src.dtypes[0]))
            pass

        # block_width, block_height = 10240,10240 #src.block_shapes[0]
        print("block_width,block_height", block_size)
        windows = []

        print("🔍 Generating processing windows...")
        for y in range(0, src.height, block_size):
            for x in range(0, src.width, block_size):
                win = Window(x, y, block_size, block_size)
                bbox = box(*rasterio.windows.bounds(win, src.transform))
                if any(bbox.intersects(g) for g in geom_shapes):
                    windows.append(win)

    print(f"🚀 Launching parallel processing for {len(windows)} blocks with {max_workers} threads...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(clip_block, input_raster, output_raster, window, geom_shapes, nodata_val)
            for window in windows
        ]
        for i, f in enumerate(as_completed(futures), 1):
            print(f"🧱 Block {i}/{len(windows)} done")

    print("✅ Parallel clipping complete.")




# shp_path  = "../ShapeFile/CONUS_boundary_5070.shp"
# mosaiced_name = "June_L89_S2_merged.tif"
# cliped_name = "June_L89_S2_clip.tif"
# raster_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'
# output_cliped_raster = os.path.join(raster_path, cliped_name)
# input_cliped_raster = os.path.join(raster_path, mosaiced_name)

