import argparse
import glob
import pathlib
import json
from collections import OrderedDict, Counter

import pandas
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def main(args):
    result_dir = args.result_dir
    review_jsons = [pathlib.Path(f) for f in glob.glob('{}/**'.format(result_dir), recursive=True)
                    if pathlib.Path(f).name == 'review.json']

    for review_json_path in tqdm(review_jsons, ascii=True):
      review_data = json.load(review_json_path.open(mode='r', encoding='utf-8'),
                              object_pairs_hook=OrderedDict)

      reviews = review_data['reviews']
      date_counter = Counter([review['date'] for review in reviews])
      reviews_on_date = np.array(sorted(date_counter.items(), key=lambda i: i[0]))
      dates = reviews_on_date[:, 0]
      x_ticks = range(len(dates))
      # print(list(x_ticks))
      review_counts = reviews_on_date[:, 1].astype(int)
      # print(review_counts)
      # quit()
      plt.figure(figsize=(16, 9))
      plt.bar(x_ticks, review_counts)
      plt.xticks(x_ticks, dates, rotation=90)
      plt.xlabel('date')
      plt.ylabel('review count')
      plt.tight_layout()
      product_dir = review_json_path.parent
      reviews_on_date_figname = product_dir / 'reviews_on_date.png'
      plt.savefig(reviews_on_date_figname)
      plt.clf()
      reviews_on_date_df = pandas.DataFrame(list(zip(dates, review_counts)), columns=['date', 'review_count'])
      reviews_on_date_csvname = product_dir / 'reviews_on_date.csv'
      reviews_on_date_df.to_csv(reviews_on_date_csvname, encoding='utf-8', index=None)

      vote_counter = Counter([review['vote'] for review in reviews])
      reviews_on_vote = np.array(sorted(vote_counter.items(), key=lambda i: i[0]))
      plt.bar(reviews_on_vote[:, 0], reviews_on_vote[:, 1])
      plt.xlabel('vote')
      plt.ylabel('review count')
      reviews_on_vote_figname = product_dir / 'reviews_on_vote.png'
      plt.savefig(reviews_on_vote_figname)
      plt.tight_layout()
      plt.clf()
      plt.close()
      reviews_on_vote_df = pandas.DataFrame(reviews_on_vote, columns=['vote', 'review_count'])
      reviews_on_vote_csvname = product_dir / 'reviews_on_vote.csv'
      reviews_on_vote_df.to_csv(reviews_on_vote_csvname, encoding='utf-8', index=None)
      # quit()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('result_dir')
  main(parser.parse_args())
    