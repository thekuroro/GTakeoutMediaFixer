import json
import os
import time
import PySimpleGUI as sg
from pathlib import Path
from datetime import datetime
from exif import Image
from win32_setctime import setctime

piexif_codecs = [k.lower() for k in ['.TIF', '.TIFF', '.JPEG', '.JPG']]


class GTakeoutMediaFixer:
    def __init__(self):
        self._nb_media_to_fix = 0
        self._nb_media_fixed = 0
        self._error_ctr = 0
        self._window = None
        self._root_path = Path()
        self._edited_word = ''

    def start(self):
        layout = [[sg.T("")],
                  [sg.Text('Enter suffix used for edited photos (optional):')],
                  [sg.InputText(key='-INPUT_TEXT-'), sg.ReadFormButton('Help')],
                  [sg.T("")],
                  [sg.Text("Choose a folder: ")],
                  [sg.Input(key="-IN2-", change_submits=True), sg.FolderBrowse(key="-IN-")],
                  [sg.T("")],
                  [sg.Button("Match")],
                  [sg.T("")],
                  [sg.ProgressBar(100, visible=False, orientation='h', border_width=4, key='-PROGRESS_BAR-')],
                  [sg.T("", key='-PROGRESS_LABEL-')]]

        self._window = sg.Window('Google Photos Matcher', layout, icon='photos.ico')

        while True:
            event, values = self._window.read()

            if event == sg.WIN_CLOSED or event == "Exit":
                break
            elif event == "Match":
                self._root_path = Path(values["-IN2-"])
                self._edited_word = values['-INPUT_TEXT-']
                self._conversion_path(self._root_path, dry_run=True)
                self._conversion_path(self._root_path)
            elif event == "Help":
                sg.Popup("", "Media edited with the integrated editor of google photos "
                             "will download both the original image 'Example.jpg' and the edited version 'Example-edited.jpg'.",
                             "",
                             "The 'edited' suffix changes depending on the language.",
                             "",
                             "If you leave this box blank default spanish suffix will be used to search for edited photos.",
                             "", title="Information", icon='photos.ico')

    def _set_exif(self, file, data, time_stamp):
        lat = data['geoData']['latitude']
        lng = data['geoData']['longitude']
        altitude = data['geoData']['altitude']
        time_stamp = time_stamp

        # Add Exif data
        with open(file, 'rb') as image_file:
            date_time = datetime.fromtimestamp(time_stamp).strftime("%Y:%m:%d %H:%M:%S")  # Create date object

            exif_image = Image(image_file)

            exif_image.datetime = date_time
            exif_image.datetime_original = date_time
            exif_image.datetime_digitized = date_time

            # TODO add GPS info
            # exif_image.gps_latitude = data['geoData']['latitude']
            # exif_image.gps_longitude = data['geoData']['longitude']
            # exif_image.gps_altitude = data['geoData']['altitude']

        with open(file, 'wb') as image_file:
            image_file.write(exif_image.get_file())

    def _fix_file(self, file: Path):
        with open(file, encoding="utf8") as f:  # Load JSON into a var
            data = json.load(f)

        # SEARCH MEDIA ASSOCIATED TO JSON
        original_title = data['title']  # Store metadata into vars

        if '.' in original_title:
            try:
                media = file.parent / Path(file.stem)
            except Exception as e:
                print(f"File {original_title} doesn't match any file")
                self._error_ctr += 1
                return
        else:
            print(f"File {file} is not a media associated json, removing")
            file.unlink()
            return

        # METADATA EDITION
        time_stamp = int(data['photoTakenTime']['timestamp'])  # Get creation time
        print(media)

        if media.suffix.lower() in piexif_codecs:  # If file support EXIF data
            self._set_exif(media, data, time_stamp)

            # Correct file creation and modification date
            setctime(media, time_stamp)  # Set Windows file creation time
            date = datetime.fromtimestamp(time_stamp)
            mod_time = time.mktime(date.timetuple())
            os.utime(media, (mod_time, mod_time))  # Set Windows file modification time

        # Restore original filename
        if original_title != media.name:
            print(f'Renaming {media.name} to {original_title}')
            media.rename(media.parent / original_title)

        # All good remove json file
        file.unlink()

    def _conversion_path(self, path: Path, dry_run: bool = False):
        if path.is_dir():
            for obj in path.iterdir():
                self._conversion_path(path=obj, dry_run=dry_run)
        else:
            if path.suffix.lower() == '.json':  # Check if file is a JSON
                if dry_run:
                    self._nb_media_to_fix += 1
                else:
                    self._fix_file(file=path)
                    progress = round(self._nb_media_fixed / self._nb_media_to_fix * 100, 2)
                    self._window['-PROGRESS_LABEL-'].update(str(progress) + "%", visible=True)
                    self._window['-PROGRESS_BAR-'].update(progress, visible=True)
                    self._nb_media_fixed += 1


if __name__ == "__main__":
    media_fixer = GTakeoutMediaFixer()
    media_fixer.start()
