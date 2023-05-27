"""
Open a GUI window to allow manual name / select.
TODO: rename to something more appropriate
"""
import platform
import sys
from os import path, remove

from clown_sort.config import Config
from clown_sort.filename_extractor import FilenameExtractor
from clown_sort.util.logging import log
from clown_sort.util.rich_helper import bullet_text, console, indented_bullet
from clown_sort.util.string_helper import is_empty

RADIO_COLS = 11
SELECT_SIZE = 45
DELETE = 'Delete'
OK = 'Move'
OPEN = 'Preview Image'
SKIP = 'Skip'
EXIT = 'Exit'


def process_file_with_popup(image: 'ImageFile') -> None:
    # Do the import here so as to allow usage without installing PySimpleGUI
    import PySimpleGUI as sg
    suggested_filename = FilenameExtractor(image).filename()
    sort_dirs = [path.basename(dir) for dir in Config.get_sort_dirs()]
    max_dirname_length = max([len(dir) for dir in sort_dirs])

    layout = [
        [sg.Image(data=image.image_bytes(), key="-IMAGE-")],
        [sg.Text("Enter file name:")],
        [sg.Input(suggested_filename, size=(len(suggested_filename), 1))],
        [sg.Combo(sort_dirs, size=(max_dirname_length, SELECT_SIZE))],
        [
            sg.Button(OK, bind_return_key=True),
            sg.Button(DELETE),
            sg.Button(OPEN),
            sg.Button(SKIP),
            sg.Button(EXIT)
        ]
    ]

    window = sg.Window(image.basename, layout)

    # Event Loop
    while True:
        event, values = window.Read()

        if event == OPEN:
            image.preview()
            continue

        window.close()

        if event == DELETE:
            log.warning(f"Deleting '{image.file_path}'")
            remove(image.file_path)
            return
        elif event == SKIP:
            return
        elif event == EXIT:
            sys.exit()
        elif event == OK:
            break

    log.debug(f"All values: {values}")
    chosen_filename = values[0]
    new_subdir = values[1]
    destination_dir = Config.sorted_screenshots_dir.joinpath(new_subdir)

    if is_empty(chosen_filename):
        raise ValueError("Filename can't be blank!")

    if not destination_dir.exists():
        result = sg.popup_yes_no(f"Subdir '{new_subdir}' doesn't exist. Create?",  title="Unknown Subdirectory")

        if result == 'Yes' and not Config.dry_run:
            log.info(f"Creating directory '{new_subdir}'...")
            destination_dir.mkdir()
        else:
            console.print(bullet_text(f"Directory not found. Skipping '{image.file_path}'..."))
            return

    new_filename = destination_dir.joinpath(chosen_filename)
    log.info(f"Chosen Filename: '{chosen_filename}'\nSubdir: '{new_subdir}'\nNew file: '{new_filename}'\nEvent: {event}\n")
    console.print(bullet_text(f"Moving '{image.file_path}' to '{new_filename}'..."))
    image.copy_file_to_sorted_dir(new_filename)
