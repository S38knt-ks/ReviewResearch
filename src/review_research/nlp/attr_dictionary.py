import os
import pathlib
import glob
from functools import partial
from collections import namedtuple, OrderedDict
from typing import List, Union, Dict, Tuple

from ..nlp import AttrName
from ..nlp import AttrDictInfo

COMMON_DICTIONARY_NAME = 'common'

AttrDict = Dict[str, Tuple[str, ...]]

class AttrDictHandler:
  """属性辞書を扱うためのクラス

  Attributes:
    dic_source_dir (Union[str, pathlib.Path]): 属性辞書の大本のディレクトリ
    all_dictionaries (List[pathlib.Path]): すべての辞書ファイルのパス一覧
    common_attr_dict (AttrDict): 商品カテゴリによらない共通の属性辞書
    common_en2ja (Dict[str, str]): 共通属性名の英日辞書
    common_ja2en (Dict[str, str]): 共通属性名の日英辞書
  """

  def __init__(self, dic_source_dir: Union[str, pathlib.Path]):
    """
    Args:
      dic_source_dir (Union[str, pathlib.Path]): 属性辞書の大本のディレクトリ
    """
    self.dic_source_dir = pathlib.Path(dic_source_dir)
    self.all_dictionaries = search_attr_dict(self.dic_source_dir)
    
    # 商品カテゴリごとに整理
    self._category_to_attrdicts = OrderedDict()
    self._category_to_en2ja_translater = OrderedDict()
    self._category_to_ja2en_translater = OrderedDict()
    for dic_path in self.all_dictionaries:
      attr_dict_info = read_attr_dict(dic_path)
      category = attr_dict_info.category

      attr_en_name, attr_ja_name = attr_dict_info.name
      self._category_to_en2ja_translater.setdefault(
          category, OrderedDict())[attr_en_name] = attr_ja_name
      self._category_to_ja2en_translater.setdefault(
          category, OrderedDict())[attr_ja_name] = attr_en_name

      attr_words = attr_dict_info.words
      self._category_to_attrdicts.setdefault(
          category, OrderedDict())[attr_ja_name] = attr_words

  @property
  def common_attr_dict(self) -> AttrDict:
    return self.attr_dict(COMMON_DICTIONARY_NAME)

  @property
  def common_en2ja(self) -> Dict[str, str]:
    return self.en2ja(COMMON_DICTIONARY_NAME)

  @property
  def common_ja2en(self) -> Dict[str, str]:
    return self.ja2en(COMMON_DICTIONARY_NAME)


  def attr_dict(self, category: str) -> AttrDict:
    """categoryで指定した属性辞書を返す
    返される属性辞書は（日本語で表現される属性, 属性語のタプル）のキーバリューとなっている

    Args:
      category (str): 商品カテゴリ

    Returns:
      属性辞書
    """
    return self._category_to_attrdicts[category]

  def en2ja(self, category: str) -> Dict[str, str]:
    """categoryで指定した属性名の英日変換辞書を返す
    
    Args:
      category (str): 商品カテゴリ

    Returns:
      属性の英名に対応した和名を格納する辞書
    """
    return self._category_to_en2ja_translater[category]

  def ja2en(self, category: str) -> Dict[str, str]:
    """categoryで指定した属性名の日英変換辞書を返す
    
    Args:
      category (str): 商品カテゴリ

    Returns:
      属性の和名に対応した英名を格納する辞書
    """
    return self._category_to_ja2en_translater[category]


  def remove_intersection_word(self, category: str) -> AttrDict:
    """categoryで指定した属性辞書において、複数属性にまたがる単語を削除して更新した属性辞書を返す
    
    Args:
      category (str): 商品カテゴリ

    Returns:
      更新した属性辞書
    """
    attr_dict = self.attr_dict(category)
    attr_list = [*attr_dict]
    attr_num  = len(attr_list)
    intersection_word_dict = {}
    for target_idx, target_attr in enumerate(attr_list[:-1]):
      target_word_set = set(attr_dict[target_attr])
      intersection_with_target = partial(set.intersection, target_word_set)
      
      for next_idx in range(target_idx+1, attr_num):
        next_attr = attr_list[next_idx]
        next_word_set = set(attr_dict[next_attr])
        intersection_words = list(intersection_with_target(next_word_set))
        for word in intersection_words:
          intersection_word_dict.setdefault(word, []).append((target_attr, next_attr))

    intersection_words = set(intersection_word_dict.keys())
    if len(intersection_words) == 0:
      return attr_dict

    else:
      new_attr_dict = {}
      for attr_name, words in attr_dict.items():      
        new_words = sorted(set.difference(set(words), intersection_words),
                            key=words.index)
        new_attr_dict[attr_name] = new_words

      return new_attr_dict


def search_attr_dict(dic_source_dir: str) -> List[pathlib.Path]:
  """
  指定したディレクトリから属性辞書のファイルパスをすべて取り出す

  Args:
    dic_source_dir (str): 属性辞書が入っているディレクトリ

  Returns:
    属性辞書のパス一覧
  """
  glob_recursively = partial(glob.glob, recursive=True)
  target = '{}/**'.format(dic_source_dir)
  all_dictionaries = [pathlib.Path(f) for f in glob_recursively(target)
                      if pathlib.Path(f).is_file()]
  return all_dictionaries


def read_attr_dict(dic_path: Union[str, pathlib.Path]) -> AttrDictInfo:
  """属性辞書を読み取り、その情報をまとめる

  Args:
    dic_path (Union[str, pathlib.Path]): 属性辞書ファイルのパス

  Returns:
    AttrDicInfoインスタンス
  """
  dic_path = pathlib.Path(dic_path)
  with dic_path.open(mode='r', encoding='utf-8') as fp:
    header = line = fp.readline()
    attr_ja_name = header.strip().replace('name:', '')
    attr_words = list()
    while line != '':
      line = fp.readline().strip()
      attr_words.append(line)

  category = dic_path.parent.name
  attr_en_name = dic_path.stem
  attr_words   = tuple(attr_words)
  return AttrDictInfo(category, 
                      AttrName(attr_en_name, attr_ja_name),
                      attr_words)