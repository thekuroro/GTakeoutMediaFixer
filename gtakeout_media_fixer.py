import json
import os
import platform
import shutil
import time
import logging
import PySimpleGUI as Sg
from pathlib import Path
from datetime import datetime
from exif import Image
from src.helper import dd2dms
from logging import INFO, WARNING, ERROR


piexif_codecs = [k.lower() for k in ['.TIF', '.TIFF', '.JPEG', '.JPG']]
log_level_color = {INFO: 'blue', WARNING: 'Orange', ERROR: 'red'}


class GTakeoutMediaFixer:
    def __init__(self):
        self._nb_media_to_fix = 0
        self._nb_media_fixed = 0
        self._window = None
        self._root_path = Path()
        self._duplicates_path = Path()
        self._edited_word = ''
        self._logger = logging.getLogger('')

    def start(self):
        """
            Display UI
        """
        layout = [[Sg.T("")],
                  [Sg.Text("Choose a folder: ")],
                  [Sg.Input(key="-IN2-", change_submits=True, size=(72, 0)), Sg.FolderBrowse(key="-IN-")],
                  [Sg.T("")],
                  [Sg.Text('Working folder:', key='-FOLDER-')],
                  [Sg.ProgressBar(100, size=(48, 3), orientation='h', border_width=4, key='-PROGRESS_BAR-'), Sg.T("0%", key='-PROGRESS_LABEL-')],
                  [Sg.Multiline(size=(180, 12), key='-LOG-', autoscroll=True)],
                  [Sg.T("")],
                  [Sg.Button("Fix")]]

        self._window = Sg.Window('Google Takeout Fixer', layout, icon='google_photos.ico', size=(605, 450))
        Sg.cprint_set_output_destination(self._window, '-LOG-')

        while True:
            event, values = self._window.read()

            if event == Sg.WIN_CLOSED or event == "Exit":
                break
            elif event == "Fix":
                self._root_path = Path(values["-IN2-"])
                self._duplicates_path = self._root_path / '--DUPLICATES--'
                logging.basicConfig(filename=self._root_path / 'fix_info.log', encoding='utf-8', level=logging.INFO)

                self._count_total_files(self._root_path)
                self._conversion_recurse(self._root_path)
                self._window['-PROGRESS_LABEL-'].update('100%')
                self._window['-PROGRESS_BAR-'].update(100)
                self._window['-FOLDER-'].update('Working folder:')
                self.log_event('Fix complete !!!', WARNING, color='green')

    def log_event(self, msg, level, color: str = ''):
        self._logger.log(msg=msg, level=level)
        print_color = color if color else log_level_color[level]
        Sg.cprint(msg, c=print_color)

    @staticmethod
    def _is_file_duplicate(file: Path) -> bool:
        """
            Return true if the file is a duplicate
        """
        full_suffixes = "".join(file.suffixes)
        file_name = file.name.replace(full_suffixes, '')

        if (file_name[-1] == ')' and file_name[-2].isdecimal()) or '(' in full_suffixes:
            return True
        else:
            return False

    @staticmethod
    def _set_exif(file, google_exif: dict, time_stamp):
        """
            Add the missing EXIF data
        """
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
            Sg.cprint(f"Failed to modify EXIF: {file.name}", c='red')

    def _fix_file(self, file: Path):
        """
            Fix the file (EXIF data + creation/modification date)
        """
        with open(file, encoding="utf8") as f:  # Load JSON into a var
            data = json.load(f)

        if 'title' not in data:
            return

        # SEARCH MEDIA ASSOCIATED TO JSON
        original_title = data['title']  # Store metadata into vars

        if '.' in original_title:
            media = file.parent / Path(file.stem)
            if not media.exists():
                self.log_event(f"File {original_title} doesn't match any file", ERROR)
                return
        else:
            self.log_event(f"File {file} is not a media associated json, removing", WARNING)
            file.unlink()
            return

        # EXIF data edition
        time_stamp = int(data['photoTakenTime']['timestamp'])  # Get creation time

        if media.suffix.lower() in piexif_codecs:  # If file support EXIF data
            self._set_exif(media, data, time_stamp)

        # Correct file creation and modification date
        if platform.system() == "Windows":
            from win32_setctime import setctime
            setctime(media, time_stamp)  # Set file creation time (Windows only)
        date = datetime.fromtimestamp(time_stamp)
        mod_time = time.mktime(date.timetuple())
        os.utime(media, (mod_time, mod_time))  # Set file modification time

        # Restore original filename
        if original_title != media.name:
            try:
                self.log_event(f'Renaming {media.name} to {original_title}', INFO)
                media.rename(media.parent / original_title)
                file.unlink()
            except:
                self.log_event(f'Fail to rename file: {media.name}', ERROR)

        else:
            # All good remove json file
            file.unlink()

    def _count_total_files(self, path: Path):
        """
            Count the total number of files to fix
        """
        if path.is_dir():
            for obj in path.iterdir():
                self._count_total_files(path=obj)
        else:
            if path.suffix.lower() == '.json':  # Check if file is a JSON
                self._nb_media_to_fix += 1

    def _conversion_recurse(self, path: Path):
        """
            Recurse if path is a folder, if path is a file process it
        """
        if path.is_dir():
            if path != self._duplicates_path:
                self._window['-FOLDER-'].update(value=f'Working folder: {path.stem}')

                for obj in path.iterdir():
                    self._conversion_recurse(path=obj)

                if not any(path.iterdir()):
                    # Remove empty dir
                    self.log_event(f'Removing emtpy folder: {path.name}', WARNING)
                    path.rmdir()
        else:
            if self._is_file_duplicate(file=path):
                # Moving file if it's a duplicate
                self._duplicates_path.mkdir(exist_ok=True)
                self.log_event(f'Moving duplicate: {path.name}', WARNING)
                shutil.move(path, self._duplicates_path / path.name)
                self._nb_media_fixed += 1
            else:
                if path.suffix.lower() == '.json':  # Check if file is a JSON
                    self._fix_file(file=path)
                    self._nb_media_fixed += 1

            progress = int(round(self._nb_media_fixed / self._nb_media_to_fix * 100, 2))
            self._window['-PROGRESS_LABEL-'].update(str(progress) + "%")
            self._window['-PROGRESS_BAR-'].update(progress)


if __name__ == "__main__":
    media_fixer = GTakeoutMediaFixer()
    media_fixer.start()
