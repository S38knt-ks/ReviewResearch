import argparse
import re
from collections import OrderedDict
from typing import Tuple, List, Dict, NamedTuple

import CaboCha

from ..nlp import Token
from ..nlp import TokenFeature
from ..nlp import ChunkDetail
from ..nlp import TokenDetail
from ..nlp import PhraseDetail
from ..nlp import LinkDetail
from ..nlp import CabochaParserSingleton

# 型の定義
ChunkDict = Dict[int, ChunkDetail]
TokenDict = Dict[int, TokenDetail]
AllocationDict = Dict[int, TokenDict]
RepresentationDict = Dict[int, PhraseDetail]
LinkDict = Dict[int, Tuple[LinkDetail, ...]]

class AnalysisResult(NamedTuple):
  """係り受け解析の結果を保存するためのクラス

  Attributes:
    chunk_dict (ChunkDict): 文節単位の解析結果
    token_dict (TokenDict): 形態素単位の解析結果
    tree (str): 係り受け構造をグラフィカルに表したもの
  """
  chunk_dict: ChunkDict
  token_dict: TokenDict
  tree: str


class DependencyAnalyzer(object):
  """係り受け解析器のラッパー
  
  Attributes:
    parser (CaboCha.Parser): 係り受け解析器

  Usage:
    初期設定
    >>> da = DependencyAnalyzer()
    >>> text = '解析したい文'

    係り受け解析に通す
    >>> analysis_result = da.analyze(text)
    >>> print(analysis_result.tree)  # 係り受け構造の表示
    >>> chunk_dict = analysis_result.chunk_dict
    >>> token_dict = analysis_result.token_dict

    形態素と文節の対応付け
    >>> alloc_dict = da.allocate_token_for_chunk(chunk_dict, token_dict)

    文節の主辞情報の抽出
    >>> repr_dict = da.extract_representation(chunk_dict, alloc_dict)

    係り受けの結合
    >>> link_dict = da.make_link_dict(chunk_dict, repr_dict)
  """

  def __init__(self):
      self._result_tree = None

  @property
  def parser(self) -> CaboCha.Parser:
      return CabochaParserSingleton.get_instance()

  def analyze(self, text: str) -> AnalysisResult:
    """係り受け解析を行う

    Args:
      text (str): 一文の文字列

    Returns:
      AnalysisResultインスタンス
    """
    self._result_tree = None
    tree = self.parser.parse(text)
    self._result_tree = tree.toString(CaboCha.FORMAT_TREE)

    chunk_list = list()
    for i in range(tree.chunk_size()):
      phrase = _make_phrase(tree, tree.chunk(i))
      chunk_prop = ChunkDetail.from_phrase_and_chunk(phrase, tree.chunk(i))
      chunk_list.append(chunk_prop)

    chunk_dict = OrderedDict()
    for idx, chunk_prop in enumerate(chunk_list):
      chunk_dict[idx] = chunk_prop

    token_list = [TokenDetail.from_cabocha_token(tree.token(i)) 
                  for i in range(tree.token_size())]
    token_dict = OrderedDict()
    for idx, token_detail in enumerate(token_list):
      token_dict[idx] = token_detail

    return AnalysisResult(chunk_dict, token_dict, self._result_tree)

  def allocate_token_for_chunk(self, chunk_dict: ChunkDict, 
                               token_dict: TokenDict) -> AllocationDict:
    """形態素と文節を対応付ける

    Args:
      chunk_dict (ChunkDict): 出現順に文節情報を格納した辞書
      token_dict (TokenDict): 出現順に形態素情報を格納した辞書

    Returns:
      文節の出現順をキーとして、その文節内にある形態素情報を出現順に格納した辞書
    """
    allocation_dict = OrderedDict()
    for chunk_id, chunk_prop in chunk_dict.items():
        token_pos  = chunk_prop.token_position
        chunk_size = chunk_prop.number_tokens

        tokens = OrderedDict()
        for token_id in range(token_pos, token_pos + chunk_size):
            tokens[token_id] = token_dict[token_id]

        allocation_dict[chunk_id] = tokens

    return allocation_dict

  def extract_representation(self, 
      chunk_dict: ChunkDict,
      allocation_dict: AllocationDict) -> RepresentationDict:
    """節内の主辞と機能語を取得

    Args:
      chunk_dict (ChunkDict): 出現順に文節情報を格納した辞書
      allocation_dict (AllocationDict):
        文節の出現順をキーとして、その文節内にある形態素情報を出現順に格納した辞書

    Returns:
      文節の出現順に、文節の主辞情報を格納した辞書
    """
    representation_dict = OrderedDict()
    for chunk_id, chunk_detail in chunk_dict.items():
      representation_dict[chunk_id] = PhraseDetail.from_analysis_result(
          chunk_detail, allocation_dict[chunk_id])

    return representation_dict
          
  def make_link_dict(self, chunk_dict: ChunkDict,
                     representation_dict: RepresentationDict) -> LinkDict:
    """係り元から終端の係り先までの係り受け関係を取得

    Args:
      chunk_dict (ChunkDict): 出現順に文節情報を格納した辞書
      representation_dict (RepresentationDict): 
        文節の出現順に、文節の主辞情報を格納した辞書

    Returns:
      最初の係り受け元から順に終端までの係り受け関係を結合した情報を格納した辞書
    """
    visited = list()
    link_dict = OrderedDict()
    for chunk_id in chunk_dict.keys():
      # 係り受け構造が決定された文節は無視する
      if chunk_id in visited:
        continue
  
      link = chunk_id
      link_list = [link]  # 始点となる文節から最後の係り先文節までを格納するリスト
      while True:
        chunk_detail = chunk_dict[link]
        next_link = chunk_detail.next_link
        if next_link == -1:
          break

        link = next_link
        link_list.append(link)

      link_detail_list = list()
      for link in link_list:
        # 係り受け構造が決定されている文節を登録
        if link not in visited:
          visited.append(link)

        link_detail_list.append(LinkDetail(link, representation_dict[link]))

      link_dict[chunk_id] = tuple(link_detail_list)

    return link_dict


