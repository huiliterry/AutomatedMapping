import os
import time
import ee
import DownloadTool
import MosaicMultiImg
import RemapTable
from datetime import datetime

# single L89 tile time-series classification
def imgL89Classified(tile, startDate, cloudCover, CONUStrainingLabel):
  """
    Classify a single Landsat 8/9 tile time-series image using Random Forest.

    Parameters:
        tile (list or tuple): Landsat WRS tile coordinates [path, row].
        startDate (str): Start date for filtering images (YYYY-MM-DD).
        cloudCover (float): Maximum cloud cover percentage allowed.
        CONUStrainingLabel (ee.Image): Training label image for classification.

    Returns:
        ee.Dictionary: Dictionary containing:
            - 'image': Classified ee.Image or 'null' if classification not possible.
            - 'description': String describing the tile classification.
            - 'region': ee.Geometry of the tile or 'null'.
    """
  # single tile path and row number
  path = tile[0] 
  row = tile[1] 

  # define current data as enddate
  endDate = datetime.now().strftime('%Y-%m-%d')

  # image selection by startDate,endDate, path, row, and cloud cover
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

  # incorporate landsat 8 and landsat 9 into one collection sorted by time, and add NDVI and NDWI bands to each single image
  L89 = (ee.ImageCollection(L8.merge(L9)).sort('system:time_start')
                                        .map(lambda image: image.addBands(image.normalizedDifference(['SR_B5','SR_B4']).rename('NDVI'))
                                                                .addBands(image.normalizedDifference(['SR_B3','SR_B5']).rename('NDWI')))
                                        .select(bands))

  # convert time-series ImageCollection to single Image
  tileImage = L89.toBands()
  # extract tile geometry
  tileGeometry = tileImage.geometry()

  # define decription of this tile's classification
  output_description = str(path) + '_' + str(row) + '_' + endDate
  
  # return null image and description, if training sample is not availabel
  def imgNull():
    output_dictionary = ee.Dictionary({'image':'null', 'description':'null', 'region':'null'})
    return output_dictionary

  # classification processing
  def imgClassified():
    # clip label image from trusted pixel raster
    tileTrainingLabel = CONUStrainingLabel.clip(tileGeometry)
    # training samples generation by stratified sampling method
    trainingSample = tileImage.addBands(tileTrainingLabel).stratifiedSample(
      numPoints = 1000,
      classBand= 'cropland',
      region= tileGeometry,
      scale= 30 # matching to landsat spatial resolution
    )


    # the real time-series classification and post processing, if training sample is availabel
    def couldClassified():
      # time-series classification
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
      
      # remove noise by using majorty filter 
      majority_filtered = classified.focal_mode(
          radius=1, # radius in pixels (1 = 3x3 window)
          units='pixels',
          kernelType='square',
          iterations=1
      )

      # define a dictionary to stroe classified image and its matedata
      output_dictionary = ee.Dictionary({'image':majority_filtered, 'description':output_description, 'region':tileGeometry})
      return output_dictionary

    # conduct classification by judging the training sample's count
    return ee.Algorithms.If(trainingSample.size().neq(0).And(trainingSample.aggregate_count_distinct("cropland").neq(1)),couldClassified(),imgNull())

  # conduct classification and return result if the tileGeometry area is not 0
  return ee.Algorithms.If(ee.Number(tileGeometry.area(1)).neq(0),imgClassified(),imgNull())


# extract all L89 tile covering CONUS into a list
def L89List(CONUSBoundary):
  """
    Extract a list of unique Landsat 8/9 tile coordinates covering CONUS within a date range.

    Parameters:
        CONUSBoundary (ee.Geometry): Geometry polygon for CONUS boundary.

    Returns:
        list: List of unique [path, row] tile pairs.
    """
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


