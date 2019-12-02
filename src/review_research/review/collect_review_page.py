import argparse
import os
import urllib.request
import urllib.parse
import time
import random
import glob
import math
from pprint import pprint
from collections import OrderedDict, namedtuple
from typing import List, Union, Tuple, Dict, NoReturn

import pandas
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..review import DetailData

# レビューページフォーマットは以下のようになる
# 'ref=cm_cr_getr_d_paging_btm_{0}?ie=UTF8&reviewerType=all_reviews&pageNumber={0}'
REVIEW_PAGE_FMT = ('ref=cm_cr_getr_d_paging_btm_{0}'
                   '?ie=UTF8&reviewerType=all_reviews&pageNumber={0}')

ProductReviewURL = namedtuple('ProductReviewURL', ['review_num', 'url'])

def load_csv(csv_file: str) -> List[Tuple[int, str]]:
  """商品に関する情報のうち必要な情報を取り出す

  Args:
    csv_file (str): 商品レビューを抽出したい商品一覧が記述されているcsvファイル

  Returns:
    レビュー数と商品ページへのURLの一覧
  """
  df = pandas.read_csv(csv_file)
  header = DetailData(*df.columns.values.tolist())
  review_num, link = header.review_num, header.link
  return df[[review_num, link]].values.tolist()

def make_review_url(
    url_list: List[Tuple[int, str]]) -> Dict[str, ProductReviewURL]:
  """商品情報一覧から、商品名とそのページへのURLを対応させる

  Args:
    url_list (List[Tuple[int, str]]): 商品情報一覧

  Returns:
    商品名とそのページへのURLを対応させた辞書
  """
  url_category = '/product-reviews/'
  url_dict = OrderedDict()

  for review_num, link in url_list:
    review_url = '{}/{}'.format(link.replace('/dp/', url_category),
                                REVIEW_PAGE_FMT)
    product = urllib.parse.unquote(link.split('/')[3])
    url_dict[product] = ProductReviewURL(review_num, review_url)

  return url_dict

def calc_last_page(num_reviews: int) -> int:
  """商品レビューページの最後のページ番号を計算する

  Args:
    num_reviews (int): レビュー数

  Returns:
    最後のページ番号
  """
  if num_reviews > 10:
    return math.ceil(num_reviews / 10.0)

  return 1

def get_current_page(product_dir: str) -> int:
  """現在保存されているレビューページ数を取得する

  Args:
    product_dir (str): 商品レビューを保存するディレクトリ

  Returns:
    現在保存されているレビューページ数
  """
  return len(glob.glob('{}/*.html'.format(product_dir)))

  
def request_url(url: str, page: int) -> BeautifulSoup:
  """指定された URL とページ番号から対応する商品レビューページを取得し、
  そのレビューページのコンテンツを取得する

  Args:
    url (str): 商品レビューページの URL フォーマット
    page (int): ページ番号

  Returns:
    商品レビューページのコンテンツ
  """
  url = url.format(page)
  html = urllib.request.urlopen(url).read()
  bs = BeautifulSoup(html, 'lxml')
  return bs


def save_html(out_dir: str, page: int, 
              digit: int, html_content: str) -> NoReturn:
  """読み取った商品レビュー html を保存する

  Args:
    outdir (str): 保存先ディレクトリ
    page (int): ページ番号
    digit (int): ページ番号の桁数
    html_content (str): 商品レビューの html
  """
  out_file = '{}/page_{}.html'.format(out_dir, str(page).zfill(digit))
  with open(out_file, mode='w', encoding='utf-8') as fp:
    fp.write(html_content)


def main(args):
  csv_file = args.sample_csv
  url_dict = make_review_url(load_csv(csv_file))

  in_dir = '/'.join(csv_file.split('\\')[:-1])
  page_fmt = '{0:{1}} / {2:{1}}'
  display_fmt = '[page]\t{}\t[interval]\t{}'
  for product, product_review_url in tqdm(url_dict.items(), ascii=True):
    review_num, url = product_review_url
    last_page = calc_last_page(review_num)
    out_dir = '{}/{}'.format(in_dir, product)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    page  = get_current_page(out_dir) + 1
    digit = len(str(last_page))
    if page > last_page:
        continue
    
    tqdm.write('[product]\t{}'.format(product)) 
    interval = random.randint(7500, 12500) / 1000.0
    time.sleep(interval)
    
    bs = request_url(url, page)
    save_html(out_dir, page, digit, bs.prettify())
    page = page_fmt.format(page, digit, last_page)
    tqdm.write(display_fmt.format(page, interval))

    if page != last_page:
      for i in range(page+1, last_page+1):
        interval = random.randint(10000, 20000) / 1000.0
        time.sleep(interval)
        bs = request_url(url, i)
        save_html(out_dir, i, digit, bs.prettify())
        page = page_fmt.format(i, digit, last_page)
        tqdm.write(display_fmt.format(page, interval))



if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('sample_csv',
                      help=('商品レビューを抽出したい商品一覧が'
                            '記述されているcsvファイル'))

  main(parser.parse_args())
