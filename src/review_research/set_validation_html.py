import argparse
import os
import glob
import re
import random
from collections import OrderedDict, namedtuple
from pprint import pprint

import pandas

HTML_CSV_FIELD = ['detail', 'sample']
HtmlCSV = namedtuple('HtmlCSV', HTML_CSV_FIELD)

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

def group_by_category(file_list) -> OrderedDict:
  category_list = []
  detail_dict = OrderedDict()
  sample_dict = OrderedDict()
  for csv_file in file_list:
    category_dir, csv_name = os.path.split(csv_file)
    _, category = os.path.split(category_dir)

    if csv_name.endswith('detail.csv'):
      detail_dict[category] = csv_file

    elif csv_name == 'sample.csv':
      sample_dict[category] = csv_file

    else:
      continue

    if category not in category_list:
      category_list.append(category)
  
  csv_dict = OrderedDict()
  category_list = sorted(list(set(category_list)))
  pprint(category_list)
  for category in category_list:
    detail = detail_dict[category]
    sample = sample_dict[category]
    csv_dict[category] = HtmlCSV(detail, sample)

  return csv_dict


def read_csv(csv_file):
  sep_pat = re.compile(r',\s?')
  with open(csv_file, mode='r', encoding='utf-8') as fp:
    contents = [CSVData(*sep_pat.split(line.strip())) for line in fp.readlines()]

  header, data = contents[0], contents[1:]
  return header, data


def create_candidate_validation(csv_dict: OrderedDict) -> OrderedDict:
  df_dict = OrderedDict()
  for category, (detail, sample) in csv_dict.items():
    header, detail_data = read_csv(detail)
    _, sample_data      = read_csv(sample)
    type_dict = {header.reviews: int,
                 header.stars:   float}

    candidate_validation_list = list(set(detail_data) - set(sample_data))
    candidate_validation_df   = pandas.DataFrame(candidate_validation_list, columns=CSV_DATA_FIELD)
    candidate_validation_df   = candidate_validation_df.astype(type_dict)

    df_dict[category] = candidate_validation_df.sort_values(header.stars, ascending=False).query('reviews >= 20')

  return df_dict


def divide_by_class(csv_df: pandas.DataFrame):
  df_dict = OrderedDict()
  for key, query in CLASS_DATA_QUERY.items():
    df_dict[key] = csv_df.query(query).sort_values('stars', ascending=False)

  return df_dict


def main(args):
  input_dir = args.input_dir
  all_csv_file_list = [
      os.path.abspath(f) for f in glob.glob('{}/**'.format(input_dir), recursive=True)
      if os.path.isfile(f)
  ]

  csv_dict = group_by_category(all_csv_file_list)
  candidate_val_dict = create_candidate_validation(csv_dict)

  out_dir = args.out_dir
  header_line = '{}\n'.format(','.join(CSV_DATA_FIELD))
  for category, df in candidate_val_dict.items():
    category_dir = '{}/{}'.format(out_dir, category)
    if not os.path.exists(category_dir):
      os.makedirs(category_dir)

    validation_list = []
    df_by_class = divide_by_class(df)
    for key, data in df_by_class.items():
      if len(data) == 0:
        continue

      validation_list.append(random.choice(data.query('reviews < 40').values.tolist()))
      out_name = '{}/{}.csv'.format(category_dir, key)
      with open(out_name, mode='w', encoding='utf-8') as fp:
        fp.write(header_line)
        for content in data.values.tolist():
          fp.write('{}\n'.format(','.join(str(c) for c in content)))

    out_name = '{}/validation.csv'.format(category_dir)
    with open(out_name, mode='w', encoding='utf-8') as fp:
      fp.write(header_line)
      for content in validation_list:
        fp.write('{}\n'.format(','.join(str(c) for c in content)))


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('out_dir')
  main(parser.parse_args())