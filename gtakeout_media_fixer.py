import json
import os
import time
import PySimpleGUI as sg
from pathlib import Path
from datetime import datetime
from exif import Image
from win32_setctime import setctime
from src.helper import dd2dms

piexif_codecs = [k.lower() for k in ['.TIF', '.TIFF', '.JPEG', '.JPG']]
DRY_RUN = False


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
                  [sg.Text("Choose a folder: ")],
                  [sg.Input(key="-IN2-", change_submits=True, size=(72, 0)), sg.FolderBrowse(key="-IN-")],
                  [sg.T("")],
                  [sg.Text('Working folder:', key='-FOLDER-')],
                  [sg.ProgressBar(100, size=(48, 3),  orientation='h', border_width=4, key='-PROGRESS_BAR-'), sg.T("0%", key='-PROGRESS_LABEL-')],
                  [sg.Multiline(size=(180, 12), key='-LOG-', autoscroll=True)],
                  [sg.T("")],
                  [sg.Button("Fix")]]

        self._window = sg.Window('Google Takeout Fixer', layout, icon='photos.ico', size=(600, 450))
        sg.cprint_set_output_destination(self._window, '-LOG-')

        while True:
            event, values = self._window.read()

            if event == sg.WIN_CLOSED or event == "Exit":
                break
            elif event == "Fix":
                self._root_path = Path(values["-IN2-"])
                self._conversion_path(self._root_path, dry_run=True)
                self._conversion_path(self._root_path)
                self._window['-PROGRESS_LABEL-'].update('100%')
                self._window['-PROGRESS_BAR-'].update(100)
                self._window['-FOLDER-'].update('Working folder:')
                sg.cprint(f'Fix complete !!!', c='green')

    def _set_exif(self, file, google_exif, time_stamp):
        lat = google_exif['geoData']['latitude']
        lng = google_exif['geoData']['longitude']
        altitude = google_exif['geoData']['altitude']
        time_stamp = time_stamp

        # Add Exif data
        try:
            with open(file, 'rb') as image_file:
                date_time = datetime.fromtimestamp(time_stamp).strftime("%Y:%m:%d %H:%M:%S")  # Create date object

                exif_image = Image(image_file)
                exif_image.datetime = date_time
                exif_image.datetime_original = date_time
                exif_image.datetime_digitized = date_time

                geo_data = google_exif['geoDataExif']
                exif_image.gps_longitude, exif_image.gps_longitude_ref = dd2dms(geo_data['longitude'], direction='longitude')
                exif_image.gps_latitude, exif_image.gps_latitude_ref = dd2dms(geo_data['latitude'], direction='latitude')

            with open(file, 'wb') as image_file:
                image_file.write(exif_image.get_file())

        except:
            sg.cprint(f"Failed to modify EXIF: {file.name}", c='red')

    def _fix_file(self, file: Path):
        with open(file, encoding="utf8") as f:  # Load JSON into a var
            data = json.load(f)

        # SEARCH MEDIA ASSOCIATED TO JSON
        original_title = data['title']  # Store metadata into vars

        if '.' in original_title:
            try:
                media = file.parent / Path(file.stem)
            except Exception as e:
                sg.cprint(f"File {original_title} doesn't match any file", c='red')
                self._error_ctr += 1
                return
        else:
            print(f"File {file} is not a media associated json, removing")
            file.unlink()
            return

        if DRY_RUN:
            sg.cprint(f'Process element: {media.name}', c='blue')
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
            try:
                print(f'Renaming {media.name} to {original_title}')
                media.rename(media.parent / original_title)
            except:
                sg.cprint(f'Fail to rename file: {media.name}', c='red')

        # All good remove json file
        file.unlink()

    def _conversion_path(self, path: Path, dry_run: bool = False):
        if path.is_dir():
            if not dry_run:
                self._window['-FOLDER-'].update(value=f'Working folder: {path.stem}')

            for obj in path.iterdir():
                self._conversion_path(path=obj, dry_run=dry_run)
        else:
            if path.suffix.lower() == '.json':  # Check if file is a JSON
                if dry_run:
                    self._nb_media_to_fix += 1
                else:
                    self._fix_file(file=path)
                    progress = round(self._nb_media_fixed / self._nb_media_to_fix * 100, 2)
                    self._window['-PROGRESS_LABEL-'].update(str(progress) + "%")
                    self._window['-PROGRESS_BAR-'].update(progress)
                    self._nb_media_fixed += 1


if __name__ == "__main__":
    media_fixer = GTakeoutMediaFixer()
    media_fixer.start()
