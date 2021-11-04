# Dataset Creation

The original dataset for this challenge contains images centered on latitude/longitude coordinates corresponding to empirically validated field sites for known blue carbon ecosystems curated from the literature and documented in [this dataset](https://nicholasinstitute.duke.edu/focal-areas/coastal-blue-carbon/blue-carbon-data-set). Train, validation, and test sets were chosen such that geographical regions in the validation and test sets are not represented in the training set. Images are 8-day true color RGB images from Jan 1-8, April 1-8, July 1-8, and Oct 1-8 for years 2020, 2019, and 2018, less those images with too much cloud cover (removed through manual inspection and retained in the folder called 'clouds' in the corresponding folder). Image dimensions are 224x224x3. Images are downloaded from the [ORNL MODIS subsetting API](https://modis.ornl.gov/data/modis_webservice.html).

## ORNL MODIS subsetting API GetMODISImages

A big credit to Andrew Michaelis who helped me with the ORNL API, scripts here adapted from his [repo](https://github.com/HyperplaneOrg/ornl-modis-site-imgs). 
This is a simple script that will build a library of modis
based images using Aqua Satellite product [MYD09A1](https://lpdaac.usgs.gov/products/myd09a1v006/) for a set of target sites via
ORNL’s modis subsetting api. Basic QC filtering is done and a gamma correction
is applied to the images for better viewing.

See the sites.csv example for defining site targets. The headers etc need to match this format.

To add the python dependencies, a simple pip install can often work fine, e.g.:

```
$ pip3 install pandas requests Pillow scikit-image --user
```


Then run:

```
$ ./build_mod_imgs_rgbonly.py
```

Note, sites.csv must be in the working directory (see script) and outputs are
placed in ./site-imgs/\<site_tag\>/\<prod\>_\<latitude\>_\<longitude\>_A\<date\>_rgb.png

------

## Coastline image dataset

Coastline data was downloaded from NOAA GSHHG (https://www.ngdc.noaa.gov/mgg/shorelines/gshhs.html):

```
wget https://www.ngdc.noaa.gov/mgg/shorelines/data/gshhg/latest/gshhg-shp-2.3.7.zip
```

lat/lon coordinates were extracted from the shp file (see GetCoastlineCoordinates.ipynb), saved in coastal_boundaries_cruderes.csv, and images were downloaded with the ORNL API as for the labeled dataset above. Other resolutions are available - low, intermediate, high, full.


# Pretrained model resources

There are a number of pretrained models trained on remote sensing data, see [here](https://tfhub.dev/google/collections/remote_sensing/1).

# Other resources

A description of the MODIS [bands](https://modis.gsfc.nasa.gov/about/specifications.php) and [products](https://lpdaac.usgs.gov/product_search/?collections=Combined+MODIS&collections=Aqua+MODIS&view=list ).

There is a [MODIS cloud mask product](https://modis.gsfc.nasa.gov/data/dataprod/mod35.php) that perhaps we can use to automate cloud cover QC
