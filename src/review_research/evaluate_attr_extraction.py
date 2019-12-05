import os
import argparse
import json
import glob
import pathlib
from collections import OrderedDict, namedtuple
from pprint import pprint

from .evaluation import AttrExtractionEvaluater

def main(args):
  input_dir = args.input_dir
  all_files = glob.glob('{}\\**'.format(input_dir), recursive=True)
  json_file_list = [os.path.abspath(f) for f in all_files 
                    if os.path.isfile(f) and f.endswith('.json')]

  def is_target(path: str ,pattern: str):
    return os.path.basename(path) == pattern

  PATTERN_PAIR_FIELD = ['pred', 'result']
  PatternPair = namedtuple('PatternPair', PATTERN_PAIR_FIELD)
  pattern_pair_dict = {
      'extend':
          PatternPair('prediction_extended.json', 'result_extended.json'),
      'extended_ristrict': 
          PatternPair('prediction_extended_ristrict.json',
                      'result_extended_ristrict.json'),
      'ristrict':
          PatternPair('prediction_ristrict.json', 'result_ristrict.json'),
      'normal': PatternPair('prediction.json', 'result.json')
  }

  product_dir_list = [os.path.dirname(f) for f in json_file_list]
  product_dir_list = sorted(set(product_dir_list), key=product_dir_list.index)
  product_file_dict = {product_dir: [] for product_dir in product_dir_list}
  for json_file in json_file_list:
    for product_dir in product_dir_list:
      if json_file.startswith(product_dir):
        product_file_dict[product_dir].append(json_file)

  # 入出力ファイルの対応付け
  io_file_dict = OrderedDict()
  for product_dir, file_list in product_file_dict.items():
    file_dict = OrderedDict()
    for pattern_name, pattern_pair in pattern_pair_dict.items():
      pred_pat, res_pat = pattern_pair
      pred_file, res_file = '', ''
      for json_file in file_list:
        if is_target(json_file, pred_pat):
          pred_file = json_file

        elif is_target(json_file, res_pat):
          res_file = json_file

      file_dict[pattern_name] = PatternPair(pred_file, res_file)

    io_file_dict[product_dir] = file_dict

  # 正解データを取り出す
  eval_file_dict = OrderedDict()
  for product_dir, file_list in product_file_dict.items():
    for json_file in file_list:
      if is_target(json_file, 'eval.json'):
        eval_file_dict[product_dir] = json_file

  category = os.path.basename(input_dir)
  print(category)
  evaluater = AttrExtractionEvaluater(args.dic_dir, category)
  for product_dir, pattern_dict in io_file_dict.items():
    eval_file = eval_file_dict[product_dir]
    for pattern_name, pattern_pair in pattern_dict.items():
      print('[{}]'.format(pattern_name))
      pred_file, res_file = pattern_pair
      eval_result = evaluater.evaluate(eval_file, pred_file)
      eval_result.dump(res_file)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('dic_dir')

  main(parser.parse_args())