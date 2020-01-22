#!/usr/bin/env python3

import os
import sys
import argparse
import pprint
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests
import shutil

TMPDIR = '/var/tmp'

archive_url = 'http://c1.hpwren.ucsd.edu/archive/'


mirrorDir = ""

file_permisson = 0o664
directory_permission = 0o775


# TODO: previous years are in a subfolder and this function does not get them yet
def getFolders(archiveURL, folder, subFolder):

    url = archiveURL + folder

    print("processing page {}".format(url))    
    html = urlopen(url).read().decode('utf-8')


    soup = BeautifulSoup(html, 'html.parser')

    folders = []
    links_html = soup.find_all('a')
    #print(years_html)
    for elem in links_html:
        folder_str = elem.get_text().rstrip()
        if folder_str[-1] != '/':
            #print("skipping non-folder: ", folder_str)
            continue


        if len(folder_str) == 5 :
            # seem to be empty, skipping for now
            continue
            subdirectory = url + folder_str
            subdirectory_folders = getFolders(subdirectory, folder_str)

            print("got subfolders:", len(subdirectory_folders))

            folders = folders + subdirectory_folders
            continue
        if len(folder_str) == 9:
            #print(folder)
            folder = {}
            folder["year"] = folder_str[0:4]
            folder["month"] = folder_str[4:6]
            folder["day"] = folder_str[6:8]
            if subFolder == "":
                folder["path"] = folder_str
            else:
                folder["path"] = subFolder+folder_str
            folders.append(folder)


    return folders

# returns list of files
# expected_timestamp_date is only a verfication mechanism
def getQFolderContent(baseURL, subfolder, expected_timestamp_date):

    qFolderURL = baseURL + subfolder
    print("processing page {}".format(qFolderURL))    
    html = urlopen(qFolderURL).read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    # sine we need the timestamps nect to the filesname, we have to
    # seach for table colums instead of simple links

    files = []

    table_row = soup.find_all('tr')
    # example result : ['', '1576224042.jpg', '2019-12-13 00:00  ', '597K', '\xa0']

    timestamp_hash = {} 

    for elem in table_row:
        td_cells = elem.find_all('td')
        row = [i.text for i in td_cells]
        if len(row) < 3:
             #print(row)
            continue
        #print(row)

        filename = row[1].strip()
        timestamp = row[2].strip()

        if filename == "Parent Directory":
            continue

        if filename == "" or timestamp == "":
            print("filename: ",filename)
            print("timestamp: ",timestamp)
            sys.exit(1)

        if not filename.endswith(".jpg"): # TODO may want to add other formats ?
            continue


        
        #print(timestamp)
        if timestamp in timestamp_hash:
            print("timestamp duplicate: ",timestamp)
            sys.exit(1)


        timestamp_array = timestamp.split(" ")
        date = timestamp_array[0]
        
        date_array = date.split('-')
        if len(date_array) != 3:
            print("Cannot parse date: ", date, date_array, len(date_array))
            sys.exit(1)


        year = int(date_array[0])
        month = int(date_array[1])
        day = int(date_array[2])
        
        time = timestamp_array[1]

        # verifiy date
        if expected_timestamp_date != date:
            print("WARNING: expected date and timestamp date do not match ({} vs {})".format(expected_timestamp_date, date))
            continue
       
        time_array = time.split(':')
        hour = int(time_array[0])
        if hour < 0 or hour > 23:
            print("error parsing timestamp:", timestamp_array)
            sys.exit(1)
        minute = int(time_array[1])
        if minute < 0 or minute > 59:
            print("error parsing timestamp:", timestamp_array)
            sys.exit(1)

        
        dayPicture = {}
        dayPicture['path'] = subfolder
        dayPicture['filename'] = filename
        dayPicture['year'] = year
        dayPicture['month'] = month
        dayPicture['day'] = day
        dayPicture['hour'] = hour
        dayPicture['minute'] = minute


        files.append(dayPicture)
        #file_str = elem.get_text().rstrip()
        #print(file_str)
    return files

# Listing of all pictures of that day
#  returns: array of objects:
#  fields: path, filename, timestamp
#  example:  {'path': 'Q8/', 'filename': '1576309962.jpg', 'timestamp': '2019-12-13 23:52'}
def getDayPictures(baseURL, pathURL, dayfolder, expected_timestamp_date):

    print("baseURL: ", baseURL)
    print("pathURL: ", pathURL)
    url = baseURL + pathURL
    print("url: ", url)


    print("dayfolder: ", dayfolder)
   
    #sys.exit(1)
    qListingURL =  url + dayfolder['path']
    print("qListingURL: ", qListingURL)

    print("processing page {}".format(qListingURL))    
    html = urlopen(qListingURL).read().decode('utf-8')

    soup = BeautifulSoup(html, 'html.parser')

    dayPictures = []

    links_html = soup.find_all('a')
    for elem in links_html:
        folder_str = elem.get_text().rstrip()
        if len(folder_str) != 3:
            continue
        if folder_str[0] != "Q":
            continue

        print("processing q-folder: ",folder_str)
        
        #qFolderURL = qListingURL + folder_str
        #subfolder = folder_str

        #baseURL + pathURLm +  dayfolder['path'] + folder_str
        subfolder = pathURL +  dayfolder['path'] + folder_str

        #print("subfolder: ", subfolder)
        #sys.exit(1)
        qPictures = getQFolderContent(baseURL, subfolder, expected_timestamp_date)
        if len(qPictures) == 0:
            print("qPictures empty ", subfolder)
            #sys.exit(1) 
            continue

        #print("qFiles: ",  qFiles)
        for qPicture in qPictures:
            dayPictures.append(qPicture)

    if len(dayPictures) == 0:
        print("dayPictures empty ({} {})".format( url, dayfolder ))
        

    return dayPictures




