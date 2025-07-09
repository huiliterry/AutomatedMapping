# %% [markdown]
import os
import glob
import time
from osgeo import gdal
import ee
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import DownloadTool
import MosaicMultiImg
import RemapTable_singleImage

# Trusted Pixels

# %%
# Trusted pixels extraction
def trustedPixels(year,gap):

  def getCDLbyYear(year):
      return ee.Image('USDA/NASS/CDL/'+year).select('cropland')

  gap = gap - 1
  # year = 2025
  oneYearList = list(range(year-gap,year))
  # print(oneYearList)
  twoYearList = oneYearList[0:gap:2]
  # print(twoYearList)

  oneYearListCdl = ee.ImageCollection(list(map(getCDLbyYear, list(map(str, oneYearList)))))
  twoYearListCdl = ee.ImageCollection(list(map(getCDLbyYear, list(map(str, twoYearList)))))
  # display(oneYearListCdl,twoYearListCdl)

  # Calculate the standard deviation across the ImageCollection to find constant pixels.
  # Create a mask where the standard deviation is zero (constant pixels).
  oneYearconstant_mask = oneYearListCdl.reduce(ee.Reducer.stdDev()).eq(0)
  twoYearconstant_mask = twoYearListCdl.reduce(ee.Reducer.stdDev()).eq(0)

  oneYearTrusted = twoYearListCdl.first().updateMask(oneYearconstant_mask)
  twoYearTrusted = twoYearListCdl.first().updateMask(twoYearconstant_mask)
  # display(oneYearTrusted,twoYearTrusted)

  # Merge the two trusted images
  UStrustedpixel = ee.ImageCollection([oneYearTrusted, twoYearTrusted]).mosaic()

  return UStrustedpixel

# %% [markdown]
# Function - L89 single classification

# %%
# single L89 tile classification
def imgL89Classified(tile, startDate, endDate, cloudCover, CONUStrainingLabel):
  # single tile path and row number
  # L89_single = ee.List(tile)
  path = tile[0] #L89_single.get(0)
  row = tile[1] #L89_single.get(1)

  # image selection
  bands = ['SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B6', 'SR_B7', 'NDVI', 'NDWI']
  L8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                  .filterDate(startDate,endDate)
                  .filter(ee.Filter.eq('WRS_PATH',path))
                  .filter(ee.Filter.eq('WRS_ROW',row))
                  .filter(ee.Filter.lt('CLOUD_COVER_LAND',cloudCover)))

  L9 = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                  .filterDate(startDate,endDate)
                  .filter(ee.Filter.eq('WRS_PATH',path))
                  .filter(ee.Filter.eq('WRS_ROW',row))
                  .filter(ee.Filter.lt('CLOUD_COVER_LAND',cloudCover)))

  L89 = (ee.ImageCollection(L8.merge(L9)).sort('system:time_start')
                                        .map(lambda image: image.addBands(image.normalizedDifference(['SR_B5','SR_B4']).rename('NDVI'))
                                                                .addBands(image.normalizedDifference(['SR_B3','SR_B5']).rename('NDWI')))
                                        .select(bands))

  # convert ImageCollection to single Image
  tileImage = L89.toBands()
  # extract tile geometry
  tileGeometry = tileImage.geometry()
  # display(tileGeometry)
  # bools = ee.Number(tileGeometry.area(1)).eq(0)
  # display(bools)

  output_description = str(path) + '_' + str(row) + '_' + endDate

  # classification processing
  def imgClassified():
    # clip label image from trusted pixel raster
    tileTrainingLabel = CONUStrainingLabel.clip(tileGeometry)
    # training samples generation by stratified sampling method
    trainingSample = tileImage.addBands(tileTrainingLabel).stratifiedSample(
      numPoints = 2000,
      classBand= 'cropland',
      region= tileGeometry,
      scale= 10
    )

    def couldClassified():
      classified = (tileImage.classify(ee.Classifier.smileRandomForest(20).train(
                                      features= trainingSample,
                                      classProperty= 'cropland',
                                      inputProperties= tileImage.bandNames()
                                    )
                            )
                      .clip(tileGeometry)
                      .set('type','classification')
                      .toUint8()
              )
      majority_filtered = classified.focal_mode(
          radius=1, # radius in pixels (1 = 3x3 window)
          units='pixels',
          kernelType='square',
          iterations=1
      )
      output_dictionary = ee.Dictionary({'image':majority_filtered, 'description':output_description, 'region':tileGeometry})
      return output_dictionary

    def couldNotClassified():
      # nullImg = ee.Image(0).clip(tileGeometry).set('type','null')
      output_dictionary = ee.Dictionary({'image':'null', 'description':'null', 'region':'null'})
      return output_dictionary


    return ee.Algorithms.If(trainingSample.size().neq(0).And(trainingSample.aggregate_count_distinct("cropland").neq(1)),couldClassified(),couldNotClassified())

  # alternative null image process
  def imgNull():
    # nullImg = ee.Image(0).set('type','null') #.clip(tileGeometry)
    output_dictionary = ee.Dictionary({'image':'null', 'description':'null', 'region':'null'})
    return output_dictionary

  # output classified crop map

  return ee.Algorithms.If(ee.Number(tileGeometry.area(1)).neq(0),imgClassified(),imgNull())


