# Authors: Nikolay Melnik <nmelnik@upwork.com>

import os

from api import app


def get_or_create_data_folder():
    path = app.config['DATA_FOLDER']
    if not os.path.exists(path):
        os.makedirs(path)
    return path
