import argparse
import os
import glob
import json
import pathlib
import re
import time
import traceback
from pprint import pprint, pformat
from collections import namedtuple, OrderedDict

import numpy as np
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..review import ReviewPageJSON, ReviewInfo, StarsDistribution

# BeautifulSoup#find or #findAllの引数を登録するためのタプルの用意
FIND_ATTRS = ['name', 'attrs']
FindAttrs = namedtuple('find_attrs', FIND_ATTRS)

# レビューページ上部に表示されている情報を取得するためのパラメータ
LINK_FINDATTRS          = FindAttrs('link', {'rel': 'canonical'})
PRODUCT_DIV_FINDATTRS   = FindAttrs('div',  {'role': 'main'})
MAKER_FINDATTRS         = FindAttrs('div',  {'class': 'a-row product-by-line'})
AVERAGE_STAR_FINDATTRS  = FindAttrs('i',    {'data-hook': 'average-star-rating'})
TOTAL_REVIEWS_FINDATTRS = FindAttrs('span', {'class'    : 'a-size-medium totalReviewCount',
                                             'data-hook': 'total-review-count'})

# ReviewInfoの範囲を絞るための用意
REVIEW_INFO_DIV_FINDATTRS = FindAttrs('div', {'data-hook': 'review'})

# ReviewInfoを埋めるためのパラメータ
DATE_FINDATTRS   = FindAttrs('span', {'class': 'a-size-base a-color-secondary review-date',
                                      'data-hook': 'review-date'})
STAR_FINDATTRS   = FindAttrs('i',    {'data-hook': 'review-star-rating'})
VOTE_FINDATTRS   = FindAttrs('span', {'class': 'a-size-base a-color-tertiary cr-vote-text',
                                      'data-hook': 'helpful-vote-statement'})
NAME_FINDATTRS   = FindAttrs('span', {'class': 'a-profile-name'})
TITLE_FINDATTRS  = FindAttrs('a',    {'data-hook': 'review-title'})
REVIEW_FINDATTRS = FindAttrs('span', {'data-hook': 'review-body'})

# 日付を取得するための正規表現
DATE_REGEX = re.compile(r'(?P<year>[0-9]*)年(?P<month>[0-9]*)月(?P<day>[0-9]*)日')

