import argparse
import os
import glob
import re
import random
import pathlib
from collections import OrderedDict, namedtuple
from pprint import pprint
from typing import Tuple, Dict, NamedTuple

import pandas

from review_research.misc import unique_sort_by_index

class HtmlCSV(NamedTuple):
  """商品レビューページの html 一覧が記述されている csv ファイルをまとめるクラス

  Attributes:
    detail (pathlib.Path): 全商品レビューページ一覧が記述されている csv ファイル
    sample (pathlib.Path): 開発セット用の商品レビューページが記述されている csv ファイル
  """
  detail: pathlib.Path
  sample: pathlib.Path

CSV_DATA_FIELD = ['reviews', 'stars', 'link']
CSVData = namedtuple('CSVData', CSV_DATA_FIELD)

CLASS_DATA_FIELD = ['class_0', 'class_1', 'class_2', 'class_3']
ClassData = namedtuple('ClassData', CLASS_DATA_FIELD)
CLASS_DATA_KEYS  = ClassData(*CLASS_DATA_FIELD)
CLASS_DATA_QUERY = {
  CLASS_DATA_KEYS.class_0: 'stars > 4.0',
  CLASS_DATA_KEYS.class_1: '4.0 >= stars > 3.0',
  CLASS_DATA_KEYS.class_2: '3.0 >= stars > 2.0',
  CLASS_DATA_KEYS.class_3: 'stars <= 2.0'
}

def group_by_category(
    csvfiles: Tuple[pathlib.Path, ...]) -> Dict[str, HtmlCSV]:
  category_list = []
  detail_dict = OrderedDict()
  sample_dict = OrderedDict()
  for csvfile in csvfiles:
    csv_name = csvfile.name
    category = csvfile.parent.name

    if csv_name.endswith('detail.csv'):
      detail_dict[category] = csvfile

    elif csv_name == 'sample.csv':
      sample_dict[category] = csvfile

    else:
      continue

    if category not in category_list:
      category_list.append(category)
  
  csv_dict = OrderedDict()
  category_list = list(unique_sort_by_index(category_list))
  for category in category_list:
    detail = detail_dict[category]
    sample = sample_dict[category]
    csv_dict[category] = HtmlCSV(detail, sample)

  return csv_dict

def read_csv(csvfile: pathlib.Path):
  sep_pat = re.compile(r',\s?')
  with csvfile.open(mode='r', encoding='utf-8') as fp:
    contents = [CSVData(*sep_pat.split(line.strip())) for line in fp]

  header, data = contents[0], contents[1:]
  return header, data

def create_candidate_validation(
    csv_dict: Dict[str, HtmlCSV]) -> Dict[str, pandas.DataFrame]:
  df_dict = OrderedDict()
  for category, (detail, sample) in csv_dict.items():
    header, detail_data = read_csv(detail)
    _, sample_data = read_csv(sample)
    type_dict = {header.reviews: int,
                 header.stars: float}

    candidate_valid_list = list(set(detail_data) - set(sample_data))
    candidate_valid_df = pandas.DataFrame(candidate_valid_list,
                                               columns=CSV_DATA_FIELD)
    candidate_valid_df = candidate_valid_df.astype(type_dict)
    sorted_valid_df = candidate_valid_df.sort_values(header.stars, 
                                                     ascending=False)
    df_dict[category] = sorted_valid_df.query('reviews >= 20')

  return df_dict

def divide_by_class(csv_df: pandas.DataFrame):
  df_dict = OrderedDict()
  for class_num, query in CLASS_DATA_QUERY.items():
    applied_df = csv_df.query(query)
    df_dict[class_num] = applied_df.sort_values('stars', ascending=False)

  return df_dict

def main(args):
  input_dir = args.input_dir
  all_paths = tuple(
      pathlib.Path(f) 
      for f in glob.glob('{}/**'.format(input_dir), recursive=True))
  all_csvfiles = tuple(p for p in all_paths if p.suffix == '.csv')

  csv_dict = group_by_category(all_csvfiles)
  candidate_val_dict = create_candidate_validation(csv_dict)

  outdir = pathlib.Path(args.outdir)
  header_line = '{}\n'.format(','.join(CSV_DATA_FIELD))
  for category, df in candidate_val_dict.items():
    category_dir = outdir / category
    if not category_dir.exists():
      category_dir.mkdir(parents=True)

    validation_list = []
    df_by_class = divide_by_class(df)
    for class_num, data in df_by_class.items():
      if len(data) == 0:
        continue

      html_list = data.query('reviews < 40').values.tolist()
      html_for_valid = random.choice(html_list)
      validation_list.append(html_for_valid)
      outfile = category_dir / '{}.csv'.format(class_num)
      with outfile.open(mode='w', encoding='utf-8') as fp:
        fp.write(header_line)
        for content in data.values.tolist():
          fp.write('{}\n'.format(','.join(str(c) for c in content)))

    out_name = category_dir / 'validation.csv'
    with out_name.open(mode='w', encoding='utf-8') as fp:
      fp.write(header_line)
      for content in validation_list:
        fp.write('{}\n'.format(','.join(str(c) for c in content)))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('outdir')
  main(parser.parse_args())