# ヘルパー関数群
def _make_phrase(tree: CaboCha.Tree, chunk: CaboCha.Chunk) -> str:
  """文節を生成するヘルパー関数
  
  Args:
    tree: CaboChaで係り受け解析した結果（表形式）
    chunk (CaboCha.Chunk): 注目しているチャンク

  Returns:
    チャンクを基に結合された文節
  """
  token_range = range(chunk.token_pos, chunk.token_pos + chunk.token_size)
  phrase = ''.join(str(tree.token(i).surface) for i in token_range)
  return phrase


# デバッグ用のコード
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('json_file')
  parser.add_argument('--out-file', default='output.txt')
  parser.add_argument('--code', default='utf-8')
  args = parser.parse_args()

  import json
  import os
  import re
  import pathlib
  from collections import namedtuple
  from pprint import pprint
  
  from ..nlp import Splitter
  from ..nlp import normalize

  jf = pathlib.Path(args.json_file)
  code = args.code

  review_data = json.load(jf.open(mode='r', encoding=code),
                          object_pairs_hook=OrderedDict)

  product = review_data['product']
  reviews = review_data['reviews']

  total_reviews = len(reviews)

  da = DependencyAnalyzer()
  sp = Splitter()

  SENTENCE_PROP_FIELD = ['review_id', 'sentence_id', 'sentence',
                         'chunk_dict', 'result_tree', 'token_dict']
  SentenceProp = namedtuple('SentenceProp', SENTENCE_PROP_FIELD)

  sentence_list = []
  for review_id, review_info in enumerate(reviews):
    review_text = normalize(review_info['review'])
    sentences = sp.split_sentence(review_text)
    for sentence_id, sentence in sentences.items():
      chunk_dict, token_dict, result_tree = da.analyze(sentence)
      sentence_list.append(
        SentenceProp(review_id, sentence_id, sentence,
                     chunk_dict, result_tree, token_dict))

  total_sentence = len(sentence_list)

  with open(args.out_file, mode='w', encoding=code) as fp:
    fp.write('<PRODUCT>\t{}\n'.format(product))
    fp.write('<REVIEWS>\t{}\n'.format(total_reviews))
    fp.write('<SENTENCES>\t{}\n\n'.format(total_sentence))

  sep = '{}\n'.format('=' * 79)

  with open(args.out_file, mode='a', encoding=code) as fp:
    for idx, sentence_prop in enumerate(sentence_list):
      fp.write(sep)
      fp.write('<review_id>\t{} / {}\n'.format(sentence_prop.review_id+1, total_reviews))
      fp.write('<sentence_id>\t{} ({} / {})\n'.format(sentence_prop.sentence_id, idx+1, total_sentence))

      sentence = '\n'.join(s.strip() for s in sentence_prop.sentence.split('\n'))
      fp.write('"{}"\n\n'.format(sentence))

      fp.write('<sentence_prop.chunk_dict>\n')
      pprint(sentence_prop.chunk_dict, fp)

      fp.write('\n{}\n'.format(sentence_prop.result_tree))

      allocation_dict = da.allocate_token_for_chunk(sentence_prop.chunk_dict, sentence_prop.token_dict)
      fp.write('<allocation_dict>\n')
      pprint(allocation_dict, fp)

      fp.write('\n')

      fp.write('<representation>\n')
      representation_dict = da.extract_representation(sentence_prop.chunk_dict, allocation_dict)
      pprint(representation_dict, fp)

      fp.write('\n')

      fp.write('<tree link>\n')
      tree_link = da.make_link_dict(sentence_prop.chunk_dict, representation_dict)
      pprint(tree_link, fp)