class ReviewInfoExtractor:

  def __init__(self, code='utf-8', parser='lxml'):
    self.code   = code
    self.parser = parser

  def extract_all_info(self, html_list: list):
    """商品レビューで重要だと思われる情報をすべて抽出する

        Params:
            html_list: list
                商品のhtmlファイルリスト
    """
    self._initialize_data()

    first_html = html_list[0]
    self.review_page_json.category = self._decide_category(first_html)
    self._extract_landmarks(first_html)
    self.all_info = [ri for h in html_list
                     for ri in self._extract_review_info_list(h)]

      
  def save_json(self, out_name: str, product: str):
    """抽出した情報をjsonファイルに保存

    Params:
      out_name: str
        出力するjsonファイルの名前

      product: str
        商品名
    """
    self.review_page_json.product            = product
    self.review_page_json.real_reviews       = len(self.all_info)
    self.review_page_json.stars_distribution = self.stars_distibution_dict
    self.review_page_json.reviews            = self.all_info

    self.review_page_json.dump(out_name)

  
  def _initialize_data(self):
    self.category         = None
    self.review_landmarks = None
    self.all_info         = None

    self.review_page_json = ReviewPageJSON()

    star_list = np.arange(1, 5+1).astype(float)
    self.stars_distibution_dict = OrderedDict()
    for s in star_list:
      self.stars_distibution_dict[s] = 0


  def _decide_category(self, html_path):
    html_path    = pathlib.Path(html_path).resolve()
    product_dir  = html_path.parent
    categoty_dir = product_dir.parent
    category     = categoty_dir.name
    return category


  def _extract_landmarks(self, html):
    bs = BeautifulSoup(pathlib.Path(html).open(mode='r', encoding=self.code),
                        self.parser)

    link = bs.find(LINK_FINDATTRS.name, LINK_FINDATTRS.attrs)['href']
    landmarks_div = bs.find(PRODUCT_DIV_FINDATTRS.name,
                            PRODUCT_DIV_FINDATTRS.attrs)
    maker = landmarks_div.find(MAKER_FINDATTRS.name,
                               MAKER_FINDATTRS.attrs).text.strip()
    average_star = landmarks_div.find(AVERAGE_STAR_FINDATTRS.name,
                                      AVERAGE_STAR_FINDATTRS.attrs)
    total_reviews = landmarks_div.find(TOTAL_REVIEWS_FINDATTRS.name,
                                       TOTAL_REVIEWS_FINDATTRS.attrs)

    average_star = self._extract_stars(average_star)
    total_reviews = int(total_reviews.text.strip().replace(',', ''))
    self.review_page_json.link          = link
    self.review_page_json.maker         = maker
    self.review_page_json.average_stars = average_star
    self.review_page_json.total_reviews = total_reviews

  def _extract_review_info_list(self, html) -> list:
    bs = BeautifulSoup(pathlib.Path(html).open(mode='r', encoding=self.code),
                       self.parser)

    review_div_list = bs.findAll(REVIEW_INFO_DIV_FINDATTRS.name,
                                 REVIEW_INFO_DIV_FINDATTRS.attrs)

    return [self._get_review_info(rv) for rv in review_div_list]


  def _get_review_info(self, review_div) -> ReviewInfo:
    date = ''
    star = 0
    vote = 0
    name = ''
    title = ''
    review = ''

    try:
      date_text = review_div.find(DATE_FINDATTRS.name, 
                                  DATE_FINDATTRS.attrs).text.strip()
      star_text = review_div.find(STAR_FINDATTRS.name,
                                  STAR_FINDATTRS.attrs).text.strip()
      vote_text = review_div.find(VOTE_FINDATTRS.name, VOTE_FINDATTRS.attrs)
      date   = self._extract_date(date_text)
      star   = self._extract_stars(star_text)
      vote   = self._extract_vote(vote_text)
      name   = review_div.find(NAME_FINDATTRS.name,
                               NAME_FINDATTRS.attrs).text.strip()
      title  = review_div.find(TITLE_FINDATTRS.name, 
                               TITLE_FINDATTRS.attrs).text.strip()
      review = review_div.find(REVIEW_FINDATTRS.name,
                               REVIEW_FINDATTRS.attrs).text.strip()
      self.stars_distibution_dict[star] += 1

    except AttributeError:
      tqdm.write('<Attribute Error>')
      tqdm.write('{}'.format(traceback.format_exc()))

    return ReviewInfo(date, int(star), vote, name, title, review)


  def _extract_date(self, content) -> str:
    date_text = DATE_REGEX.match(content)
    date = '{}/{}/{}'.format(date_text.group('year'),
                             date_text.group('month').zfill(2),
                             date_text.group('day').zfill(2))
    return date

  
  def _extract_stars(self, content) -> float:
    stars = float(content.replace('5つ星のうち', ''))
    return stars

  
  def _extract_vote(self, content) -> int:
    vote = 0
    if content:
      vote_text = content.text.strip()
      vote = int(vote_text.replace('人のお客様がこれが役に立ったと考えています', ''))

    return vote

        


def main(args):
  input_dir = args.input_dir
  all_files = glob.glob('{}/**'.format(input_dir), recursive=True)
  page_pat = re.compile(r'.*\\page_(\d+)\.html')

  review_html_list = sorted([pathlib.Path(f).resolve() for f in all_files
                             if page_pat.match(f)])

  product_dict = OrderedDict()
  for review_html in review_html_list:
    product_key = review_html.parent
    product_dict.setdefault(product_key, []).append(review_html)

  print('[products]\t{}'.format(len(product_dict)))
  print('[htmls]\t{}'.format(len(review_html_list)))
  print()

  print('extracting...')
  rie = ReviewInfoExtractor()        
  for product_key, review_html_list in tqdm(product_dict.items(), ascii=True):
    tqdm.write('[product]\t{}'.format(product_key))
    
    tqdm.write('htmls = {}'.format(len(review_html_list)))
    tqdm.write(pformat(review_html_list))

    rie.extract_all_info(review_html_list)

    product = product_key.stem
    out_file = os.path.join(str(product_key), 'review.json')
    tqdm.write(out_file)
    rie.save_json(out_file, product)

  print('done!')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  main(parser.parse_args())
