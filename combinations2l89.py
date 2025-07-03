# %% [markdown]
# Trusted Pixels

# %% [markdown]
# Processing - Mosaic L89 and S2 (S2 cover L89)

# %%
def mosaic_L89_S2_gdal(output_path,month):
  l89_path = os.path.join(output_path, f"{month}_L89mosaic.tif")
  s2_path = os.path.join(output_path, f"{month}_S2mosaic.tif")
  if not os.path.exists(l89_path) or not os.path.exists(s2_path):
    raise FileNotFoundError("One or both classification TIFFs are missing. Mosaic step aborted.")

  input_files = [
      l89_path,
      s2_path
  ]

  vrt_path = os.path.join(output_path, 'temp_mosaic.vrt')
  mosaic_output = os.path.join(output_path, f"{month}_L89_S2_merged.tif")

  # 1. Build virtual mosaic
  vrt_options = gdal.BuildVRTOptions(srcNodata=0, VRTNodata=0)  # if 0 is NoData
  gdal.BuildVRT(vrt_path, input_files, options=vrt_options)

  # 2. Translate VRT to GeoTIFF using parallel write
  translate_options = gdal.TranslateOptions(format='GTiff', creationOptions=[
      'TILED=YES',
      'COMPRESS=LZW',
      'BIGTIFF=YES',
      'NUM_THREADS=ALL_CPUS'
  ])
  gdal.Translate(mosaic_output, vrt_path, options=translate_options)

  # 3. Cleanup
  os.remove(vrt_path)

  print("Mosaic saved to:", mosaic_output)

# %% [markdown]
# Delete specific folder

# %%
def delete_folder(folder_path_to_delete):
  try:
      shutil.rmtree(folder_path_to_delete)
      print(f"Folder deleted successfully: {folder_path_to_delete}")
  except FileNotFoundError:
      print(f"Error: Folder not found at {folder_path_to_delete}")
  except Exception as e:
      print(f"Error deleting folder {folder_path_to_delete}: {e}")

# %% [markdown]
# Generate remap value table

# %%
# Remap: original → new class values
def remap_values():
  return {  0	:	255	,
            7	:	255	,
            8	:	255	,
            9	:	255	,
            15	:	255	,
            16	:	255	,
            17	:	255	,
            18	:	255	,
            19	:	255	,
            20	:	255	,
            40	:	255	,
            62	:	255	,
            73	:	255	,
            78	:	255	,
            79	:	255	,
            80	:	255	,
            84	:	255	,
            85	:	255	,
            86	:	255	,
            89	:	255	,
            90	:	255	,
            91	:	255	,
            93	:	255	,
            94	:	255	,
            95	:	255	,
            96	:	255	,
            97	:	255	,
            98	:	255	,
            99	:	255	,
            100	:	255	,
            101	:	255	,
            102	:	255	,
            103	:	255	,
            104	:	255	,
            105	:	255	,
            106	:	255	,
            107	:	255	,
            108	:	255	,
            109	:	255	,
            110	:	255	,
            113	:	255	,
            114	:	255	,
            115	:	255	,
            116	:	255	,
            117	:	255	,
            118	:	255	,
            119	:	255	,
            120	:	255	,
            125	:	255	,
            126	:	255	,
            127	:	255	,
            128	:	255	,
            129	:	255	,
            130	:	255	,
            132	:	255	,
            133	:	255	,
            134	:	255	,
            135	:	255	,
            136	:	255	,
            137	:	255	,
            138	:	255	,
            139	:	255	,
            140	:	255	,
            144	:	255	,
            145	:	255	,
            146	:	255	,
            147	:	255	,
            148	:	255	,
            149	:	255	,
            150	:	255	,
            151	:	255	,
            153	:	255	,
            154	:	255	,
            155	:	255	,
            156	:	255	,
            157	:	255	,
            158	:	255	,
            159	:	255	,
            160	:	255	,
            161	:	255	,
            162	:	255	,
            163	:	255	,
            164	:	255	,
            165	:	255	,
            166	:	255	,
            167	:	255	,
            168	:	255	,
            169	:	255	,
            170	:	255	,
            171	:	255	,
            172	:	255	,
            173	:	255	,
            174	:	255	,
            175	:	255	,
            177	:	255	,
            178	:	255	,
            179	:	255	,
            180	:	255	,
            181	:	255	,
            182	:	255	,
            183	:	255	,
            184	:	255	,
            185	:	255	,
            186	:	255	,
            187	:	255	,
            188	:	255	,
            189	:	255	,
            191	:	255	,
            192	:	255	,
            193	:	255	,
            194	:	255	,
            196	:	255	,
            197	:	255	,
            198	:	255	,
            199	:	255	,
            200	:	255	,
            201	:	255	,
            202	:	255	,
            203	:	255
          }