# %% [markdown]
# Function - L89 tile list

# %%
def L89List(CONUSBoundary):
  # Filter the L89 harmonized collection by date and bounds.
  L8 = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                    .filterDate("2025-05-01","2025-05-20")
                    .filterBounds(CONUSBoundary))
  L9 = (ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
                  .filterDate("2025-05-01","2025-05-20")
                  .filterBounds(CONUSBoundary))

  L89 = ee.ImageCollection(L8.merge(L9))

  pathString = ee.Array(L89.aggregate_array('WRS_PATH'))
  rowString = ee.Array(L89.aggregate_array('WRS_ROW'))
  L89_pathrowlist = ee.Array.cat([pathString, rowString], 1).toList().distinct().getInfo()
  return L89_pathrowlist

# %% [markdown]
# Function - L89 mosaic

# %%
def mosaicL89outputVRT(inputfolder_path,outputfolder_path,month,file_name):
    # Build full folder path
    # inputfolder_path = os.path.join('/content/drive/MyDrive', inputfolder)
    # print(f"Input folder path: {inputfolder_path}")
    # Find all .tif files in the folder
    tif_files = glob.glob(os.path.join(inputfolder_path, '*.tif'))
    print(f"Found {len(tif_files)} files for mosaicking.")

    if not tif_files:
        print("No .tif files found.")
        return

    # Create temporary VRT (Virtual Raster Tile)
    vrt_path = os.path.join(inputfolder_path, "temp_mosaic.vrt")
    vrt_options = gdal.BuildVRTOptions(srcNodata=0, VRTNodata=0)
    vrt = gdal.BuildVRT(vrt_path, tif_files, options=vrt_options)
    if vrt is None:
        print("VRT build failed.")
        return
    vrt = None  # Close the VRT handle

    # Define output mosaic path
    # outputfolder_path = os.path.join('/content/drive/MyDrive', outputfolder)
    os.makedirs(outputfolder_path, exist_ok=True)
    out_fp = os.path.join(outputfolder_path, month+file_name)

    # Translate VRT to compressed GeoTIFF using tiling and LZW compression
    translate_options = gdal.TranslateOptions(
        format='GTiff',
        creationOptions=[
            'TILED=YES',
            'COMPRESS=LZW',
            'BIGTIFF=YES',  # Use for large outputs
            'NUM_THREADS=ALL_CPUS'
        ]
    )
    gdal.Translate(out_fp, vrt_path, options=translate_options)
    print(f"Mosaic written to: {out_fp}")

    # Optional: remove temporary VRT
    os.remove(vrt_path)

# %% [markdown]
# Function - L89 mosaic mapping

