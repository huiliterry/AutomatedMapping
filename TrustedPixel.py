import ee


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