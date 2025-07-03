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
# Function - S2 single classification

# %%
# single S2 tile classification
def imgS2Classified(tile, startDate, endDate, cloudCover, CONUStrainingLabel):
  # image selection
  bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'NDVI', 'NDWI']
  S2  = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                        .filter(ee.Filter.eq('MGRS_TILE', tile))
                        .filterDate(startDate, endDate)
                        .filter(ee.Filter.lt('NODATA_PIXEL_PERCENTAGE',10))
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',cloudCover))
                        .map(lambda image: image.addBands(image.normalizedDifference(['B8', 'B4']).rename('NDVI'))
                                                .addBands(image.normalizedDifference(['B3', 'B8']).rename('NDWI')))
                        .select(bands)
                        )

  # convert ImageCollection to single Image
  tileImage = S2.toBands()
  # extract tile geometry
  tileGeometry = tileImage.geometry()
  # display(tileGeometry)
  # bools = ee.Number(tileGeometry.area(1)).eq(0)
  # display(bools)

  output_description = str(tile) + '_' + endDate

  # classification processing
  def imgClassified():
    # clip label image from trusted pixel raster
    tileTrainingLabel = CONUStrainingLabel.clip(tileGeometry)
    # training samples generation by stratified sampling method
    trainingSample = tileImage.addBands(tileTrainingLabel).stratifiedSample(
      numPoints = 1800,
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
# Function - S2 state tile list

# %%
def stateS2List(CONUSBoundary):
  # Filter the S2 harmonized collection by date and bounds.
  S2_tilelist = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                              .filterDate("2025-05-01", "2025-05-15")
                              .filterBounds(CONUSBoundary)
                              .aggregate_array('MGRS_TILE')
                              .distinct()
                              .getInfo())
  return S2_tilelist

# %% [markdown]
# Function - S2 mosaic

# %%
def mosaicS2outputVRT(inputfolder_path,outputfolder_path,month):
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
    out_fp = os.path.join(outputfolder_path, month+"_S2mosaic.tif")

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
# Download all files in the folder

# %%
def list_all_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            spaces='drive',
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)

        if page_token is None:
            break

    return files


# create service account key in Google Cloud, download key .json, share downloadable folders to created service account
def downloadfiles_byserviceaccout(target_name, local_folder):
    # Load your service account key
    SERVICE_ACCOUNT_FILE = 'ee-huil7073-81b7212a3bd2.json'
    SCOPES = ['https://www.googleapis.com/auth/drive']

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    drive_service = build('drive', 'v3', credentials=creds)

    # List shared files
    results = drive_service.files().list(q=f"name = '{target_name}' and trashed = false", pageSize=10, fields="files(id, name)").execute()
    print('results',results.get('files'))

    # search and download each file in every folder
    for f in results['files']:
        folder_name = f['name']
        folder_id = f['id']
        print("folder_id",folder_id)
        
        # create local folder 
        local_file_path = os.path.join(local_folder, folder_name)
        os.makedirs(local_file_path, exist_ok=True)
        print('local_file_path',local_file_path)

        # Search for all files in this Drive folder
        filesList = list_all_files_in_folder(drive_service, folder_id)
        print('filesList',len(filesList))
        if len(filesList) == 0:
            break
        for i, file_obj in enumerate(filesList):
                file_title = file_obj['name']
                file_id = file_obj['id']
                print(f"{i+1}. {file_title} ({file_id})")
                local_file_name = os.path.join(local_file_path, file_title)

                request = drive_service.files().get_media(fileId=file_id)
                fh = io.FileIO(local_file_name, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {int(status.progress() * 100)}%.")

        print(f"All files downloaded to: {local_file_path}")

# %% [markdown]
# Function - S2 mosaic mapping

# %%
def S2MosaicClassification(startDate, endDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, tileFolder, local_root_folder, mosaicFolder):
  """""
  # Filter the S2 harmonized collection by date and bounds.
  S2_tilelist = stateS2List(CONUSBoundary)
  numList = len(S2_tilelist)
  print('Number of S2 tiles:',numList)

  taskList = []

  # classification for each single tile
  # for i in range(935,numList):
  for i in range(0,1):
    tile = S2_tilelist[i]
    print(i, tile)
    classified_dictionary = ee.Dictionary(imgS2Classified(tile, startDate, endDate, cloudCover, CONUStrainingLabel))
    # display(classified_dictionary)
    imgID =classified_dictionary.get('description').getInfo()
    # print('ifnull',ifnull)
    if imgID != 'null':
      classified =ee.Image(classified_dictionary.get('image'))
      refion = ee.Geometry(classified_dictionary.get('region'))
      description = month+'_'+classified_dictionary.get('description').getInfo()

      task = ee.batch.Export.image.toDrive(
          image = classified,
          description = description,
          folder = tileFolder,
          region = refion, # Ensure region is a list of coordinates
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
  downloadfiles_byserviceaccout(tileFolder, local_root_folder)

  # mosaic all classified images when finishing download
  # time.sleep(30) # Wait for 30 seconds before checking again
  print("Ready to mosaic")
  sourceFolder = os.path.join(local_root_folder, tileFolder)
  mosaicS2outputVRT(sourceFolder, mosaicFolder, month)

# %% [markdown]
# Application - S2 mapping

# %%
# Define a geometry to cover Conterminous U.S.
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
# S2tileFolder = 'AutoInseasonS2_MappingTest'
# local_root_folder = '../DownloadClassifications'
# mosaicfolder_path = '../DownloadClassifications/AutoInseasonL89S2_Mosaic'

# S2MosaicClassification(startDate, endDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, S2tileFolder, local_root_folder, mosaicfolder_path)


