import os
import json
import pandas
import re
import pathlib
from typing import Tuple, Any, Dict, Union

from pprint import pprint
from collections import OrderedDict
from bs4 import BeautifulSoup

from review_research.review import ReviewPageJSON, ReviewInfo, StarsDistribution
from review_research.nlp import normalize
from review_research.nlp import TFIDF
from review_research.htmlgenerator import CSS_DIR
from review_research.htmlgenerator import JS_DIR
from review_research.htmlgenerator import tag
from review_research.htmlgenerator import organize_contents
from review_research.htmlgenerator import read_script

# 展開すると https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/css/theme.metro-dark.min.css?ver=4.9.8
TABLESORTER_CSS = ('https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/'
                  '2.31.0/css/theme.metro-dark.min.css?ver=4.9.8')
JQUERY_JS = 'https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js'
# 展開すると https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/js/jquery.tablesorter.min.js
TABLESORTER_JS1 = ('https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/'
                   '2.31.0/js/jquery.tablesorter.min.js')
# 展開すると 'https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/js/jquery.tablesorter.widgets.min.js'
TABLESORTER_JS2 = ('https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/'
                   '2.31.0/js/jquery.tablesorter.widgets.min.js')

OLD_AND_NEW = ('TABLE_ID', 'reviewTable')
TABLE_DESIGN = 'metro-dark'
DOC_TYPE = tag('!DOCTYPE html')  # html5の宣言

class ReviewDataConvertor(object):
  """review.json ファイルの中身を見やすいように html ファイルに変換する
  
  Attributes:
    normalize_mode (bool): レビュー文を正規化する場合は True, そうでない場合は False
  """

  def __init__(self, normalize_mode: bool = False):
    self.normalize_mode = normalize_mode

    # スタイルシートを埋め込む
    css_file = CSS_DIR / 'review_info_style.css'
    style_content = read_script(css_file, OLD_AND_NEW)
    # <script>コンテンツの用意
    js_file = JS_DIR / 'review_info_tablesorter.js'
    script_content = read_script(js_file, OLD_AND_NEW)
    # jsonファイルに依存しない<head>コンテンツの用意
    head_content_list = [
        tag('meta', charset='UTF-8'),
        tag('link', rel='stylesheet', id="tablesorter-css",
            href=TABLESORTER_CSS, type="text/css", media="all"),
        tag('script', '', type='text/javascript', src=JQUERY_JS),
        tag('script', '', type='text/javascript', src=TABLESORTER_JS1),
        tag('script', '', type='text/javascript', src=TABLESORTER_JS2),
        tag('style', style_content),
        tag('script', script_content),
    ]
    self.head_contents = tuple(head_content_list)

  def __call__(self, reviewjson: Union[str, pathlib.Path]) -> str:
    return self.convert(reviewjson)

  def convert(self, reviewjson: Union[str, pathlib.Path]) -> str:
    """jsonファイルを読み込み、htmlフォーマットに変換

    Args:
      reviewjson (Union[str, pathlib.Path]): jsonファイルのパス

    Returns:
      JSON ファイルの中身を html に変換したもの(BeautifulSoup による整形済み)
    """
    reviewdata = ReviewPageJSON.load(reviewjson)
    head = self._make_head_content(reviewdata.product)
    body = self._convert_review_data_to_body_content(reviewdata)
    html = organize_contents((head, body), 'html')
    html = DOC_TYPE + '\n' + html

    # BeautifulSoupで整形
    bs = BeautifulSoup(html, 'lxml')
    return bs.prettify()

  def _make_head_content(self, product_name: str) -> str:
    """head コンテンツの作成"""
    title = tag('title', product_name)
    head_content_list = [*self.head_contents, title]
    head = organize_contents(head_content_list, 'head')
    return head

  def _convert_review_data_to_body_content(
      self, reviewdata: ReviewPageJSON) -> str:
    """レビューデータを html の body 要素に変換する

    Args:
      reviewdata (ReviewPageJSON): Amazon レビューデータ

    Returns:
      body タグで囲まれたテキスト
    """
    real_reviews  = reviewdata.real_reviews
    num_reviews_text = 'レビュー数：{}'.format(real_reviews)
    total_reviews = reviewdata.total_reviews
    if total_reviews != real_reviews:
      num_reviews_text = '{} / {}'.format(num_reviews_text, total_reviews)

    reviews = reviewdata.reviews
    h3_content_list = _make_stars_texts(reviews, reviewdata.stars_distribution)
    # <body>コンテンツの用意
    body_content_list = [
        tag('h1', reviewdata.product),
        tag('h2', tag('a', '商品レビューページ', href=reviewdata.link)),
        tag('h2', 'メーカー：{}'.format(reviewdata.maker)),
        tag('h2', '評価：{}'.format(reviewdata.average_stars)),
        tag('h2', num_reviews_text),
        *h3_content_list,
    ]

    # <table>コンテンツの用意
    table = self._create_table(reviews)

    # <body>コンテンツの再設定
    body_content_list.append(table)
    body = organize_contents(body_content_list, 'body')
    return body

  
  def _create_table(self, reviews: Tuple[ReviewInfo, ...]) -> str:
    """レビュー情報一覧から table 要素を作成する

    Args:
      reviews (Tuple[ReviewInfo, ...]): レビュー情報一覧

    Returns:
      table タグで囲まれたテキスト
    """
    thead = tag('thead', tag('tr', tag('th', *ReviewInfo._fields)))
    tr_content_list = list()
    for review_info in reviews:
      # レビュー文の処理
      review = review_info.review.replace('\n', '<br>')
      review_info = review_info._replace(review=review)

      if self.normalize_mode:
        review = normalize(review)

      # 列要素を作成
      td_content_list = [tag('td', info) for info in review_info]

      # 行要素を作成
      tr = organize_contents(td_content_list, 'tr')
      tr_content_list.append(tr)

    tbody = organize_contents(tr_content_list, 'tbody')
    table_content_list = [thead, tbody]
    table = organize_contents(
        table_content_list, 'table',
        class_='tablesorter tablesorter-{}'.format(TABLE_DESIGN),
        id=OLD_AND_NEW[1]
    )
    return table