# conduct all classifications, exports, downloads, and mosaics
def L89MosaicClassification(startDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, tileFolder, local_root_folder, mosaicFolder,file_name):
  """
    Run classification on all Landsat 8/9 tiles covering CONUS, export results, download, and mosaic.

    Parameters:
        startDate (str): Start date for filtering images (YYYY-MM-DD).
        month (str): Month label for output file naming.
        cloudCover (float): Maximum cloud cover percentage allowed.
        CONUSBoundary (ee.Geometry): Geometry polygon for CONUS boundary.
        CONUStrainingLabel (ee.Image): Training label image for classification.
        tileFolder (str): Google Drive folder name for exporting images.
        local_root_folder (str): Local folder path to download images.
        mosaicFolder (str): Local folder path for mosaicking output.
        file_name (str): Output filename for mosaic image.

    Returns:
        None
    """
  # Filter the L89 harmonized collection by date and bounds.
  pathrowlist = L89List(CONUSBoundary)
  numList = len(pathrowlist)
  print('Number of L89 tiles:',numList)

  taskList = []
  remap_original = RemapTable.originalValueList()
  remap_target = RemapTable.resetValueList()
  
  # classification for each single tile
  for i in range(numList):#range(1):#
    tile = pathrowlist[i]
    print(i, tile)

    try:
        # This step usually does not trigger computation
        classified_dictionary = ee.Dictionary(imgL89Classified(tile, startDate, cloudCover, CONUStrainingLabel))
        
        # This line triggers a server-side computation (potential failure point)
        try:
            imgID = classified_dictionary.get('description').getInfo()
        except Exception as e:
            print(f"[SKIPPED] Failed to get imgID for tile {tile}: {e}")
            continue

        if imgID and imgID != 'null':
            try:
                # extract classified image, geometry region, and description
                classified = ee.Image(classified_dictionary.get('image')).remap(remap_original, remap_target)
                region = ee.Geometry(classified_dictionary.get('region'))
                description = month + '_' + imgID

                # export classification to Drive
                task = ee.batch.Export.image.toDrive(
                    image=classified,
                    description=description,
                    folder=tileFolder,
                    region=region,
                    scale=10,
                    crs='EPSG:5070',
                    maxPixels=1e12
                )
                task.start()
                taskList.append(task)
                print(f"Export task '{description}' started.")
            except Exception as e:
                print(f"[SKIPPED] Error setting up export for tile {tile}: {e}")
                continue
        else:
            print(f"[SKIPPED] imgID is null for tile {tile}")

    except Exception as e:
        print(f"[ERROR] Unexpected failure for tile {tile}: {e}")
        continue

  # waiting for uploading finish
  try:
    # Monitor tasks individually
    def wait_for_tasks(taskList):
      completed_tasks = set() 
      while len(completed_tasks) < len(taskList):
        for i, task in enumerate(taskList):
          if i in completed_tasks:
              continue
          status = task.status()
          task_name = status['description']
          state = status['state']
          if state in ['COMPLETED', 'FAILED', 'CANCELLED']:
            print(f"Task '{task_name}' finished with state: {state}")
            completed_tasks.add(i)
        # Avoid spamming Earth Engine with too many requests
        time.sleep(30)  

    # Call the monitoring function
    wait_for_tasks(taskList)
    print(f"Landsad 8/9 dataset classification done. Check Google Drive {tileFolder} folder.")
  except:
    print("Something wrong during classification task conducting")

  
  # download all classified images when finishing upload  
  try:
    # Wait for 30 seconds before downloading 
    time.sleep(30) 
    print("Ready to download")
    DownloadTool.downloadfiles_byserviceaccout(tileFolder, local_root_folder)
  except:
    print("Something wrong during classification downloading")


  # mosaic all classified images when finishing download
  try:
    # Wait for 30 seconds before mosaic 
    time.sleep(30) 
    print("Ready to mosaic multiple L89 classifications")
    sourceFolder = os.path.join(local_root_folder, tileFolder)
    MosaicMultiImg.mosaicoutputVRT(sourceFolder, mosaicFolder, file_name)
  except:
    print("Something wrong in multi-image mosaic")