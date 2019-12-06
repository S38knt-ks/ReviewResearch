import os
import glob
from pprint import pprint
from collections import OrderedDict, namedtuple, Counter
from functools import partial
from typing import List

from review_research.nlp import Tokenizer
from review_research.nlp import WordRepr
from review_research.nlp import Splitter

INTERSECTION_PROP_FIELD = ['word', 'source', 'target']
IntersectionProp = namedtuple('IntersectionProp', INTERSECTION_PROP_FIELD)

WORD_ATTRIBUTE_FIELD = ['word', 'attribute']
WordAttribute = namedtuple('WordAttribute', WORD_ATTRIBUTE_FIELD)

SENTENCE_ATTRIBUTE_FIELD = ['attribute', 'count', 'inclusion', 'reference', 'words']
SentenceAttribute = namedtuple('SentenceAttribute', SENTENCE_ATTRIBUTE_FIELD)

class AttributeAllocation:

  # カテゴリごとに共通の属性の辞書が格納されているディレクトリ名
  COMMON_DIR = 'common'

  def __init__(self, dic_dir: str, category: str, code='utf-8'):
    self._dic_dir  = dic_dir
    self._category = category
    self._code     = code

    dic_path_list = self._search_dictionary()
    self._dictionary = OrderedDict()
    for dic_path in dic_path_list:
      self._read_dictionary(dic_path)

    self._remove_intersection_word()
    print('[after removing intersection word]')
    pprint(self.dictionary)
    self._tokenizer = Tokenizer()

  @property
  def dic_dir(self) -> str:
    return self._dic_dir

  @property
  def category(self) -> str:
    return self._category

  @property
  def code(self) -> str:
    return self._code

  @property
  def dictionary(self) -> OrderedDict:
    return self._dictionary

  @property
  def attributes(self) -> list:
    return [*self._dictionary]

  @property
  def intersection_words(self) -> List[str]:
    return self._intersection_word_list

  def alloc_attribute(self, sentence: str) -> List[SentenceAttribute]:
    # 形態素解析し、単語を取り出す
    word_list = self._tokenizer.get_baseforms(sentence, remove_stopwords=False)

    # 辞書間で重複している語を取り除く
    word_list = [word for word in word_list
                 if not word.word in self.intersection_words]
    word_list = [word for word in word_list
                 if not word.surface in self.intersection_words]

    total_word = len(word_list)

    # 属性と単語の抽出
    attribute_list      = []
    word_attribute_list = []
    for word in word_list:
      for attr_name, dic_words in self.dictionary.items():
        if word.word in dic_words or word.surface in dic_words:
          attribute_list.append(attr_name)
          word_attribute_list.append(WordAttribute(word.surface, attr_name))
          break

    word_dict = OrderedDict()
    for attr in sorted(set(attribute_list)):
      word_dict[attr] = []

    for (word, attr) in word_attribute_list:
      word_dict[attr].append(word)
    
    attribute_counter = Counter(attribute_list)

    sentence_attribute_list = [
      SentenceAttribute(attr, count, count / float(total_word), self._calc_reference_value(count, total_word),  word_dict[attr])
      for (attr, count) in attribute_counter.most_common()
    ]

    sentence_attribute_list = sorted(sentence_attribute_list,
                                     key=lambda sa: sa.count,
                                     reverse=True)

    return sentence_attribute_list


  def _search_dictionary(self) -> list:
      dic_dir_format = partial('{}\\{}'.format, self.dic_dir)
      common_dic_dir   = dic_dir_format(self.COMMON_DIR)
      category_dic_dir = dic_dir_format(self.category)


      dic_path_format = partial('{}\\*.txt'.format)
      common_dic_paths   = glob.glob(dic_path_format(common_dic_dir))
      category_dic_paths = glob.glob(dic_path_format(category_dic_dir))

      dic_paths = common_dic_paths
      dic_paths.extend(category_dic_paths)

      return dic_paths


  def _read_dictionary(self, dic_path: str):
      with open(dic_path, mode='r', encoding=self.code) as fp:
          data = [line.strip() for line in fp.readlines()]

      dic_name = data[0].replace('name:', '')
      dic_data = data[1:]

      self._dictionary[dic_name] = dic_data
  

  def _remove_intersection_word(self):
      # 複数属性にまたがる語を抽出
      attr_list = self.attributes
      print('<attributes>')
      pprint(attr_list)
      attr_length  = len(self.dictionary)
      target_begin = 1
      intersection_word_list = []
      for source_idx in range(attr_length - 1):
          source_attr      = attr_list[source_idx]
          source_word_set  = set(self.dictionary[source_attr])
          get_intersection = partial(set.intersection, source_word_set)

          for target_idx in range(target_begin, attr_length):
              target_attr        = attr_list[target_idx]
              target_word_set    = set(self.dictionary[target_attr])
              intersection_words = [IntersectionProp(word, source_attr, target_attr) 
                                    for word in list(get_intersection(target_word_set))]
              if len(intersection_words) > 0:
                  intersection_word_list.extend(intersection_words)

          target_begin += 1

      # 重複する語を削除
      print('[intersection words]')
      pprint(intersection_word_list)
      print()

      self._intersection_word_list = list(set([intersection.word for intersection in intersection_word_list]))

      if len(intersection_word_list) == 0:
          return

      # 複数属性にまたがる語を辞書から削除
      for dic_name, word_list in self.dictionary.items():
          new_word_list = word_list[:]
          for word in self.intersection_words:
              if word in new_word_list:
                  new_word_list.remove(word)

          self._dictionary[dic_name] = new_word_list


  def _calc_reference_value(self, count: int, total_word: int) -> float:
    return (count ** 2) / float(total_word)