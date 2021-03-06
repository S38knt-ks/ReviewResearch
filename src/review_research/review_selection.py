"""
    レビューの選別に使うプログラム
    edgeとdistributionから選別方法を選ぶ

    edge
        「star」でソートを行い、その結果の両端から選ぶ

    distribution
        「star」でデータを分け、レビューの分配数を決定
        その後、「vote」でソートを行い、上位からその分配数分だけ選択する
"""

import argparse
import json
import os
import pathlib
import glob
from pprint import pprint
from collections import OrderedDict

import pandas
from tqdm import tqdm

from review_research.review import ReviewInfo
from review_research.review import ReviewPageJSON
from review_research.misc import get_all_jsonfiles


EDGE = 'edge'
DISTRIBUTION = 'distribution'

EXTRACT_CONTAINER = [EDGE, DISTRIBUTION]


def divide_df(df, key):
  df_dict = OrderedDict()
  value_list = [1.0, 2.0, 3.0, 4.0, 5.0]
  for v in value_list:
    df_dict[v] = df.query('{} == {}'.format(key, v))
  
  return df_dict

def save_data(json_data: ReviewPageJSON, sample_df: pandas.DataFrame, 
              extract: int, jsonpath: pathlib.Path):
  json_data.reviews = [ReviewInfo(*s) for s in sample_df.values.tolist()]
  out_filename = '_{}_{}.json'.format(extract, len(sample_df))
  out_file = str(jsonpath).replace('.json', out_filename)
  json_data.dump(out_file)

def main(args):
  input_dir = args.input_dir
  amount = args.amount
  extract = args.extract

  for jsonfile in tqdm(get_all_jsonfiles(input_dir), ascii=True):
    data = ReviewPageJSON.load(jsonfile)
    total_reviews = data.total_reviews
    if total_reviews <= amount:
      continue

    total_reviews = float(total_reviews)
    review_df = pandas.DataFrame(data.reviews)
    cols = review_df.columns.values.tolist()
    star_key = cols[1]

    if extract == DISTRIBUTION:
      df_dict = divide_df(review_df, star_key)
      vote_key = cols[2]
      sample_df_list = []
      for df in df_dict.values():
        sample_amount = 0
        if df.empty:
          continue

        else:
          sample_amount = int(len(df) * amount / total_reviews) + 1
          if sample_amount >= len(df):
            dif = sample_amount - len(df)
            sample_amount -= dif

        sample_df = df.sort_values(vote_key, ascending=False)
        sample_df_list.append(sample_df.head(sample_amount))

      sample_df = pandas.concat(sample_df_list)
      save_data(data, sample_df, extract, jsonfile)        

    else:
      sorted_df = review_df.sort_values(star_key, ascending=False)
      half = amount // 2
      head_df = sorted_df.head(half)
      tail_df = sorted_df.tail(amount - half)
      sample_df = pandas.concat([head_df, tail_df])
      save_data(data, sample_df, extract, jsonfile)           


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('--amount', type=int, default=20)
  parser.add_argument('--extract',
                      choices=EXTRACT_CONTAINER,
                      default=EXTRACT_CONTAINER[0])
  main(parser.parse_args())