# %%
# Color table: class value → (R, G, B)
def color_table_Arc():
  return {  #0	:	(	0	,	0	,	0	),
            1	:	(	255	,	212	,	0	),
            2	:	(	255	,	38	,	38	),
            3	:	(	0	,	169	,	230	),
            4	:	(	255	,	158	,	15	),
            5	:	(	38	,	115	,	0	),
            6	:	(	255	,	255	,	0	),
            7	:	(	0	,	0	,	0	),
            8	:	(	0	,	0	,	0	),
            9	:	(	0	,	0	,	0	),
            10	:	(	112	,	168	,	0	),
            11	:	(	0	,	175	,	77	),
            12	:	(	224	,	166	,	15	),
            13	:	(	224	,	166	,	15	),
            14	:	(	128	,	212	,	255	),
            15	:	(	0	,	0	,	0	),
            16	:	(	0	,	0	,	0	),
            17	:	(	0	,	0	,	0	),
            18	:	(	0	,	0	,	0	),
            19	:	(	0	,	0	,	0	),
            20	:	(	0	,	0	,	0	),
            21	:	(	226	,	0	,	127	),
            22	:	(	138	,	100	,	83	),
            23	:	(	217	,	181	,	108	),
            24	:	(	168	,	112	,	0	),
            25	:	(	214	,	157	,	188	),
            26	:	(	115	,	115	,	0	),
            27	:	(	174	,	1	,	126	),
            28	:	(	161	,	88	,	137	),
            29	:	(	115	,	0	,	76	),
            30	:	(	214	,	157	,	188	),
            31	:	(	209	,	255	,	0	),
            32	:	(	128	,	153	,	255	),
            33	:	(	214	,	214	,	0	),
            34	:	(	209	,	255	,	0	),
            35	:	(	0	,	175	,	77	),
            36	:	(	255	,	168	,	227	),
            37	:	(	165	,	245	,	141	),
            38	:	(	0	,	175	,	77	),
            39	:	(	214	,	157	,	188	),
            40	:	(	0	,	0	,	0	),
            41	:	(	169	,	0	,	230	),
            42	:	(	168	,	0	,	0	),
            43	:	(	115	,	38	,	0	),
            44	:	(	0	,	175	,	77	),
            45	:	(	179	,	128	,	255	),
            46	:	(	115	,	38	,	0	),
            47	:	(	255	,	102	,	102	),
            48	:	(	255	,	102	,	102	),
            49	:	(	255	,	204	,	102	),
            50	:	(	255	,	102	,	102	),
            51	:	(	0	,	175	,	77	),
            52	:	(	0	,	222	,	176	),
            53	:	(	85	,	255	,	0	),
            54	:	(	245	,	162	,	122	),
            55	:	(	255	,	102	,	102	),
            56	:	(	0	,	175	,	77	),
            57	:	(	128	,	212	,	255	),
            58	:	(	232	,	190	,	255	),
            59	:	(	178	,	255	,	222	),
            60	:	(	0	,	175	,	77	),
            61	:	(	191	,	191	,	122	),
            62	:	(	0	,	0	,	0	),
            63	:	(	149	,	206	,	147	),
            64	:	(	199	,	215	,	158	),
            65	:	(	204	,	191	,	163	),
            66	:	(	255	,	0	,	255	),
            67	:	(	255	,	145	,	171	),
            68	:	(	185	,	0	,	80	),
            69	:	(	112	,	68	,	137	),
            70	:	(	0	,	120	,	120	),
            71	:	(	179	,	156	,	112	),
            72	:	(	255	,	255	,	128	),
            73	:	(	0	,	0	,	0	),
            74	:	(	182	,	112	,	92	),
            75	:	(	0	,	168	,	132	),
            76	:	(	235	,	214	,	176	),
            77	:	(	179	,	156	,	112	),
            78	:	(	0	,	0	,	0	),
            79	:	(	0	,	0	,	0	),
            80	:	(	0	,	0	,	0	),
            81	:	(	247	,	247	,	247	),
            82	:	(	156	,	156	,	156	),
            83	:	(	77	,	112	,	163	),
            84	:	(	0	,	0	,	0	),
            85	:	(	0	,	0	,	0	),
            86	:	(	0	,	0	,	0	),
            87	:	(	128	,	179	,	179	),
            88	:	(	233	,	255	,	190	),
            89	:	(	0	,	0	,	0	),
            90	:	(	0	,	0	,	0	),
            91	:	(	0	,	0	,	0	),
            92	:	(	0	,	255	,	255	),
            93	:	(	0	,	0	,	0	),
            94	:	(	0	,	0	,	0	),
            95	:	(	0	,	0	,	0	),
            96	:	(	0	,	0	,	0	),
            97	:	(	0	,	0	,	0	),
            98	:	(	0	,	0	,	0	),
            99	:	(	0	,	0	,	0	),
            100	:	(	0	,	0	,	0	),
            101	:	(	0	,	0	,	0	),
            102	:	(	0	,	0	,	0	),
            103	:	(	0	,	0	,	0	),
            104	:	(	0	,	0	,	0	),
            105	:	(	0	,	0	,	0	),
            106	:	(	0	,	0	,	0	),
            107	:	(	0	,	0	,	0	),
            108	:	(	0	,	0	,	0	),
            109	:	(	0	,	0	,	0	),
            110	:	(	0	,	0	,	0	),
            111	:	(	77	,	112	,	163	),
            112	:	(	212	,	227	,	252	),
            113	:	(	0	,	0	,	0	),
            114	:	(	0	,	0	,	0	),
            115	:	(	0	,	0	,	0	),
            116	:	(	0	,	0	,	0	),
            117	:	(	0	,	0	,	0	),
            118	:	(	0	,	0	,	0	),
            119	:	(	0	,	0	,	0	),
            120	:	(	0	,	0	,	0	),
            121	:	(	156	,	156	,	156	),
            122	:	(	156	,	156	,	156	),
            123	:	(	156	,	156	,	156	),
            124	:	(	156	,	156	,	156	),
            125	:	(	0	,	0	,	0	),
            126	:	(	0	,	0	,	0	),
            127	:	(	0	,	0	,	0	),
            128	:	(	0	,	0	,	0	),
            129	:	(	0	,	0	,	0	),
            130	:	(	0	,	0	,	0	),
            131	:	(	204	,	191	,	163	),
            132	:	(	0	,	0	,	0	),
            133	:	(	0	,	0	,	0	),
            134	:	(	0	,	0	,	0	),
            135	:	(	0	,	0	,	0	),
            136	:	(	0	,	0	,	0	),
            137	:	(	0	,	0	,	0	),
            138	:	(	0	,	0	,	0	),
            139	:	(	0	,	0	,	0	),
            140	:	(	0	,	0	,	0	),
            141	:	(	149	,	206	,	147	),
            142	:	(	149	,	206	,	147	),
            143	:	(	149	,	206	,	147	),
            144	:	(	0	,	0	,	0	),
            145	:	(	0	,	0	,	0	),
            146	:	(	0	,	0	,	0	),
            147	:	(	0	,	0	,	0	),
            148	:	(	0	,	0	,	0	),
            149	:	(	0	,	0	,	0	),
            150	:	(	0	,	0	,	0	),
            151	:	(	0	,	0	,	0	),
            152	:	(	199	,	215	,	158	),
            153	:	(	0	,	0	,	0	),
            154	:	(	0	,	0	,	0	),
            155	:	(	0	,	0	,	0	),
            156	:	(	0	,	0	,	0	),
            157	:	(	0	,	0	,	0	),
            158	:	(	0	,	0	,	0	),
            159	:	(	0	,	0	,	0	),
            160	:	(	0	,	0	,	0	),
            161	:	(	0	,	0	,	0	),
            162	:	(	0	,	0	,	0	),
            163	:	(	0	,	0	,	0	),
            164	:	(	0	,	0	,	0	),
            165	:	(	0	,	0	,	0	),
            166	:	(	0	,	0	,	0	),
            167	:	(	0	,	0	,	0	),
            168	:	(	0	,	0	,	0	),
            169	:	(	0	,	0	,	0	),
            170	:	(	0	,	0	,	0	),
            171	:	(	0	,	0	,	0	),
            172	:	(	0	,	0	,	0	),
            173	:	(	0	,	0	,	0	),
            174	:	(	0	,	0	,	0	),
            175	:	(	0	,	0	,	0	),
            176	:	(	233	,	255	,	190	),
            177	:	(	0	,	0	,	0	),
            178	:	(	0	,	0	,	0	),
            179	:	(	0	,	0	,	0	),
            180	:	(	0	,	0	,	0	),
            181	:	(	0	,	0	,	0	),
            182	:	(	0	,	0	,	0	),
            183	:	(	0	,	0	,	0	),
            184	:	(	0	,	0	,	0	),
            185	:	(	0	,	0	,	0	),
            186	:	(	0	,	0	,	0	),
            187	:	(	0	,	0	,	0	),
            188	:	(	0	,	0	,	0	),
            189	:	(	0	,	0	,	0	),
            190	:	(	128	,	179	,	179	),
            191	:	(	0	,	0	,	0	),
            192	:	(	0	,	0	,	0	),
            193	:	(	0	,	0	,	0	),
            194	:	(	0	,	0	,	0	),
            195	:	(	128	,	179	,	179	),
            196	:	(	0	,	0	,	0	),
            197	:	(	0	,	0	,	0	),
            198	:	(	0	,	0	,	0	),
            199	:	(	0	,	0	,	0	),
            200	:	(	0	,	0	,	0	),
            201	:	(	0	,	0	,	0	),
            202	:	(	0	,	0	,	0	),
            203	:	(	0	,	0	,	0	),
            204	:	(	0	,	255	,	140	),
            205	:	(	214	,	157	,	188	),
            206	:	(	255	,	102	,	102	),
            207	:	(	255	,	102	,	102	),
            208	:	(	255	,	102	,	102	),
            209	:	(	255	,	102	,	102	),
            210	:	(	255	,	145	,	171	),
            211	:	(	52	,	74	,	52	),
            212	:	(	230	,	117	,	37	),
            213	:	(	255	,	102	,	102	),
            214	:	(	255	,	102	,	102	),
            215	:	(	102	,	153	,	77	),
            216	:	(	255	,	102	,	102	),
            217	:	(	179	,	156	,	112	),
            218	:	(	255	,	145	,	171	),
            219	:	(	255	,	102	,	102	),
            220	:	(	255	,	145	,	171	),
            221	:	(	255	,	102	,	102	),
            222	:	(	255	,	102	,	102	),
            223	:	(	255	,	145	,	171	),
            224	:	(	0	,	175	,	77	),
            225	:	(	255	,	212	,	0	),
            226	:	(	255	,	212	,	0	),
            227	:	(	255	,	102	,	102	),
            228	:	(	255	,	212	,	0	),
            229	:	(	255	,	102	,	102	),
            230	:	(	138	,	100	,	83	),
            231	:	(	255	,	102	,	102	),
            232	:	(	255	,	38	,	38	),
            233	:	(	226	,	0	,	127	),
            234	:	(	255	,	158	,	15	),
            235	:	(	255	,	158	,	15	),
            236	:	(	168	,	112	,	0	),
            237	:	(	255	,	212	,	0	),
            238	:	(	168	,	112	,	0	),
            239	:	(	38	,	115	,	0	),
            240	:	(	38	,	115	,	0	),
            241	:	(	255	,	212	,	0	),
            242	:	(	0	,	0	,	153	),
            243	:	(	255	,	102	,	102	),
            244	:	(	255	,	102	,	102	),
            245	:	(	255	,	102	,	102	),
            246	:	(	255	,	102	,	102	),
            247	:	(	255	,	102	,	102	),
            248	:	(	255	,	102	,	102	),
            249	:	(	255	,	102	,	102	),
            250	:	(	255	,	102	,	102	),
            251	:	(	255	,	212	,	0	),
            252	:	(	38	,	115	,	0	),
            253	:	(	168	,	112	,	0	),
            254	:	(	38	,	115	,	0	),
            255	:	(	0	,	0	,	0	)
            }

