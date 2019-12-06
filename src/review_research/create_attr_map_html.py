import os
import json
import argparse
import glob
from pathlib import Path
from collections import OrderedDict, namedtuple
from pprint import pprint

from bs4 import BeautifulSoup

from review_research.misc import get_all_jsonfiles
from review_research.htmlgenerator import AttrMapConvertor

def main(args):
  dic_dir = args.dic_dir
  convertor = AttrMapConvertor(dic_dir)
  input_dir = args.input_dir
  map_json_list = get_all_jsonfiles(input_dir, 'map_')
  for map_json in map_json_list:
    html = convertor.convert(map_json)
    f_name = map_json.stem
    out_dir = map_json.parent
    out_file = out_dir / 'detail_{}.html'.format(f_name)

    with out_file.open(mode='w', encoding='utf-8') as fp:
      fp.write(html)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir',
                      help=('属性と星評価別に対応付けされた'
                            ' JSON ファイルが保存されているディレクトリ'))
  parser.add_argument('dic_dir',
                      help='属性辞書が格納されているディレクトリ')

  main(parser.parse_args())