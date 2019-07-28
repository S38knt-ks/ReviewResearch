import pathlib

from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path

curr_dir = pathlib.Path(__file__).resolve().parent
FONT_DIR = curr_dir.parent.parent / 'Fonts'
YU_GOTHIC_M = "YuGothM.ttc"

def set_font(font_dir=FONT_DIR, font_name=YU_GOTHIC_M):
    resource_add_path(FONT_DIR)
    LabelBase.register(DEFAULT_FONT, YU_GOTHIC_M)