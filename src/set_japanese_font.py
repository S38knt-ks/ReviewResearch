from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path

FONT_DIR    = r"C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\Fonts"
YU_GOTHIC_M = "YuGothM.ttc"

def set_font(font_dir=FONT_DIR, font_name=YU_GOTHIC_M):
    resource_add_path(FONT_DIR)
    LabelBase.register(DEFAULT_FONT, YU_GOTHIC_M)