# %%
# # Define a geometry to cover Conterminous U.S.
# CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
#                     .filter(ee.Filter.neq('NAME', 'United States Virgin Islands'))
#                     .filter(ee.Filter.neq('NAME', 'Puerto Rico'))
#                     .filter(ee.Filter.neq('NAME', 'Alaska'))
#                     .filter(ee.Filter.neq('NAME', 'Hawaii'))
#                     .filter(ee.Filter.neq('NAME', 'Guam'))
#                     .filter(ee.Filter.neq('NAME', 'Virgin Islands'))
#                     .filter(ee.Filter.neq('NAME', 'American Samoa'))
#                     .filter(ee.Filter.neq('NAME', 'Northern Mariana Islands'))
#                     .filter(ee.Filter.neq('NAME', 'Commonwealth of the Northern Mariana Islands'))).union().geometry()


# %%
# def mosaic_remap_collor_conver(startDate,endDate,month,L89cloudCover,S2cloudCover,CONUSBoundary,CONUStrainingLabel, L89tileFolder,S2tileFolder,local_root_folder,mosaicfolder_path):
#     def run_landsat():
#         # image title: month+"_L89mosaic_output.tif"
#         L89MosaicClassification(startDate, endDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path)

#     def run_sentinel():
#         # image title: month+"_S2mosaic_output.tif"
#         S2MosaicClassification(startDate, endDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path)

