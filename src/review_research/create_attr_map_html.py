import os
import json
import argparse
import glob
from pathlib import Path
from collections import OrderedDict, namedtuple
from pprint import pprint

from bs4 import BeautifulSoup

from . import SentenceMapper, STAR_CORRESPONDENCE_DICT
from review_research import tag
from .nlp import normalize


def arrange_content(content_list, tag_name, **attrs):
  content = '\n'.join(content_list)
  return tag(tag_name, content, **attrs)


ANCHOR_PROP = ['link_id', 'sentence_info_list']
AnchorProp  = namedtuple('AnchorProp', ANCHOR_PROP)

STAR_DISPLAY_DICT = {'star1': '★☆☆☆☆',
                     'star2': '★★☆☆☆',
                     'star3': '★★★☆☆',
                     'star4': '★★★★☆',
                     'star5': '★★★★★'}

class AttrMapHtmlCreator:

  def __init__(self, dic_dir: str, category: str, js_file: str, css_file: str, code='utf-8'):
    self._code = code

    self._mapper = SentenceMapper(dic_dir)
    self._mapper.category = category

    self._ja_to_en_dict = OrderedDict()
    for en, ja in self._mapper.en2ja.items():
      self._ja_to_en_dict[ja] = en

    print('<en2ja>')
    pprint(self._mapper.en2ja)
    print()

    self._doc_type = tag('!DOCTYPE html')

    script_content = self._read_script(js_file)
    style_content  = self._read_script(css_file)

    meta_content = tag('meta', charset=str.upper(code))
    jquery_script_content = tag('script', '', 
                                type='text/javascript', 
                                src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js")
    js_script_content = tag('script', script_content, 
                            type='text/JavaScript')
    css_script_content = tag('style', style_content, 
                             type='text/css')
    self._head_contents = [meta_content,
                           jquery_script_content,
                           js_script_content,
                           css_script_content]

  @property
  def code(self) -> str:
    return self._code

  def create(self, json_file: str):
    map_data = json.load(open(json_file, mode='r', encoding=self.code),
                         object_pairs_hook=OrderedDict)

    # headコンテンツ
    product_name = map_data['product']
    title        = tag('title', product_name)

    head_content_list = [*self._head_contents, title]
    head = arrange_content(head_content_list, 'head')

    body_content_list = []

    # h1コンテンツ
    h1_content = tag('h1', product_name)
    body_content_list.append(h1_content)

    # h2コンテンツ
    review_info_head = tag('h2', 'レビュー情報')
    link           = map_data['link']
    maker          = map_data['maker']
    average_stars  = map_data['average_stars']
    total_review   = map_data['total_review']
    total_sentence = map_data['total_sentence']

    review_info_content = [
        review_info_head,
        tag('h3', tag('a', '商品レビューページ（Amazon）', href=link)),
        tag('h3', 'メーカー：{}'.format(maker)),
        tag('h3', '評価：{}'.format(average_stars)),
        tag('h3', 'レビュー数：{}'.format(total_review)),
        tag('h3', '総文数：{}'.format(total_sentence))]

    body_content_list.extend(review_info_content)

    # heatmapコンテンツ
    heatmap_content_list = [tag('h2', '属性別での文分布')]
    sentence_info_dict = map_data['map']

    map_dict = OrderedDict()
    sentence_map_dict = OrderedDict()
    anchor_dict = OrderedDict()
    for en_attr, star_dict in sentence_info_dict.items():
      attr = self._mapper.en2ja[en_attr]
      sentence_map_dict[attr] = star_dict

      star_map_dict    = OrderedDict()
      anchor_prop_dict = OrderedDict()
      for star_str, sentence_info_list in star_dict.items():
        star_map_dict[star_str] = len(sentence_info_list)
        anchor = '{}-{}'.format(en_attr, star_str)
        anchor_prop_dict[star_str] = AnchorProp(anchor, sentence_info_list)

      map_dict[attr]    = star_map_dict
      anchor_dict[attr] = anchor_prop_dict

    heatmap_content_list.append(self._create_heatmap_table(map_dict, anchor_dict))
    body_content_list.extend(heatmap_content_list)

    # 属性別のレビュー列挙
    enum_content_list = self._enum_sentences(sentence_info_dict, anchor_dict)
    body_content_list.extend(enum_content_list)

    # bodyコンテンツ
    body = arrange_content(body_content_list, 'body')

    # htmlコンテンツ
    html_content_list = [head, body]
    html = arrange_content(html_content_list, 'html')
    html = self._doc_type + '\n' + html

    # bsで整形して出力
    # bs = BeautifulSoup(html, 'lxml')
    # return bs.prettify()
    return html

  def _read_script(self, fpath: str) -> str:
    with open(fpath, mode='r', encoding=self.code) as fp:
      content = ''.join(line for line in fp.readlines())

    return content

  def _create_heatmap_table(self, map_dict: OrderedDict, anchor_dict: OrderedDict):
    tr_content_list = [tag('th', '属性', cls='first')]
    values = [STAR_DISPLAY_DICT[star_str] for star_str in STAR_CORRESPONDENCE_DICT.values()]
    tr_content_list.extend([tag('th', star_str) for star_str in values[:-1]])
    tr_content_list.append(tag('th', values[-1], cls='last'))
    tr = arrange_content(tr_content_list, 'tr')
    thead = tag('thead', tr)

    jump_fmt = '#{}'
    tbody_content_list = []
    for attr in map_dict:
      if attr != "その他":
        td_header = tag('td', 
                        tag('a', attr, 
                            href=jump_fmt.format(self._ja_to_en_dict[attr])),
                        cls='stats-title')
        tr_content_list = [td_header]
        sentences_and_anchors = zip(map_dict[attr].values(),
                                    anchor_dict[attr].values())
        for sentence_num, anchor_prop in sentences_and_anchors:
          td_content = tag('td', 
                           tag('a', sentence_num, 
                               href=jump_fmt.format(anchor_prop.link_id)))
          tr_content_list.append(td_content)
        
        tr = arrange_content(tr_content_list, 'tr', cls='stats-row')
        tbody_content_list.append(tr)

    tbody = arrange_content(tbody_content_list, 'tbody')
    table_content_list = [thead, tbody]
    table = arrange_content(table_content_list, 'table',
                            cls='heat-map', cellpadding='0', cellspacing='0',
                            border='0', id='heat-map-3')
    return table
                  


  def _enum_sentences(self, sentence_info_dict: OrderedDict, anchor_dict: OrderedDict) -> list:        
    enum_content_list = []
    for en_attr in sentence_info_dict.keys():
      attr = self._mapper.en2ja[en_attr]
      enum_content_list.append(tag('h2', attr, id=en_attr))
      for star_str, anchor_prop in anchor_dict[attr].items():
        link_id, sentence_info_list = anchor_prop
        star_disp = STAR_DISPLAY_DICT[star_str]
        enum_content_list.append(tag('h3', '{}：{}'.format(attr, star_disp), id=link_id))
        if sentence_info_list:
          ul_content_list = []
          for sentence_info in sentence_info_list:
            sentence = sentence_info['sentence']
            summary = tag('summary', sentence)

            review = normalize(sentence_info['review'])
            marked_review = review.replace(sentence, tag('span', sentence, cls='sentence-marker'))
            details_content_list = [summary, marked_review.replace('\n', '<br>')]
            details = arrange_content(details_content_list, 'details')

            ul_content_list.append(tag('li', details))

          ul = arrange_content(ul_content_list, 'ul')
          enum_content_list.append(ul)

    return enum_content_list
              

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('dic_dir')
  args = parser.parse_args()

  input_dir = args.input_dir
  category = os.path.basename(input_dir)
  
  dic_dir = args.dic_dir

  src_dir = Path(__file__).resolve().parent.parent
  js_file  = src_dir / 'js' / 'heatmap.js'
  css_file = src_dir / 'css' / 'heatmap.css'

  creator = AttrMapHtmlCreator(dic_dir, category, str(js_file), str(css_file))

  all_files = glob.glob('{}\\**'.format(input_dir), recursive=True)
  all_filepaths = [Path(f) for f in all_files]
  map_json_list = [path for path in all_filepaths
                   if path.suffix == '.json' and path.name.startswith('map_')]
  for map_json in map_json_list:
    html = creator.create(map_json)
    f_name = map_json.stem
    out_dir = map_json.parent
    out_file = out_dir / 'detail_{}.html'.format(f_name)

    with out_file.open(mode='w', encoding=creator.code) as fp:
      fp.write(html)

  