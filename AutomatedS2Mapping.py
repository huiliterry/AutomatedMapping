import os
import time
import ee
import DownloadTool
import MosaicMultiImg
import RemapTable
from datetime import datetime


# single S2 tile classification
def imgS2Classified(tile, startDate, cloudCover, CONUStrainingLabel):
  # image selection
  endDate = datetime.now().strftime('%Y-%m-%d')
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
      numPoints = 1500,
      classBand= 'cropland',
      region= tileGeometry,
      scale= 10
    )

    def couldClassified():
      classified = (tileImage.classify(ee.Classifier.smileRandomForest(30).train(
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

# Function - S2 tile list
def stateS2List(CONUSBoundary):
  # Filter the S2 harmonized collection by date and bounds.
  S2_tilelist = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                              .filterDate("2025-05-01", "2025-05-15")
                              .filterBounds(CONUSBoundary)
                              .aggregate_array('MGRS_TILE')
                              .distinct()
                              .getInfo())
  return S2_tilelist

# Function - S2 mosaic classification
def S2MosaicClassification(startDate, month, cloudCover, CONUSBoundary, CONUStrainingLabel, tileFolder, local_root_folder, mosaicFolder,file_name):
  
  # Filter the S2 harmonized collection by date and bounds.
  S2_tilelist = stateS2List(CONUSBoundary)
  numList = len(S2_tilelist)
  print('Number of S2 tiles:',numList)

  taskList = []
  remap_original = RemapTable.originalValueList()
  remap_target = RemapTable.resetValueList()

  # classification for each single tile
  for i in range(numList):#range(1):#
    tile = S2_tilelist[i]
    print(i, tile)

    try:
        # This step usually does not trigger computation; it's lazy
        classified_dictionary = ee.Dictionary(imgS2Classified(tile, startDate, cloudCover, CONUStrainingLabel))
        
        # This line triggers a server-side computation (potential failure point)
        try:
            imgID = classified_dictionary.get('description').getInfo()
        except Exception as e:
            print(f"[SKIPPED] Failed to get imgID for tile {tile}: {e}")
            continue

        if imgID and imgID != 'null':
            try:
                classified = ee.Image(classified_dictionary.get('image')).remap(remap_original, remap_target)
                region = ee.Geometry(classified_dictionary.get('region'))
                description = month + '_' + imgID

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
            print(f"Task '{task_name}' finished with state: {state}.")
            completed_tasks.add(i)
        time.sleep(30)  # Avoid spamming Earth Engine with too many requests

    # Call the monitoring function
    wait_for_tasks(taskList)
    print(f"Sentinel-2 dataset classification done. Check Google Drive {tileFolder} folder.")
  except:
    print("Something wrong during classification task conducting")

  
  # download all classified images when finishing upload  
  try:
    time.sleep(30) # Wait for 30 seconds before checking again
    print("Ready to download")
    DownloadTool.downloadfiles_byserviceaccout(tileFolder, local_root_folder)
  except:
    print("Something wrong during classification downloading")


  # mosaic all classified images when finishing download
  try:
    time.sleep(30) # Wait for 30 seconds before checking again
    print("Ready to mosaic multiple S2 classifications")
    sourceFolder = os.path.join(local_root_folder, tileFolder)
    MosaicMultiImg.mosaicoutputVRT(sourceFolder, mosaicFolder, file_name)
  except:
    print("Something wrong in multi-image mosaic")
