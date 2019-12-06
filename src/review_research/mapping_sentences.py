import argparse
import json
import os
import pathlib
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint
from typing import NamedTuple, Tuple, Dict, List, Set, Union, NoReturn

import pandas
import seaborn
import numpy as np
import matplotlib.pyplot as plt

from review_research.evaluation import ReviewTextInfo
from review_research.nlp import AttributionExtractor
from review_research.evaluation import AttrPredictionResult
from review_research.review import StarsDistribution
from review_research.misc import unique_sort_by_index
from review_research.misc import get_all_jsonfiles

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
                            'link_length',]
SentenceTempInfo = namedtuple('SentenceTempInfo', SENTENCE_TEMP_INFO_FIELD)

SENTENCE_INFO_FIELD = [*SENTENCE_TEMP_INFO_FIELD, 'score', 'score_detail']
SentenceInfo = namedtuple('SentenceInfo', SENTENCE_INFO_FIELD)

class ReviewTextInfoForMapping(NamedTuple):
  """対応付けのためのクラス

  Attributes:
    review (str): レビュー本文
    text (str): 対象の文
    candidate_terms (Union[str, Set[str]]): 属性候補語一覧
    hit_terms (Union[str, Set[str]]): 属性語として抽出された語一覧
    phrases (Union[str, Set[str]]): 文節一覧
    num_attributions (int): 文中の属性数
    link_length (int): 係り受け関係中の文節数
    score (int): 文の有用度(仮)
  """
  review: str
  text: str
  candidate_terms: Union[str, Set[str]]
  hit_terms: Union[str, Set[str]]
  phrases: Union[str, Set[str]]
  num_attributions: int
  link_length: int
  score: int

class MappingResult(NamedTuple):
  """レビュー文中の文を属性と星評価に対応付けさせた結果

  Attributes:
    category (str): 商品カテゴリ
    product (str): 商品名
    link (str): レビューページへの URL
    maker (str): 製造企業
    average_stars (float): 平均評価
    stars_distribution (StarsDistribution): 星評価分布
    total_review (int): レビュー数
    total_text (int): 総文数
    mapping (Dict[str, Dict[str, Tuple[ReviewTextInfoForMapping, ...]]]): 対応付け
  """
  category: str
  product: str
  link: str
  maker: str
  average_stars: float
  stars_distribution: StarsDistribution
  total_review: int
  total_text: int
  mapping: Dict[str, Dict[str, Tuple[ReviewTextInfoForMapping, ...]]]

  @classmethod
  def load(cls, jsonpath: Union[str, pathlib.Path]):
    jsonpath = pathlib.Path(jsonpath)
    data = json.load(jsonpath.open('r', encoding='utf-8'),
                     object_pairs_hook=OrderedDict)
    this = cls(**data)
    mapping = OrderedDict()
    for attr, star_to_text_list in this.mapping.items():
      star_map = OrderedDict()
      for star, text_list in star_to_text_list.items():
        texts = tuple(ReviewTextInfoForMapping(**text) for text in text_list)
        star_map[star] = texts

      mapping[attr] = star_map

    return this._replace(mapping=mapping)

  def dump(self, filepath: Union[str, pathlib.Path]) -> NoReturn:
    """JSON ファイルに保存する

    Args:
      filepath (Union[str, pathlib.Path]): 出力先ファイル名
    """
    filepath = pathlib.Path(filepath)
    this = MappingResult._make(self)
    mapping = OrderedDict()
    for attr, star_to_text_list in self.mapping.items():
      star_map = OrderedDict()
      for star, text_list in star_to_text_list.items():
        texts = tuple(text._asdict() for text in text_list)
        star_map[star] = texts

      mapping[attr] = star_map

    this = this._replace(mapping=mapping)
    json.dump(this, filepath.open('w', encoding='utf-8'),
              ensure_ascii=False, indent=4)


