import os
import json
import pandas
import re
import pathlib

from pprint import pprint
from collections import OrderedDict
from bs4 import BeautifulSoup

from .review import ReviewPageJSON, ReviewInfo, StarsDistribution
from .nlp import normalize
from .nlp import TFIDF


class HtmlConvertor:

  def __init__(self, code='utf-8', normalize_mode=False, top=5, mark=True):
    self.code           = code
    self.normalize_mode = normalize_mode
    self.top            = top
    self.mark           = mark

    self.TABLE_ID     = 'reviewTable'
    self.table_design = 'metro-dark'

    self._split_pat = re.compile(r'。+')

    # html5の宣言
    self.doc_type = tag('!DOCTYPE html')

    src_dir = pathlib.Path(__file__).resolve().parent
    # スタイルシートを埋め込む
    css_file = src_dir / 'css' / 'review_info_style.css'
    style_content = self._read_script(str(css_file))

    # <script>コンテンツの用意
    js_file = src_dir / 'js' / 'review_info_tablesorter.js'
    script_content = self._read_script(str(js_file))


    # jsonファイルに依存しない<head>コンテンツの用意
    head_content_list = [tag('meta', charset='UTF-8'),
                         tag('link',
                             rel="stylesheet",
                             id="tablesorter-css",
                             href="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/css/theme.{}.min.css?ver=4.9.8".format(self.table_design), 
                             type="text/css",
                             media="all"),
                         tag('script', 
                             '',
                             type='text/javascript',
                             src='https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js'),
                         tag('script',
                             '',
                             type='text/javascript',
                             src='https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/js/jquery.tablesorter.min.js'),
                         tag('script',
                             '',
                             type='text/javascript',
                             src='https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.31.0/js/jquery.tablesorter.widgets.min.js'),
                         tag('style', style_content),
                         tag('script', script_content)]
    self.head_content = head_content_list

  def convert(self, json_file) -> str:
    """jsonファイルを読み込み、htmlフォーマットに変換
    Params
      json_file:
        jsonファイルのパス

    Return: str
      jsonファイルの中身をhtmlフォーマットに変換したもの
      (BeautifulSoupによる整形済み)
    """

    data = ReviewPageJSON.load(json_file)

    # <head>コンテンツの用意
    product_name = data.product
    title = tag('title', product_name)
    head_content_list = [*self.head_content, title]
    head = self._arrange_content(head_content_list, 'head')

    # <h*>コンテンツの用意
    # category      = data[REVIEW_JSON_KEYS.category]
    link          = data.link
    maker         = data.maker
    average_stars = data.average_stars
    total_reviews = data.total_reviews
    real_reviews  = data.real_reviews

    reviews = data.reviews
    reviews_df = pandas.DataFrame(reviews)
    stars_dict = self._divide_by_stars(reviews_df)

    # 星評価の整理
    stars_distribution = data.stars_distribution
    h3_content_dict = OrderedDict()
    for k, v in stars_dict.items():
      h3_text = '{}：\t{}'.format(k, v)
      if v != stars_distribution[k]:
        h3_text = '{} / {}'.format(h3_text, stars_distribution[k])

      h3_content_dict[k] = h3_text

    h3_content_list = [tag('h3', v) for v in h3_content_dict.values()]

    review_num_text = 'レビュー数：{}'.format(real_reviews)
    if total_reviews != real_reviews:
      review_num_text = '{} / {}'.format(review_num_text, total_reviews)

    # <body>コンテンツの用意
    body_content_list = [tag('h1', product_name),
                         tag('h2', tag('a', '商品レビューページ', href=link)),
                         tag('h2', 'メーカー：{}'.format(maker)),
                         tag('h2', '評価：{}'.format(average_stars)),
                         tag('h2', review_num_text),*h3_content_list]

    # pprint(reviews)

    # TF-IDFの計算
    if self.mark:
      self._mark_top_words(reviews_df, reviews)

    # <table>コンテンツの用意
    thead = tag('thead', tag('tr', tag('th', *ReviewInfo._fields())))
    # テーブルの作成
    tbody_content_list = [self._create_table(review_info) for review_info in reviews]
    tbody = self._arrange_content(tbody_content_list, 'tbody')
    table_content_list = [thead, tbody]
    table = self._arrange_content(table_content_list,
                                  'table',
                                  cls='tablesorter tablesorter-{}'.format(self.table_design),
                                  id=self.TABLE_ID)

    # <body>コンテンツの再設定
    body_content_list.append(table)
    body = self._arrange_content(body_content_list, 'body')

    # <html>コンテンツの用意
    html_content_list = [head, body]
    html = self._arrange_content(html_content_list, 'html')
    html = self.doc_type + '\n' + html

    # BeautifulSoupで整形
    bs = BeautifulSoup(html, 'lxml')
    return bs.prettify()     


  def _read_script(self, script_file):
    with open(script_file, mode='r', encoding=self.code) as fp:
      content = '\n'.join(line.strip() for line in fp.readlines())

    return content.replace('TABLE_ID', self.TABLE_ID)


  def _arrange_content(self, content_list, tag_name, **attrs):
    content = '\n'.join(content_list)
    return tag(tag_name, content, **attrs)


  def _divide_by_stars(self, df):
    key_list = StarsDistribution._fields()
    key_dict = OrderedDict()
    for i, k in enumerate(key_list):
      key_dict[k] = float(i + 1)

    divided_dict = OrderedDict()
    for k, v in key_dict.items():
      divided_dict[k] = df.query('star == {}'.format(v))['star'].count()

    return divided_dict


  def _mark_top_words(self, reviews_df, reviews):
    review_key = ReviewInfo._fields()[-1]
    tfidf_computer = TFIDF()
    result_dict = tfidf_computer.compute(reviews_df[review_key].values.tolist())
    # pprint(tfidf_computer.alignment_dict)

    # pprint(result_dict)
    for idx, review_info in enumerate(reviews):
      review_text = ''
      result_df = result_dict[idx]
      # print(result_df)
      top_word_df = result_df.query('tfidf > 0').sort_values('tfidf', ascending=False)
      # print(idx)
      # pprint(top_word_df)

      top = int(len(top_word_df) * 0.1)
      if self.top > top:
        top = self.top

      top_words = top_word_df['word'].head(top).values.tolist()

      for s, w, is_token in tfidf_computer.alignment_dict[idx]:
        # pprint(tfidf_computer.correspond_words_dict[idx])
        if is_token and w in top_words:
          # word = tfidf_computer.correspond_words_dict[idx][w]
          review_text += tag('span', s, cls='marker')
                
        else:
          review_text += s

      reviews[idx] = ReviewInfo(review_info._replace(review=review_text))

  
  def _create_table(self, review_info: ReviewInfo) -> str:
    date, star, vote, name, title, review = review_info

    # レビュー文の処理
    # review = '。\n'.join(
    #     self.review_split_pattern_obj.split(review)
    # ).replace('\n\n', '\n').replace('\n', '<br>')
    review = review.replace('\n', '<br>')

    if self.normalize_mode:
      review = normalize(review)

    # 列要素を作成
    td_content_list = [tag('td', date),
                       tag('td', star),
                       tag('td', vote),
                       tag('td', name),
                       tag('td', title),
                       tag('td', review)]

    # 行要素を作成
    tr = self._arrange_content(td_content_list, 'tr')
    return tr


def tag(name, *content, cls=None, **attrs):
  if cls is not None:
    attrs['class'] = cls

  if attrs:
    attr_str = ''.join(' {}="{}"'.format(attr, value) 
                       for attr, value in sorted(attrs.items()))
  else:
    attr_str = ''

  if content:
    return '\n'.join('<{}{}>{}</{}>'.format(name, attr_str, c, name)
                     for c in content)

  else:
    return '<{}{}>'.format(name, attr_str)

