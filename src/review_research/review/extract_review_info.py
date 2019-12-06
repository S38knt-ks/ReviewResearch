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
from typing import NoReturn, Iterable, Union, List

import numpy as np
import bs4
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..review import ReviewPageJSON, ReviewInfo, StarsDistribution

# BeautifulSoup#find or #findAllの引数を登録するためのタプルの用意
FIND_ATTRS = ['name', 'attrs']
FindAttrs = namedtuple('find_attrs', FIND_ATTRS)

# レビューページ上部に表示されている情報を取得するためのパラメータ
LINK_FINDATTRS = FindAttrs('link', {'rel': 'canonical'})
PRODUCT_DIV_FINDATTRS = FindAttrs('div', {'role': 'main'})
MAKER_FINDATTRS = FindAttrs('div', {'class': 'a-row product-by-line'})
AVERAGE_STAR_FINDATTRS = FindAttrs('i', {'data-hook': 'average-star-rating'})
TOTAL_REVIEWS_FINDATTRS = FindAttrs(
    'span', {'class': 'a-size-medium totalReviewCount',
             'data-hook': 'total-review-count'})

# ReviewInfoの範囲を絞るための用意
REVIEW_INFO_DIV_FINDATTRS = FindAttrs('div', {'data-hook': 'review'})

# ReviewInfoを埋めるためのパラメータ
DATE_FINDATTRS   = FindAttrs(
    'span', {'class': 'a-size-base a-color-secondary review-date',
             'data-hook': 'review-date'})
STAR_FINDATTRS   = FindAttrs('i',    {'data-hook': 'review-star-rating'})
VOTE_FINDATTRS   = FindAttrs(
    'span', {'class': 'a-size-base a-color-tertiary cr-vote-text',
             'data-hook': 'helpful-vote-statement'})
NAME_FINDATTRS   = FindAttrs('span', {'class': 'a-profile-name'})
TITLE_FINDATTRS  = FindAttrs('a',    {'data-hook': 'review-title'})
REVIEW_FINDATTRS = FindAttrs('span', {'data-hook': 'review-body'})

# 日付を取得するための正規表現
DATE_REGEX = re.compile(r'(?P<year>[0-9]*)年(?P<month>[0-9]*)月(?P<day>[0-9]*)日')

class ReviewInfoExtractor:
  """レビューページから分析に必要な情報を取り出す

  Attributes:
    parser (str): html のパーサ
    all_info (List[ReviewInfo]): レビューに関する情報一覧
    review_page_json (ReviewPageJSON): レビュー情報を格納するためのインスタンス
  """

  def __init__(self, parser: str = 'lxml'):
    self.parser = parser

  def __call__(self, html_list: Iterable[str]) -> NoReturn:
    """extract_all_info の呼び出し

    Args:
      html_list (Iterable[str]): 商品のhtmlファイルリスト
    """
    self.extract_all_info(html_list)

  def extract_all_info(self, html_list: Iterable[str]) -> NoReturn:
    """商品レビューで重要だと思われる情報をすべて抽出する

    Args:
      html_list (Iterable[str]): 商品のhtmlファイルリスト
    """
    self._initialize_data()

    first_html = html_list[0]
    self.review_page_json.category = _decide_category(first_html)
    self._extract_landmarks(first_html)
    self.all_info = [ri for h in html_list
                     for ri in self._extract_review_info_list(h)]

      
  def save_json(self, out_name: Union[str, pathlib.Path], 
                product: str) -> NoReturn:
    """抽出した情報をjsonファイルに保存

    Args:
      out_name (Union[str, pathlib.Path]): 出力するjsonファイルの名前
      product (str): 商品名
    """
    self.review_page_json.product = product
    self.review_page_json.real_reviews = len(self.all_info)
    self.review_page_json.stars_distribution = self.stars_distibution_dict
    self.review_page_json.reviews = self.all_info
    self.review_page_json.dump(out_name)

  
  def _initialize_data(self) -> NoReturn:
    """抽出するための準備のため、データを初期化する"""
    self.category = None
    self.all_info = None
    self.review_page_json = ReviewPageJSON()
    star_list = np.arange(1, 5 + 1).astype(float)
    self.stars_distibution_dict = OrderedDict()
    for s in star_list:
      self.stars_distibution_dict[s] = 0

  def _extract_landmarks(self, html: Union[str, pathlib.Path]) -> NoReturn:
    """商品に関する情報(URL や 評価)を抽出

    Args:
      html (Union[str, pathlib.Path]): html ファイルのパス
    """
    bs = BeautifulSoup(pathlib.Path(html).open(mode='r', encoding='utf-8'),
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

    average_star = _extract_stars(average_star)
    total_reviews = int(total_reviews.text.strip().replace(',', ''))
    self.review_page_json.link = link
    self.review_page_json.maker = maker
    self.review_page_json.average_stars = average_star
    self.review_page_json.total_reviews = total_reviews

  def _extract_review_info_list(self, 
      html: Union[str, pathlib.Path]) -> List[ReviewInfo]:
    """与えられた html ファイルに記述されているレビュー情報を抽出する

    Args:
      html (Union[str, pathlib.Path]): html ファイルのパス

    Returns:
      レビュー情報の一覧
    """
    bs = BeautifulSoup(pathlib.Path(html).open(mode='r', encoding='utf-8'),
                       self.parser)

    review_div_list = bs.findAll(REVIEW_INFO_DIV_FINDATTRS.name,
                                 REVIEW_INFO_DIV_FINDATTRS.attrs)

    return [self._get_review_info(rv) for rv in review_div_list]


  def _get_review_info(self, review_div: bs4.element.Tag) -> ReviewInfo:
    """レビューに関する情報を抽出する

    Args:
      review_div (bs4.element.Tag): html に書かれている1つのレビュー区画

    Returns:
      ReviewInfoインスタンス
    """
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
      date   = _extract_date(date_text)
      star   = _extract_stars(star_text)
      vote   = _extract_vote(vote_text)
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


## ヘルパー関数群
def _decide_category(html_path: Union[str, pathlib.Path]) -> str:
  """商品カテゴリを html ファイルのパスから取得する

  Args:
    html_path (Union[str, pathlib.Path]): html ファイルのパス

  Returns:
    商品カテゴリ
  """
  html_path = pathlib.Path(html_path).resolve()
  product_dir = html_path.parent
  categoty_dir = product_dir.parent
  category = categoty_dir.name
  return category      

def _extract_date(content: str) -> str:
  """日付情報を取得

  Args:
    content (str): html から取得した日付が書かれているテキスト

  Returns:
    YYYY/mm/DD 形式で日付を返す
  """
  date_text = DATE_REGEX.match(content)
  date = '{}/{}/{}'.format(date_text.group('year'),
                           date_text.group('month').zfill(2),
                           date_text.group('day').zfill(2))
  return date

STARS_INFO_DUST = '5つ星のうち'
def _extract_stars(content: str) -> float:
  """評価を取得

  Args:
    content (str): html から取得した評価が書かれているテキスト

  Returns:
    ☆評価
  """
  stars = float(content.replace(STARS_INFO_DUST, ''))
  return stars

VOTE_INFO_DUST = '人のお客様がこれが役に立ったと考えています'
def _extract_vote(content: str) -> int:
  """投票数を取得

  Args:
    content (str): html から取得した投票数が書かれているテキスト

  Returns:
    投票数(投票数が無ければ 0 を返す)
  """
  vote = 0
  if content:
    vote_text = content.text.strip()
    vote = int(vote_text.replace(VOTE_INFO_DUST, ''))

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