#     if __name__ == '__main__':
#         p1 = Process(target=run_landsat)
#         p2 = Process(target=run_sentinel)

#         p1.start()
#         p2.start()

#         p1.join()
#         p2.join()

#         print("Both L89 and S2 classification processes completed.")
#         try:
#           # output mosaiced image to folderPath+f'/{month}_L89_S2_merged.tif'
#           mosaic_L89_S2_gdal(mosaicfolder_path, month)
#           # Use shutil.rmtree() to delete the folder and its contents
#           # l89folder_path_to_delete = root_path + L89tileFolder
#           # s2folder_path_to_delete = root_path + S2tileFolder
#           # delete_folder(l89folder_path_to_delete)
#           # delete_folder(s2folder_path_to_delete)
#         except Exception as e:
#             print(f"Mosaicking failed: {e}")

#         # ========== CONFIGURATION ==========

#         mosaicedFilePath = mosaicfolder_path + f'/{month}_L89_S2_merged.tif'
#         outcolor_tif = mosaicfolder_path + f'/{month}_L89_S2_remapcolor.tif'
#         output_erdas_path = mosaicfolder_path + f'/{month}_L89_S2_erdas.img'

#         # ========== FUNCTIONS ==========

#         # Remap table
#         remap_dict = remap_values()

