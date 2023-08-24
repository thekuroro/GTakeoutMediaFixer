# GTakeoutMediaFixer

Python script to fix the media from Google takeout (date, GPS info ...), inspired by [Google Photos Matcher](https://github.com/anderbggo/GooglePhotosMatcher)

## Introduction 📙

Media downloaded from google takeout are striped from there EXIF metadata, such as (GPS coordinate, ...), those metadata are stored in matching json files, 
this program add the missing metadata and delete the json file

## What it does
This script will process all the files in the specified path, the duplicated file will be moved to the --DUPLICATES-- folder, once proceeded the json file containing the missing data will be removed, leaving you only with picture

## Usage

1. Download your _Google_ media from [Takeout](https://takeout.google.com/)
2. Install the requirement: ```pip install -r requirements.txt```
3. Start the scrip ```python gtakeout_media_fixer.py```
4. Select the folder in which images/videos along with its JSONs were downloaded ('Google Photos' for example)
5. Click on _Fix_ button
