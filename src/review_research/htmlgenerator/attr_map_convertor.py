import os
import json
import argparse
import glob
import pathlib
from collections import OrderedDict, namedtuple
from pprint import pprint
from typing import Dict, Tuple, Union

from bs4 import BeautifulSoup

from review_research import STAR_CORRESPONDENCE_DICT
from review_research import ReviewTextInfoForMapping
from review_research import MappingResult
from review_research import SentenceMapper
from review_research.htmlgenerator import tag
from review_research.htmlgenerator import organize_contents
from review_research.htmlgenerator import read_script
from review_research.htmlgenerator import JS_DIR
from review_research.htmlgenerator import CSS_DIR
from review_research.nlp import normalize


ANCHOR_PROP = ['link_id', 'review_text_info_list']
AnchorProp  = namedtuple('AnchorProp', ANCHOR_PROP)

STAR_DISPLAY_DICT = {'star1': '★☆☆☆☆',
                     'star2': '★★☆☆☆',
                     'star3': '★★★☆☆',
                     'star4': '★★★★☆',
                     'star5': '★★★★★'}

JQUERY_JS = 'http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js'
DOC_TYPE = tag('!DOCTYPE html')

AnchorDict = Dict[str, Dict[str, AnchorProp]]
HeatmapDict = Dict[str, Dict[str, int]]
Attr2StarMap = Dict[str, Dict[str, Tuple[ReviewTextInfoForMapping, ...]]]

