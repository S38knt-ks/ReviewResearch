import argparse
import pathlib
import glob
import json
import re
import asyncio
from collections import OrderedDict, namedtuple

import pandas

from review_research.review import ReviewPageJSON

FEATURE_HEADER = ('index',
                  'vote',
                  'date',
                  'star',
                #   'reviewer',
                #   'title',
                #   'text',
                  'review_length',
                  'readability',
                  'purchaser',
                  'user',
                  'using_situation',
                  'not_reach_or_use',
                  'unrelated',
                  'comparion',
                  'reason_for_rating',
                  'evaluate_on_attribute',
                  'reason_for_attribute',
                  'detect_description_error',
                  'reviewer_status',
                  'reason_for_recommendation',
                  'reason_for_use')

Feature = namedtuple('Feature', FEATURE_HEADER)

async def create_template(review_json, semaphore):
  async with semaphore:
    # standardization_regex = re.compile(r'[\n,]+')
    reviews = ReviewPageJSON.load(review_json).reviews
    features = []
    for idx, review in enumerate(reviews):
      index = idx + 1 

      vote     = review.vote
      date     = review.date
      star     = review.star
      reviewer = review.name
      title    = review.title
      text     = review.review

      review_length = len(text)
      if review_length < 75:
        review_length = 0
      
      elif review_length <= 350:
        review_length = 1

      else:
        review_length = 2

      feature = Feature(index, vote, date, star,
                      #   reviewer, title, text,
                        review_length, '', '', '', '', '',
                        '', '', '', '', '')
      features.append(feature)

    df = pandas.DataFrame(features)
    template_file = review_json.parent / 'features_v2.csv'
    df.to_csv(str(template_file), index=None)


async def create(review_jsons, concur_num):
  semaphore = asyncio.Semaphore(concur_num)
  to_do = [create_template(review_json, semaphore) for review_json in review_jsons]
  await asyncio.gather(*to_do)


def main(args):
  review_dir = pathlib.Path(args.review_dir)

  all_files = glob.glob('{}/**'.format(review_dir), recursive=True)
  all_files = [pathlib.Path(f) for f in all_files
               if pathlib.Path(f).is_file()]
  review_jsons = [f for f in all_files
                  if f.suffix == '.json' and f.stem == 'review']

  print('Create feature format...')
  asyncio.run(create(review_jsons, args.concur_num))
  print('Done!')



if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('review_dir')
  parser.add_argument('-n', '--concur-num', type=int, default=10)
  
  main(parser.parse_args())