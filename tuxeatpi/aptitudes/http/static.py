"""Handle static files and folder"""

import os

import hug


def _current_folder():
    return os.path.dirname(__file__)

@hug.static("/ui")
def tuxeatpi_web():
    """Return ui files from ui folder
    populated by tuxeatpi-web project
    """
    ui_folder = os.path.join(_current_folder(), "ui")
    return (ui_folder, )


# Maybe this is not needed
@hug.static("/service-worker.js")
def tuxeatpi_web_worker():
    """Return service-worker.js"""
    ui_folder = os.path.join(_current_folder(), "ui/service-worker.js")
    return (ui_folder, )