# %%
def L89MosaicClassification(startDate, endDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, tileFolder, local_root_folder, mosaicFolder,file_name):
  """""
  # Filter the L89 harmonized collection by date and bounds.
  pathrowlist = L89List(CONUSBoundary)
  numList = len(pathrowlist)
  print('Number of L89 tiles:',numList)

  taskList = []
  remap_original = RemapTable_singleImage.orginal_value()
  remap_target = RemapTable_singleImage.target_value()

  # classification for each single tile
#   for i in range(numList):
  for i in range(0,1):
    tile = pathrowlist[i]
    print(i, tile)
    classified_dictionary = ee.Dictionary(imgL89Classified(tile, startDate, endDate, cloudCover, CONUStrainingLabel))
    # display(classified_dictionary)
    imgID =classified_dictionary.get('description').getInfo()
    print('imgID',imgID)
    if imgID != 'null':
      # classified image was remapped as new pixel values and clipped by CONUS boundary
      classified =ee.Image(classified_dictionary.get('image')).remap(remap_original,remap_target).clip(CONUSBoundary)
      g = ee.Geometry(classified_dictionary.get('region'))
      description = month + '_' + classified_dictionary.get('description').getInfo()

      task = ee.batch.Export.image.toDrive(
          image = classified,
          description = description,
          folder = tileFolder,
          region = region, # Ensure region is a list of coordinates
          scale = 10, # Resolution of your output image
          crs = 'EPSG:5070', # Coordinate Reference System
          maxPixels = 1e12 # Increase if you encounter "Too many pixels" error
      )
      task.start()
      taskList.append(task)
      print(f"Export task '{classified_dictionary.get('description').getInfo()}' started. Check Google Drive {tileFolder} folder.")

  # Function to monitor task completion
  def wait_for_tasks(tasks):
      print("Waiting for all export tasks to complete...")
      while True:
          statuses = [task.status()['state'] for task in tasks]
          print(statuses)  # Optional: track task progress
          if all(state in ['COMPLETED', 'FAILED', 'CANCELLED'] for state in statuses):
              break
          time.sleep(30)  # Wait 30 seconds before checking again

  # Call the monitoring function
  wait_for_tasks(taskList)
"""
  # download all classified images when finishing upload  
  # time.sleep(30) # Wait for 30 seconds before checking again
  DownloadTool.downloadfiles_byserviceaccout(tileFolder, local_root_folder)

  # mosaic all classified images when finishing download
  # time.sleep(30) # Wait for 30 seconds before checking again
  print("Ready to mosaic")
  sourceFolder = os.path.join(local_root_folder, tileFolder)
  MosaicMultiImg.mosaicoutputVRT(sourceFolder, mosaicFolder, file_name)

# %% [markdown]
# Application - L89 mapping

# %%
# import os
# import glob
# import time
# from osgeo import gdal
# import ee
# import io
# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseDownload

# # Path to your downloaded JSON key
# SERVICE_ACCOUNT = 'automatedmapping@ee-huil7073.iam.gserviceaccount.com'
# KEY_FILE = 'ee-huil7073-81b7212a3bd2.json'

# credentials = ee.ServiceAccountCredentials(SERVICE_ACCOUNT, KEY_FILE)
# ee.Initialize(credentials)

# CONUSBoundary = (ee.FeatureCollection("TIGER/2018/States")
#                     .filter(ee.Filter.eq('NAME', 'Nebraska'))).geometry()

# CONUStrainingLabel = trustedPixels(2025,7)

# startDate = "2025-05-01"
# endDate = "2025-07-01"
# month = "June"
# cloudCover = 20


# # root_path = '/content/drive/MyDrive/'
# L89tileFolder = 'AutoInseasonL89_MappingTest'
# S2tileFolder = 'AutoInseasonS2_MappingTest'
# local_root_folder = '../DownloadClassifications'
# mosaicfolder_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'

# L89MosaicClassification(startDate, endDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, L89tileFolder, local_root_folder, mosaicfolder_path)


