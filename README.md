# GTakeoutMediaFixer

Python script to fix the media from Google takeout (date, GPS info ...), inspired by [Google Photos Matcher](https://github.com/anderbggo/GooglePhotosMatcher)

## Introduction 📙

Media downloaded from google takeout are striped from there EXIF metadata, such as (GPS coordinate, ...), those metadata are stored in matching json files, 
this program add the missing metadata and delete the json file

## Usage

1. Download your _Google_ media from [Takeout](https://takeout.google.com/)
2. Install the requirement: ```pip install -r requirements.txt```
3. Start the scrip ```python gtakeout_media_fixer.py```
4. Select the folder in which images/videos along with its JSONs were downloaded ('Photos from 20xx' for example)
5. Click on _Fix_ button
