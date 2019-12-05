"""review.json ファイルを html ファイルに変換するスクリプト"""

import argparse
import json
import glob
import os
import pathlib
from pprint import pprint

import pandas
from tqdm import tqdm

from .htmlgenerator import ReviewDataConvertor
from .misc import get_all_jsonfiles

def main(args):
  input_dir = args.input_dir
  json_list = get_all_jsonfiles(input_dir, 'review.json')

  normalize = args.normalize
  convertor = ReviewDataConvertor(normalize_mode=normalize)
  out_dir = pathlib.Path(args.out_dir)
  for path in tqdm(json_list, ascii=True):
    tqdm.write('\n[file] {}'.format(path))
    out_name = path.name.replace('.json', '.html')
    if normalize:
      out_name = out_name.replace('.html', '_normalized.html')

    product_dir = out_dir.parent
    out_name = product_dir / out_name
    html = convertor.convert(path)
    with out_name.open(mode='w', encoding='utf-8') as fp:
      fp.write(html)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('out_dir')
  parser.add_argument('--normalize',
                      action='store_true', default=False)
  main(parser.parse_args())