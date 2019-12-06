import pathlib

SRC_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
JS_DIR = SRC_DIR / 'js'
CSS_DIR = SRC_DIR / 'css'

from .utils import tag
from .utils import organize_contents
from .utils import read_script
from .review_data_convertor import ReviewDataConvertor
from .attr_map_convertor import AttrMapConvertor

__all__ = ['ReviewDataConvertor']