## ヘルパー関数 
def _make_stars_texts(reviews: Tuple[ReviewInfo, ...],
                      stars_dist: StarsDistribution) -> Tuple[str, ...]:
  """星評価に関する表示テキストを作成する

  Args:
    reviews (Tuple[ReviewInfo, ...]): レビュー情報一覧
    stars_dist (StarsDistribution): 星評価分布

  Returns:
    星の数ごとの h3 要素一覧
  """
  # 星評価の整理
  reviews_df = pandas.DataFrame(reviews)
  key_dict = OrderedDict()
  for i, num_stars_field in enumerate(StarsDistribution._fields):
    key_dict[num_stars_field] = float(i + 1)

  divided_dict = OrderedDict()
  eval_star_query_fmt = 'star == {}'
  for num_stars_field, eval_star in key_dict.items():
    eval_star_query = eval_star_query_fmt.format(eval_star)
    num_stars_df = reviews_df.query(eval_star_query)['star']
    divided_dict[num_stars_field] = num_stars_df.count()

  star_to_text = OrderedDict()
  for num_stars_field, star_count in divided_dict.items():
    star_text = '{}：\t{}'.format(num_stars_field, star_count)
    num_stars = getattr(stars_dist, num_stars_field)
    if star_count != num_stars:  # レビューの数が元のものと異なると元の星評価の数も異なる
      star_text = '{} / {}'.format(star_text, num_stars)

    star_to_text[num_stars_field] = star_text

  star_texts = [tag('h3', v) for v in star_to_text.values()]
  return star_texts