# picture_type: c : color , m: monochrome
def download(site, camera, picture_type):

    


    # exmaple: http://c1.hpwren.ucsd.edu/archive/69bravo-n-mobo-c/large/
    folder = '{}-{}-mobo-{}/large/'.format(site, camera, picture_type) 

    #day_listing_url = '{}{}'.format(archive_url, folder)
    #print("day_listing_url: ", day_listing_url)


    # get list of days with data available 
    dayFolders = getFolders(archive_url, folder, "")
    print("dayFolders: ", dayFolders)

    #example: http://c1.hpwren.ucsd.edu/archive/69bravo-n-mobo-c/large/20191213/

    # Q folders are 3 hour windows:
    #Q1: 0000-0259 	Q2: 0300-0559 	Q3: 0600-0859 	Q4: 0900-1159
    #Q5: 1200-1459 	Q6: 1500-1759 	Q7: 1800-2059 	Q8: 2100-2359

    # this path does not include date/time subfolders

    siteDir = os.path.join(mirrorDir, site)
    if not os.path.isdir(siteDir):
        os.mkdir(siteDir)
        os.chmod(siteDir, directory_permission)

    cameraDir = os.path.join(siteDir, camera)
    if not os.path.isdir(cameraDir):
        os.mkdir(cameraDir)
        os.chmod(cameraDir, directory_permission)

    targetPathBase = os.path.join(cameraDir, picture_type)
    if not os.path.isdir(targetPathBase):
        os.mkdir(targetPathBase)
        os.chmod(targetPathBase, directory_permission)
    
   


    for dayfolder in dayFolders:

        #print("dayfolder: ", dayfolder) 
    
        expected_timestamp_date = "{}-{}-{}".format(dayfolder["year"], dayfolder["month"], dayfolder["day"])
        dayPictures = getDayPictures(archive_url, folder, dayfolder, expected_timestamp_date)

        #print(dayPictures)
        if len(dayPictures) == 0:
            continue 

        print("------")
       
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(dayPictures)
        
       # sys.exit(1)

        
      

        for picture in dayPictures:
       # outfileBase = '{}_{}_{}.zip'.format(sitename, year, month)

            year = str(picture["year"])
            month = "{:02d}".format(picture["month"])
            day = "{:02d}".format(picture["day"])
            hour = "{:02d}".format(picture["hour"])
            minute = "{:02d}".format(picture["minute"])
            orgFilename = picture["filename"]
            sourcePath =  picture["path"]

            #print("sourcePath: ", sourcePath)

            sourceURL = archive_url + sourcePath + orgFilename

            #print("sourceURL: ", sourceURL)


            targetFilenameBase = "{}{}{}-{}{}_{}".format(year, month, day, hour, minute, orgFilename)


            yearDir = os.path.join(targetPathBase, year)
            if not os.path.isdir(yearDir):
                os.mkdir(yearDir)
                os.chmod(yearDir, directory_permission)

            monthDir = os.path.join(yearDir, month)
            if not os.path.isdir(monthDir):
                os.mkdir(monthDir)
                os.chmod(monthDir, directory_permission)

            dayDir = os.path.join(monthDir, day)
            if not os.path.isdir(dayDir):
                os.mkdir(dayDir)
                os.chmod(dayDir, directory_permission)


            targetFile = os.path.join(dayDir, targetFilenameBase)

            #tmpDownloadTarget = os.path.join(TMPDIR, targetFilenameBase)
            

            #print("tmpDownloadTarget: ", tmpDownloadTarget)
            #print("targetFile: ", targetFile)
            

            #sys.exit(1)

            #targetPathBase = os.path.join(cameraDir, picture_type)
            
            if os.path.exists( targetFile ):
                # skip download, we already have that file 
                continue

            print("writing ", targetFile)
            r = requests.get(sourceURL, stream=True)
            if r.status_code != 200:
                print("got status_code: ", r.status_code )
                sys.exit(1)
            with open(targetFile, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)       

            os.chmod(targetFile, file_permisson) 



    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="HPWREN mirror script")
    
    # options

    
    parser.add_argument("-c","--config",
                        help="config file with lists of data sets to mirror",
                        default = ""
                         )

    parser.add_argument("-v","--verbose",
                        help="increase output verbosity",
                        action="store_true",
                        default=False)

    parser.add_argument("-d","--debug",
                        help="log connections for debugging",
                        action="store_true",
                        default=False)



    

    # get args
    args = parser.parse_args()
    
    config_file = args.config
    verbose = args.verbose
    debug = args.debug


    # get env
    mirrorDir = os.getenv('HPWREN_MIRROR_DIR')
    if not mirrorDir:
        print("Enviornment variable HPWREN_MIRROR_DIR is not defined")
        sys.exit(1)

    if not os.path.isdir(mirrorDir):
        print("directory {} does not exist.".format(mirrorDir))
        sys.exit(1)

    locations = []

    with open(config_file) as config_f:
        for line in config_f:
            #print(line)

            # remove comments
            line = line.split('#', 1)[0]
            line_array = line.split(',', 2)
            location = line_array[0].strip()
            #print("location: ",  location)
            if location == "":
                continue
            cameras = [x.strip() for x in  line_array[1].split(';')]
            description = line_array[2]
            #print(location, cameras)
            locations.append({ 'location' : location, 'cameras': cameras , 'description': description})
    

    #pp = pprint.PrettyPrinter(indent=4)
    #pp.pprint(locations)

    for source in locations:
        #print(source)
        site = source['location']
        for camera in source['cameras']:
            print("download pictures on site {} from camera {} ...".format(site, camera))
    
            download(site=site, camera=camera, picture_type='c')