#         # Color table
#         color_table = color_table_Arc()

#         # ========== RUN ==========
#         try:
#             # output color image to folderPath+f'/{month}_L89_S2_remapcolor.tif'
#             remap_and_color_large_raster(mosaicedFilePath, outcolor_tif, remap_dict, color_table)
#         except Exception as e:
#             print(f"Post-processing failed: {e}")

#         try:
#             # output Erdas image to folderPath+f'/{month}_L89_S2_erdas.tif'
#             convert_tiff_to_erdas(outcolor_tif, output_erdas_path)
#         except Exception as e:
#             print(f"Post-processing failed: {e}")

# %%
import os
import glob
import time
from osgeo import gdal
import ee
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import shutil
import numpy as np
from multiprocessing import Process
import TrustedPixel
import RemapColorTool
import ErdasConvert

from AutomatedL89Mapping import L89MosaicClassification
from AutomatedS2Mapping import S2MosaicClassification

# Path to your downloaded JSON key
SERVICE_ACCOUNT = 'automatedmapping@ee-huil7073.iam.gserviceaccount.com'
KEY_FILE = 'ee-huil7073-81b7212a3bd2.json'

credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_FILE)
ee.Initialize(credentials)



year = 2025
startDate = str(year) + "-05-01"
endDate = str(year) + "-07-01"
month = "June"

