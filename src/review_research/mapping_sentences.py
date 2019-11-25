import argparse
import json
import os
import pathlib
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint

import pandas
import seaborn
import numpy as np
import matplotlib.pyplot as plt

from .nlp import AttributionExtractor, WORD_SEPARATOR

OTHER_EN_ATTR = 'other'
OTHER_JA_ATTR = 'その他'

STAR_CORRESPONDENCE_DICT = {1.0: 'star1',
                            2.0: 'star2',
                            3.0: 'star3',
                            4.0: 'star4',
                            5.0: 'star5'}

SENTENCE_TEMP_INFO_FIELD = ['review',
                            'sentence',
                            'candidate_terms',
                            'hit_terms',
                            'cooccurrence_words',
                            'phrases',
                            'phrase_link_num',
                            'link_length']
SentenceTempInfo = namedtuple('SentenceTempInfo', SENTENCE_TEMP_INFO_FIELD)

SENTENCE_INFO_FIELD = [*SENTENCE_TEMP_INFO_FIELD, 'score', 'score_detail']
SentenceInfo = namedtuple('SentenceInfo', SENTENCE_INFO_FIELD)

class SentenceMapper:

  def __init__(self, dic_dir: str, code='utf-8'):
    self._code = code
    self._extractor = AttributionExtractor(dic_dir)

  @property
  def category(self):
    return self.__category

  @category.setter
  def categoty(self, category):
    if self.category != category:
      self._extractor.category = category
      self._build_translator()
      self.__category = category

  def _build_translator(self):
    self._en2ja = self._extractor.en2ja
    self._en2ja[OTHER_EN_ATTR] = OTHER_JA_ATTR
    self._ja2en = self._extractor.ja2en
    self._ja2en[OTHER_JA_ATTR] = OTHER_EN_ATTR

  @property
  def attrdict(self) -> dict:
    return self._extractor.attrdict

  @property
  def en2ja(self) -> dict:
    return self._en2ja

  @property
  def ja2en(self) -> dict:
    return self._ja2en

  @property
  def code(self) -> str:
    return self._code

  def create_map(self, pred_json: str) -> OrderedDict:
    pred_data = self._read_prediction_json(pred_json)
    sentences = pred_data['sentences']

    attr_map = OrderedDict()
    co_occurrence_dict = OrderedDict()
    for attr in self.en2ja:
      attr_map[attr] = self._make_star_dict()
      co_occurrence_dict[attr] = defaultdict(int)

    attr_map[OTHER_EN_ATTR] = self._make_star_dict()    
    for sentence_prop in sentences:
      star = sentence_prop['star']
      star_str = STAR_CORRESPONDENCE_DICT[star]

      review   = sentence_prop['review']
      sentence = sentence_prop['sentence']

      result_dict = sentence_prop['result']
      if result_dict:
        for attr, extraction_detail_list in result_dict.items():                    
          cooccurrence_words = []
          phrases = []
          candidate_terms = []
          hit_terms = []
          for ed in extraction_detail_list:
            # cooccurrence_words.extend(ed['cooccurrence_words'].split(AttributionExtractor.WORD_SEPARATOR))
            _phrases = ed['phrases'].split(WORD_SEPARATOR)
            phrases.extend(_phrases)
            candidate_terms.extend(ed['candidate_terms'].split(WORD_SEPARATOR))
            cooccurrence_words.extend(
                [w for w in ed['cooccurrence_words'].split(WORD_SEPARATOR)
                  if not self._extractor._analyzer._a_hiragana_pat.match(w)]
            )
            hit_terms.extend(ed['hit_terms'].split(WORD_SEPARATOR))

          cooccurrence_words = sorted(set(cooccurrence_words), key=cooccurrence_words.index)
          candidate_terms = sorted(set(candidate_terms), key=candidate_terms.index)
          hit_terms = sorted(set(hit_terms), key=hit_terms.index)
          link_length = len(sorted(set(phrases), key=phrases.index))
          for word in cooccurrence_words:
            co_occurrence_dict[attr][word] += 1

          cooccurrence_word = WORD_SEPARATOR.join(cooccurrence_words) if len(cooccurrence_words) > 0 else ''
          candidate_terms = WORD_SEPARATOR.join(candidate_terms)
          hit_terms = WORD_SEPARATOR.join(hit_terms)
          
          phrases = WORD_SEPARATOR.join(phrases)
          sentence_info = SentenceTempInfo(review, sentence, candidate_terms, hit_terms,  cooccurrence_word, phrases, len(extraction_detail_list), link_length)                  
          attr_map[attr][star_str].append(sentence_info)

      else:
        sentence_info = SentenceInfo(review, sentence, '', '', '', '', 1, 0, 0, '')
        attr_map[OTHER_EN_ATTR][star_str].append(sentence_info)

    scored_attr_map = OrderedDict()
    for attr, star_dict in attr_map.items():
      if attr != OTHER_EN_ATTR:
        scored_attr_map[attr] = self._make_star_dict()
        for star_str, sentence_temp_info_list in star_dict.items():
          sentence_info_list = []
          for sentence_temp_info in sentence_temp_info_list:
            link_length = sentence_temp_info.link_length
            cooccurrence_words = sentence_temp_info.cooccurrence_words.split(WORD_SEPARATOR)
            # phrases = sentence_temp_info.phrases.split(WORD_SEPARATOR)
            counted_words = []
            for word in cooccurrence_words:
                val = co_occurrence_dict[attr][word]
                counted_words.append('{}={}'.format(word, val))

            score = link_length
            counted_words = ', '.join(counted_words)
            # print(attr)
            # print(sentence_temp_info)

            sentence_info = SentenceInfo(*sentence_temp_info, score, counted_words)
            sentence_info_list.append(sentence_info)

          scored_attr_map[attr][star_str] = sentence_info_list

      else:
        scored_attr_map[attr] = star_dict

    sorted_attr_map = OrderedDict()
    result_dict = OrderedDict()
    result_dict['product'] = pred_data['product']
    result_dict['link']    = pred_data['link']
    result_dict['maker']   = pred_data['maker']
    result_dict['average_stars']     = pred_data['average_stars']
    result_dict['star_distribution'] = pred_data['star_distribuition']
    result_dict['total_review']   = pred_data['total_review']
    result_dict['total_sentence'] = pred_data['total_sentence']
    for attr, star_dict in scored_attr_map.items():
      sorted_star_dict = OrderedDict()
      for star_str, sentence_info_list in star_dict.items():
        if attr in self.en2ja.keys():
          sorted_sentence_info_list = sorted(sentence_info_list, key=lambda si: si.score, reverse=True)
          sorted_star_dict[star_str] = [OrderedDict(si._asdict()) for si in sorted_sentence_info_list]

        else:
          sorted_star_dict[star_str] = [OrderedDict(si._asdict()) for si in sentence_info_list]
      
      sorted_attr_map[attr] = sorted_star_dict

    result_dict['map'] = sorted_attr_map
    return result_dict


  def _read_prediction_json(self, pred_json) -> list:
    pred_json = pathlib.Path(pred_json)
    pred_data = json.load(pred_json.open(mode='r', encoding=self.code),
                          object_pairs_hook=OrderedDict)
    return pred_data
  
  def _make_star_dict(self) -> OrderedDict:
    star_dict = OrderedDict()
    for star_str in STAR_CORRESPONDENCE_DICT.values():
      star_dict[star_str] = []

    return star_dict