class AttrMapConvertor(object):
  """商品レビュー内の文を属性と星評価別に対応付けされた JSON ファイルを見やすいように html ファイルに変換"""

  def __init__(self, dic_dir: str):
    self.dic_dir = dic_dir
    self.__category = ''
    self._mapper = None

    js_file = JS_DIR / 'heatmap.js'
    css_file = CSS_DIR / 'heatmap.css'

    script_content = read_script(js_file)
    style_content  = read_script(css_file)

    meta_content = tag('meta', charset='UTF-8')
    jquery_script_content = tag('script', '', type='text/javascript', 
                                src=JQUERY_JS)
    js_script_content = tag('script', script_content, type='text/JavaScript')
    css_script_content = tag('style', style_content, type='text/css')
    self._head_contents = (meta_content,
                           jquery_script_content,
                           js_script_content,
                           css_script_content,)

  @property
  def category(self) -> str:
    return self.__category

  @category.setter
  def category(self, value: str):
    if self.category != value or not self.category:
      self.__category = value
      self._mapper = SentenceMapper(self.dic_dir, self.category)
      self._mapper.category = self.category
      self._setup_dictionary()

  def convert(self, map_jsonfile: Union[str, pathlib.Path]) -> str:
    """商品レビュー内の文を属性と星評価別に対応付けされた JSON ファイルを見やすいように html ファイルに変換

    Args:
      map_jsonfile (Union[str, pathlib.Path]): 対応付けの結果を格納した JSON ファイル

    Returns:
      html で記述されたテキスト
    """
    mapped_data = MappingResult.load(map_jsonfile)
    self.category = mapped_data.category

    # head コンテンツ
    product_name = mapped_data.product
    title = tag('title', product_name)
    head_content_list = [*self._head_contents, title]
    head = organize_contents(head_content_list, 'head')

    # body コンテンツ
    body = self._make_body_content(mapped_data)

    # html コンテンツ
    html_content_list = [head, body]
    html = organize_contents(html_content_list, 'html')
    html = DOC_TYPE + '\n' + html
    return html

  def _setup_dictionary(self):
    self._attr_ja2en = OrderedDict()
    for en, ja in self._mapper.en2ja.items():
      self._attr_ja2en[ja] = en

  def _make_body_content(self, mapped_data: MappingResult) -> str:
    """html の body タグを作成

    Args:
      mapped_data (MappingResult): 対応付けされた結果

    Returns:
      body タグ
    """
    body_content_list = []
    # h1コンテンツ
    h1_content = tag('h1', mapped_data.product)
    body_content_list.append(h1_content)

    # h2コンテンツ
    review_info_content = [
        tag('h2', 'レビュー情報'),
        tag('h3', tag('a', '商品レビューページ（Amazon）', href=mapped_data.link)),
        tag('h3', 'メーカー：{}'.format(mapped_data.maker)),
        tag('h3', '評価：{}'.format(mapped_data.average_stars)),
        tag('h3', 'レビュー数：{}'.format(mapped_data.total_review)),
        tag('h3', '総文数：{}'.format(mapped_data.total_text)),
    ]
    body_content_list.extend(review_info_content)

    # heatmapコンテンツ
    heatmap_content_list = [tag('h2', '属性別での文分布')]
    attr_to_star_map = mapped_data.mapping
    heatmap_dict, anchor_dict = self._reorganize_mapped_data(attr_to_star_map)
    heatmap_table = self._create_heatmap_table(heatmap_dict, anchor_dict)
    heatmap_content_list.append(heatmap_table)
    body_content_list.extend(heatmap_content_list)

    # 属性別のレビュー列挙
    enum_content_list = self._itemize_text_by_attr_and_star(attr_to_star_map,
                                                            anchor_dict)
    body_content_list.extend(enum_content_list)

    # bodyコンテンツ
    body = organize_contents(body_content_list, 'body')
    return body

  def _reorganize_mapped_data(
      self, mapping: Attr2StarMap) -> Tuple[HeatmapDict, AnchorDict]:
    """対応付けされたデータを改めて整理する

    Args:
      mapping (Attr2StarMap): 属性と星評価別にレビュー文中の文をまとめた辞書

    Returns:
      ヒートマップ作成用の辞書と、リンク内ジャンプ用の辞書
    """
    anchor_fmt = '{}-{}'
    heatmap_dict = OrderedDict()
    anchor_dict = OrderedDict()
    for en_attr, star_to_texts in mapping.items():
      attr = self._mapper.en2ja[en_attr]
      star_to_num_texts = OrderedDict()
      anchor_prop_dict = OrderedDict()
      for star_str, review_text_info_list in star_to_texts.items():
        star_to_num_texts[star_str] = len(review_text_info_list)
        anchor = anchor_fmt.format(en_attr, star_str)
        anchor_prop_dict[star_str] = AnchorProp(anchor, review_text_info_list)

      heatmap_dict[attr] = star_to_num_texts
      anchor_dict[attr] = anchor_prop_dict
    
    return (heatmap_dict, anchor_dict)

  def _create_heatmap_table(
      self, heatmap_dict: HeatmapDict, anchor_dict: AnchorDict
  ) -> str:
    """属性と星評価別にレビュー文中の文数をヒートマップにして可視化したものを table タグで作成

    Args:
      heatmap_dict (HeatmapDict): 属性と星評価別にレビュー文中の文数をまとめた辞書
      anchor_dict (AnchorDict): 属性と星評価別にレビュー文の情報をまとめたリストとアンカーを格納した辞書

    Returns:
      ヒートマップを実装した table タグ
    """
    tr_content_list = [tag('th', '属性', class_='first')]
    star_strs = tuple(STAR_DISPLAY_DICT[star_str] 
                      for star_str in STAR_CORRESPONDENCE_DICT.values())
    tr_content_list.extend([tag('th', star_str) 
                            for star_str in star_strs[:-1]])
    tr_content_list.append(tag('th', star_strs[-1], class_='last'))
    tr = organize_contents(tr_content_list, 'tr')
    thead = tag('thead', tr)

    jump_fmt = '#{}'
    tbody_content_list = []
    for attr in heatmap_dict:
      if attr != "その他":
        attr_anchor = tag('a', attr, 
                          href=jump_fmt.format(self._attr_ja2en[attr]))
        td_header = tag('td', attr_anchor, class_='stats-title')
        td_content_list = [td_header]
        num_texts_and_anchor_props = zip(heatmap_dict[attr].values(),
                                         anchor_dict[attr].values())
        for num_texts, anchor_prop in num_texts_and_anchor_props:
          anchor = tag('a', num_texts, 
                       href=jump_fmt.format(anchor_prop.link_id))
          td_content = tag('td', anchor)
          td_content_list.append(td_content)
        
        tr = organize_contents(td_content_list, 'tr', class_='stats-row')
        tbody_content_list.append(tr)

    tbody = organize_contents(tbody_content_list, 'tbody')
    table = organize_contents(
        [thead, tbody], 'table', class_='heat-map', cellpadding='0',
        cellspacing='0', border='0', id='heat-map-3')
    return table
                  
  def _itemize_text_by_attr_and_star(
      self, attr_to_star_map: Attr2StarMap, anchor_dict: AnchorDict
  ) -> Tuple[str, ...]:
    """属性と星評価別にレビュー文中の文を列挙する

    Args:
      attr_to_star_map (Attr2StarMap): 属性と星評価別にレビュー文中の文を格納した辞書
      anchor_dict (AnchorDict): 属性と星評価別にレビュー文の情報をまとめたリストとアンカーを格納した辞書

    Returns:
      列挙された文一覧
    """
    display_fmt = '{}：{}'
    enum_content_list = list()
    for en_attr in attr_to_star_map:
      attr = self._mapper.en2ja[en_attr]
      enum_content_list.append(tag('h2', attr, id=en_attr))
      for star_str, anchor_prop in anchor_dict[attr].items():
        link_id, review_text_info_list = anchor_prop
        star_disp = STAR_DISPLAY_DICT[star_str]
        enum_content_list.append(
            tag('h3', display_fmt.format(attr, star_disp), id=link_id))
        if review_text_info_list:
          li_content_list = list()
          for review_text_info in review_text_info_list:
            text = review_text_info.text
            summary = tag('summary', text)
            review = normalize(review_text_info.review)
            marked_text = tag('span', text, class_='sentence-marker')
            marked_review = review.replace(text, marked_text)
            details_content_list = [
                summary, marked_review.replace('\n', '<br>')
            ]
            details = organize_contents(details_content_list, 'details')
            li_content_list.append(tag('li', details))

          ul = organize_contents(li_content_list, 'ul')
          enum_content_list.append(ul)

    return tuple(enum_content_list)