S2cloudCover = 15
L89cloudCover = 20 
CONUStrainingLabel = TrustedPixel.trustedPixels(year,7)

root_path = '/content/drive/MyDrive/'
L89tileFolder = 'AutoInseasonL89_MappingTest'
S2tileFolder = 'AutoInseasonS2_MappingTest'
local_root_folder = '../DownloadClassifications'
mosaicfolder_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'
# folderPath = root_path + mosaicFolder # '/content/drive/MyDrive/' could be set to any root direction

CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
                    .filter(ee.Filter.eq('NAME', 'Nebraska'))).geometry()

# mosaic_remap_collor_conver(startDate,endDate,month,L89cloudCover,S2cloudCover,CONUSBoundary,CONUStrainingLabel, L89tileFolder,S2tileFolder,local_root_folder,mosaicfolder_path)
def run_landsat():
    # image title: month+"_L89mosaic_output.tif"
    L89MosaicClassification(startDate, endDate, month, S2cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path)

def run_sentinel():
    # image title: month+"_S2mosaic_output.tif"
    S2MosaicClassification(startDate, endDate, month, L89cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path)

if __name__ == '__main__':
    p1 = Process(target=run_landsat)
    p2 = Process(target=run_sentinel)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Both L89 and S2 classification processes completed.")
    try:
        # output mosaiced image to folderPath+f'/{month}_L89_S2_merged.tif'
        mosaic_L89_S2_gdal(mosaicfolder_path, month)
        # Use shutil.rmtree() to delete the folder and its contents
        # l89folder_path_to_delete = root_path + L89tileFolder
        # s2folder_path_to_delete = root_path + S2tileFolder
        # delete_folder(l89folder_path_to_delete)
        # delete_folder(s2folder_path_to_delete)
    except Exception as e:
        print(f"Mosaicking failed: {e}")

    # ========== CONFIGURATION ==========

    mosaicedFilePath = mosaicfolder_path + f'/{month}_L89_S2_merged.tif'
    outcolor_tif = mosaicfolder_path + f'/{month}_L89_S2_remapcolor.tif'
    output_erdas_path = mosaicfolder_path + f'/{month}_L89_S2_erdas.img'

    # ========== FUNCTIONS ==========

    # Remap table
    remap_dict = remap_values()

    # Color table
    color_table = color_table_Arc()
    
    # ========== RUN ==========
    try:
        # output color image to folderPath+f'/{month}_L89_S2_remapcolor.tif'
        RemapColorTool.remap_and_color_large_raster(mosaicedFilePath, outcolor_tif, remap_dict, color_table)
    except Exception as e:
        print(f"Post-processing failed: {e}")

    try:
        # output Erdas image to folderPath+f'/{month}_L89_S2_erdas.tif'
        ErdasConvert.convert_tiff_to_erdas(outcolor_tif, output_erdas_path)
    except Exception as e:
        print(f"Post-processing failed: {e}")