class SentenceMapper:
  """レビュー文中の文を属性と星評価別に対応付ける"""

  def __init__(self, dic_dir: Union[str, pathlib.Path], category: str):
    self._extractor = AttributionExtractor(dic_dir)
    self.category = category

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

  def create_map(self, pred_jsonpath: Union[str, pathlib.Path]) -> MappingResult:
    """属性抽出の結果からレビュー文中の文を属性と星評価で対応付ける

    Args:
      pred_jsonpath (Union[str, pathlib.Path]): 属性抽出の結果を格納した JSON ファイル

    Returns:
      対応付けの結果
    """
    pred_data = AttrPredictionResult.load(pred_jsonpath)
    attr_map = self._adapt_text_to_attr_and_star(pred_data)
    sorted_attr_map = OrderedDict()
    for attr, star_dict in attr_map.items():
      sorted_star_dict = OrderedDict()
      for star_str, info_for_mapping_list in star_dict.items():
        if attr in self.en2ja:
          sorted_sentence_info_list = sorted(
              info_for_mapping_list, key=lambda si: si.score, reverse=True)
          sorted_star_dict[star_str] = tuple(sorted_sentence_info_list)

        else:
          sorted_star_dict[star_str] = tuple(info_for_mapping_list)
      
      sorted_attr_map[attr] = sorted_star_dict

    mapping_result = MappingResult(
        pred_data.category, pred_data.product, pred_data.link, pred_data.maker,
        pred_data.average_stars, pred_data.stars_distribution,
        pred_data.total_review, pred_data.total_text, sorted_attr_map)
    return mapping_result

  def _adapt_text_to_attr_and_star(
      self, pred_data: AttrPredictionResult
  ) -> Dict[str, Dict[str, List[ReviewTextInfoForMapping]]]:
    """レビュー文中の文を属性と星評価に対応付ける

    Args:
      pred_data (AttrPredictionResult): 属性抽出予測結果

    Returns:
      レビュー文中の文を属性と星評価に対応付けた辞書
    """
    attr_to_star_map = OrderedDict()
    for attr in self.en2ja:
      attr_to_star_map[attr] = _initialize_star_map()

    attr_to_star_map[OTHER_EN_ATTR] = _initialize_star_map()    
    for review_text_info in pred_data.texts:
      star = review_text_info.star
      star_str = STAR_CORRESPONDENCE_DICT[star]
      review = review_text_info.review
      text = review_text_info.text
      result_dict = review_text_info.result
      if result_dict:
        for attr, extraction_results in result_dict.items():                    
          phrases = []
          candidate_terms = []
          hit_terms = []
          for extraction_result in extraction_results:
            phrases.extend(extraction_result.phrases)
            candidate_terms.extend(extraction_result.candidate_terms)
            hit_terms.extend(extraction_result.hit_terms)

          phrases = frozenset(phrases)
          link_length = len(phrases)
          candidate_terms = frozenset(unique_sort_by_index(candidate_terms))
          hit_terms = frozenset(unique_sort_by_index(hit_terms))
          info_for_mapping = ReviewTextInfoForMapping(
              review, text, candidate_terms, hit_terms, phrases,
              len(extraction_results), link_length, link_length)
          attr_to_star_map[attr][star_str].append(info_for_mapping)

      else:  # 属性が抽出できなかった場合
        info_for_mapping = ReviewTextInfoForMapping(review, text, '', '', '',
                                                    0, 0, 0)
        attr_to_star_map[OTHER_EN_ATTR][star_str].append(info_for_mapping)

    return attr_to_star_map
  
def _initialize_star_map() -> Dict[str, List[()]]:
  """星評価とレビュー文中の文を対応付けさせるための辞書を初期化して返す"""
  star_to_texts = OrderedDict()
  for star_str in STAR_CORRESPONDENCE_DICT.values():
    star_to_texts[star_str] = list()

  return star_to_texts


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
  jsonpath_list = get_all_jsonfiles(input_dir, 'prediction')
  for jsonpath in jsonpath_list:
    map_result = mapper.create_map(jsonpath)
    out_file = jsonpath.parent / 'map_{}'.format(jsonpath.name)
    map_result.dump(out_file)