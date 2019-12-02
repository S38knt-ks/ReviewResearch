import argparse
import os
import glob
import pathlib
from collections import namedtuple
from typing import Union, List

import pandas
from tqdm import tqdm
import bs4
from bs4 import BeautifulSoup

DETAIL_CSV_HEADER = tuple(['review_num', 'star', 'link'])
DetailData = namedtuple('DetailData', DETAIL_CSV_HEADER)

# class タグの文字列は次のようになる
# 's-result-item s-result-card-for-container-noborder s-carded-grid celwidget '
ITEM_INFO_PATTERN_ARGS1 = {
    'name': 'li',
    'attrs': {
        'class': ('s-result-item s-result-card-for-container-noborder'
                  ' s-carded-grid celwidget ')
    }
}

ITEM_INFO_PATTERN_ARGS2 = {
    'name': 'li',
    'attrs': {'class': 's-result-item celwidget '}
}

NUM_REVIEWS_PATTERN_ARGS = {
    'name': 'a',
    'attrs': {'class': 'a-size-small a-link-normal a-text-normal'}
}

STAR_PATTERN_ARGS = {
    'name': 'a', 
    'attrs': {'class': 'a-popover-trigger a-declarative'}
}

# class タグの文字列は以下のようになる
# 'a-link-normal s-access-detail-page s-color-twister-title-link a-text-normal'
LINK_PATTERN_ARGS = {
    'name': 'a', 
    'attrs': {
        'class': ('a-link-normal s-access-detail-page'
                  ' s-color-twister-title-link a-text-normal')
    }
}

def get_items(html: Union[str, pathlib.Path]) -> bs4.element.ResultSet:
  """商品一覧の html ファイルから商品情報に関する html タグを抽出する

  Args:
    html (Union[str, pathlib.Path]): html ファイルへのパス

  Returns:
    商品情報に関する html タグ一覧
  """
  html = pathlib.Path(html)
  bs = BeautifulSoup(html.open(mode='r', encoding='utf-8'), 'lxml')
  items = bs.findAll(**ITEM_INFO_PATTERN_ARGS1)

  return items if items else bs.findAll(**ITEM_INFO_PATTERN_ARGS2)


def extract_detail(item: bs4.element.Tag) -> DetailData:
  """商品に関するデータを抽出する

  Args:
    item (bs4.element.Tag): 商品情報

  Returns:
    商品に関するデータ
  """
  item_review_num = item.findAll(**NUM_REVIEWS_PATTERN_ARGS)
  if len(item_review_num) == 1:
    item_review_num = item_review_num[0].text.strip()

  else:
    item_review_num = [ir for ir in item_review_num 
                       if ir.text.strip().isdecimal()]
    item_review_num = item_review_num[0].text.strip()

  item_star = item.findAll(**STAR_PATTERN_ARGS)
  if len(item_star) == 1:
    item_star = item_star[0].text.strip()

  else:
    item_star = item_star[-1].text.strip()

  item_review_num = int(item_review_num.replace(',', ''))
  item_star = item_star.split(' ')[-1]
  item_link = item.find(**LINK_PATTERN_ARGS).get('href')
  return DetailData(item_review_num, item_star, item_link)


def main(args):
  category_dir = pathlib.Path(args.category_dir)
  html_list = glob.glob('{}/*.html'.format(category_dir))

  print('extracting data...')
  html_list = tqdm(html_list, ascii=True)
  detail_list = [extract_detail(item) for html in html_list
                                      for item in get_items(html)]
  except_link = 'https://www.amazon.co.jp/gp/slredirect/picassoRedirect.html'
  detail_list = [detail for detail in detail_list 
                 if not except_link in detail.link]
  print('done')

  category_name = category_dir.name
  outdir = pathlib.Path(args.out_dir)
  outdir = outdir / category_name
  if not outdir.exists():
    outdir.mkdir(parents=True)

  out_file = outdir / '{}_detail.csv'.format(category_name)
  print('saving data...')
  detail_df = pandas.DataFrame(detail_list)
  detail_df.to_csv(out_file, encoding='utf-8', index=False)
  print('done')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('category_dir',
                      help=('ある商品カテゴリの商品一覧ページの'
                            ' html ファイルが保存されているフォルダ'))
  parser.add_argument('out_dir',
                      help='出力先ディレクトリ')
  main(parser.parse_args())