if __name__ == "__main__":
  import glob
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('dic_dir')
  args = parser.parse_args()

  input_dir = args.input_dir
  category = os.path.basename(input_dir)

  dic_dir = args.dic_dir
  mapper = SentenceMapper(dic_dir, category)

  jsonpath_list = [pathlib.Path(f).resolve() for f in glob.glob('{}\\**'.format(input_dir), recursive=True)
                   if pathlib.Path(f).suffix == '.json' and pathlib.Path(f).name.startswith('prediction')]
  
  for jsonpath in jsonpath_list:
    out_file = jsonpath.parent / 'map_{}'.format(jsonpath.name)
    product_name = jsonpath.parent.name

    map_dict = mapper.create_map(jsonpath)

    # pprint(map_dict)

    # attrs = len(map_dict.keys())
    # stars = len(SentenceMapper.STAR_CORRESPONDENCE_DICT.keys())
    # heatmap = np.zeros((stars, attrs-1), dtype=int)
    # for cidx, (attrs, star_dict) in enumerate(map_dict.items()):
    #     if attrs == SentenceMapper.OTHER_EN_ATTR:
    #         continue

    #     for ridx, (star_str, sentence_info_list) in enumerate(star_dict.items()):
    #         heatmap[ridx, cidx] = len(sentence_info_list)

    # map_df = pandas.DataFrame(
    #     heatmap, 
    #     index=SentenceMapper.STAR_CORRESPONDENCE_DICT.values(),
    #     columns=[*map_dict.keys()][:-1]
    # )
    
    # plt.figure()
    # plt.title('{}'.format(product_name))
    # seaborn.heatmap(map_df, cmap='cool')
    # f, _ = os.path.splitext(file_name)
    # img_file = '{}\\heatmap_{}.png'.format(product_dir, f)
    # plt.savefig(img_file)
    

    json.dump(map_dict, out_file.open(mode='w', encoding=mapper.code),
              ensure_ascii=False, indent=4)