#!/usr/bin/env python3

# See the README.md file

import json
import logging
import sys
import os
from datetime import datetime
import numpy
from PIL import Image
import pandas as pd
import requests
from skimage import exposure

# The site file, of the format: site_tag,latitude,longitude,start_date,end_date,kmAboveBelow,kmLeftRight
CSV = "sites.csv"

URL = "https://modis.ornl.gov/rst/api/v1/"
ORDURL = "https://modis.ornl.gov/subsetdata"
HEADER = {'Accept': 'application/json'}

BANDS = ['sur_refl_b01', 'sur_refl_b04', 'sur_refl_b03', 'sur_refl_qc_500m']
PROD = ['MYD09A1', 'MOD09A1']
# MXD09A1 QC, this runs parallel to BANDS, defs at https://lpdaac.usgs.gov/documents/925/MOD09_User_Guide_V61.pdf
BANDS_QC = [
    60,      # 111100, band 1
    245760,  # 111100000000000000, band 4
    15360    # 11110000000000, band 3
]
SR_MAX = 16000
SR_MIN = -100
GAMMA = 0.4
IMG_DIR= 'site-imgs'

def json_sr_2_channel(band_name, band_idx, data, qc_band):
    nsubs = len(data[band_name]['subset'])
    if nsubs > 1:
        logging.warning("using the first subset for %s ...", band_name)
    scale = float(data[band_name]['scale'])
    arr = numpy.array(data[band_name]['subset'][0]['data']).astype('f4')
    arr = numpy.ma.masked_where(arr > SR_MAX, arr, copy=False)
    arr = numpy.ma.masked_where(arr < SR_MIN, arr, copy=False)
    arr *= scale
    sr_min, sr_max = SR_MIN * scale, SR_MAX * scale
    dat = ((arr - sr_min) * (1/(sr_max - sr_min) * 255)).astype('uint8')
    qc_bnd = qc_band & BANDS_QC[band_idx]
    dat = numpy.ma.masked_where(qc_bnd != 0, dat, copy=False)
    return dat
#json_sr_2_channel

def post_m09a1(data):
    logging.info("Building rgb image for MODIS Terra/Aqua Surface Reflectance (SREF) 8-Day L3 Global 500 %s", data['name'])
    qc = numpy.array(data['sur_refl_qc_500m']['subset'][0]['data'], dtype='u4')
    redish = json_sr_2_channel('sur_refl_b01', 0, data, qc)
    greenish = json_sr_2_channel('sur_refl_b04', 1, data, qc)
    blueish = json_sr_2_channel('sur_refl_b03', 2, data, qc)
    msk = redish.mask | greenish.mask | blueish.mask
    alpha = numpy.where(msk == True, 0, 255).astype('uint8')
    shp = data['sur_refl_b01']['nrows'], data['sur_refl_b01']['ncols'], 4
    try:
        rgba = numpy.dstack((redish, greenish, blueish, alpha)).reshape(shp)
        gcorrect = exposure.adjust_gamma(rgba, GAMMA)
        img = Image.fromarray(gcorrect,'RGBA') #changed this to RGB to be 3-channel and it borked everything
        img = img.resize((224, 224)) #resize to 224x224 needed (closest can get with integer bounds is 225x225)
        img.save(data['name'])
    except ValueError as valerr:
        logging.error("%s for %s, image not created", str(valerr), data['name'])
#post_m09a1

def subset_site_data(csv, prod):
    coordinates = pd.read_csv(csv)
    logging.debug(coordinates)

    # Convert start_date and end_date columns to datetimes
    coordinates['start_date'] =  pd.to_datetime(coordinates['start_date'])
    coordinates['end_date'] =  pd.to_datetime(coordinates['end_date'])

    # Make new columns for MODIS start and end dates
    coordinates['start_MODIS_date'] = ''
    coordinates['end_MODIS_date'] = ''
    time_idx = {}

    for index, row in coordinates.iterrows():
        url = URL + prod + '/dates?latitude=' + str(row['latitude']) + '&longitude='+ str(row['longitude'])
        #logging.debug(url)
        response = requests.get(url, headers=HEADER)
        # Get dates object as list of python dictionaries
        dates = json.loads(response.text)['dates']
        # Convert to list of tuples; change calendar_date key values to datetimes
        dates = [(datetime.strptime(date['calendar_date'], "%Y-%m-%d"), date['modis_date']) for date in dates]
        # Get MODIS dates nearest to start_date and end_date and add to new pandas columns
        coordinates.loc[index, 'start_MODIS_date'] = min(date[1] for date in dates if date[0] >= row['start_date'])
        coordinates.loc[index, 'end_MODIS_date'] = max(date[1] for date in dates if date[0] <= row['end_date'])
        time_idx[row['site_tag']] = [date[1] for date in dates if date[0] <= row['end_date'] and date[0] >= row['start_date']]
    #done
    #logging.debug(coordinates)

    for index, row in coordinates.iterrows():
        fdir = os.path.join(IMG_DIR, row['site_tag'])
        if not os.path.exists(fdir):
            os.makedirs(fdir)
        for doi in time_idx[row['site_tag']]:
            data_obj = {}
            data_obj['name'] = os.path.join(fdir, prod+'_'+str(row['latitude'])+'_'+str(row['longitude'])+'_'+doi+'_rgba.png')
            for band in BANDS:
                url = URL + prod + "/subset?latitude=" + str(row['latitude']) + "&longitude=" + str(row['longitude']) + \
                       "&startDate=" + doi + "&endDate=" + doi + "&kmAboveBelow=" + str(row['kmAboveBelow']) + \
                       "&kmLeftRight=" + str(row['kmLeftRight']) + "&band="+band

                #logging.debug(url)
                response = requests.get(url, headers=HEADER)
                if response.status_code != 200:
                    logging.error("Request failed %s", str(response.text))
                    continue
                else:
                    subset = json.loads(response.text)
                    data_obj[band] = subset
            #done
            post_m09a1(data_obj)
        #done
    #done
    logging.debug("done writing subsets ...")
#subset_site_data

if __name__ == '__main__':
    LOGFILE = None # Add a path to log to file...
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
    try:
        for PRD in PROD:
            subset_site_data(CSV, PRD)
    except KeyboardInterrupt as kbex:
        logging.warning("aborted by user...")
        sys.exit(1)
