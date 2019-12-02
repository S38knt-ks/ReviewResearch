import os
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint
from typing import NamedTuple, Iterable, List, Any, Tuple, NoReturn, Dict

from tqdm import tqdm

from ..nlp import REQUIREMENT_POS_LIST
from ..nlp import DependencyAnalyzer
from ..nlp import PhraseDetail
from ..nlp import LinkDetail
from ..nlp import ChunkDict
from ..nlp import TokenDict
from ..nlp import AllocationDict
from ..nlp import RepresentationDict
from ..nlp import LinkDict
from ..nlp import AttrExtractionResult
from ..nlp import AttrExtractionInfo
from ..nlp import COMMON_DICTIONARY_NAME
from ..nlp import StopwordRemover
from ..nlp import AttrDictHandler

class DependencyAnalysisResult(NamedTuple):
  """DependencyAnalyzerの解析結果を格納するクラス

  Attributes:
    chunk_dict (ChunkDict):
    token_dict (TokenDict):
    alloc_dict (AllocationDict):
    repr_dict (RepresentationDict):
    link_dict (LinkDict):
  """
  chunk_dict: ChunkDict
  token_dict: TokenDict
  alloc_dict: AllocationDict
  repr_dict: RepresentationDict
  link_dict: LinkDict

# 並列表現を表す助詞
PAEALLEL_PRESENTATION_WORDS = ('や', 'と')
# 格助詞による抽出方法のための格助詞一覧
BASE_PATTERN_WORDS = ('が', 'は', 'も', 'に', 'を')

WORD_SEPARATOR = '<WORDSEP>'

class AttributionExtractor:
  """属性抽出器"""

  def __init__(self, dic_dir: str, encoding: str = 'utf-8', 
               extend: bool = True, ristrict: bool = True):
    self.remover = StopwordRemover()

    self.category  = None
    self._encoding = encoding
    self._extend   = extend
    self._ristrict = ristrict

    self._category_to_attrdict = None
    self._ja2en = None
    self._en2ja = None

    self._attrdict_handler = AttrDictHandler(dic_dir)
    self._common_attr_dict = self._attrdict_handler.common_attr_dict

    self._analyzer = DependencyAnalyzer()

  @property
  def extend(self) -> bool:
    return self._extend

  @property
  def ristrict(self) -> bool:
    return self._ristrict

  @property
  def category(self) -> str:
    """現在扱っている商品カテゴリ"""
    return self.__category

  @category.setter
  def category(self, category):
    if category is not None and self.category != category:
      self.__category = category
      self._update_attr_dictionary(category)

  @property
  def encoding(self) -> str:
    return self._encoding

  @property
  def ja2en(self):
    """日本語属性名を英語属性名に変換する辞書"""
    return self._ja2en

  @property
  def en2ja(self):
    """英語属性名を日本語属性名に変換する辞書"""
    return self._en2ja

  @property
  def attrdict(self):
    return self._attr_dict

  @property
  def stopwords(self) -> list:
    return self.remover.stopwords

  def extract_attribution(self, text: str) -> Dict[str, Tuple[Dict[str, Any]]]:
    """属性の抽出を行う

    Args:
      text (str): 属性を抽出したい文

    Returns:
      抽出できた属性ごとに属性に関する情報をまとめた辞書
    """
    analysis_result = self._analyze(text)
    result_list = []
    for linkdetails in analysis_result.link_dict.values():
      attrs = []
      candidate_term_list = []
      hit_terms = []
      links = tuple(linkdetail.phrase_id for linkdetail in linkdetails)
      flagment = _convert_link_to_flagment(links, 
                                           analysis_result.chunk_dict)
      candidate_linkdetails = self._get_canndidate_terms(linkdetails)
      for linkdetail in candidate_linkdetails:
        head, words, _, _ = linkdetail.phrase_detail
        
        candidate_terms = [head]
        # 候補語が複合語の場合、属性辞書に載っていない場合がある
        # そのことを防ぐために複合語を構成する形態素も候補語に追加する
        if self.extend and words:
          candidate_terms.extend(words)

        candidate_term_list.extend(candidate_terms)
        for attr, words in self.attrdict.items():
          for term in candidate_terms:
            if term in words:
              hit_terms.append(term)
              attrs.append(attr)

      attrs = frozenset(_unique_sort_by_index(attrs))
      candidate_terms = frozenset(_unique_sort_by_index(candidate_term_list))
      hit_terms = frozenset(_unique_sort_by_index(hit_terms))
      phrases = frozenset(linkdetail.phrase_detail.head_surface 
                          for linkdetail in linkdetails)
      result_list.append(AttrExtractionResult(
          attrs, flagment, candidate_terms, hit_terms, phrases, len(links)))

    result_dict = defaultdict(list)
    for result in result_list:
      for attr in result.attrs:
        info = AttrExtractionInfo.from_result(result)
        result_dict[attr].append(info)

    temp_dict = dict(result_dict)
    result_dict = OrderedDict()
    for attr in self.attrdict:
      if attr in temp_dict:
        info_list = temp_dict[attr]
        info_set = _unique_sort_by_index(info_list)
        result_dict[attr] = tuple(OrderedDict(info._asdict()) 
                                  for info in info_set)

    return result_dict

  def _get_canndidate_terms(self, 
      linkdetails: Tuple[LinkDetail, ...]) -> Tuple[LinkDetail, ...]:
    """属性候補語を抽出するためのヘルパーメソッド

    Args:
      linkdetails (Tuple[LinkDetail, ...]): 係り受け関係

    Returns:
      属性候補語のみを含む文節の係り受け構造の一覧
    """
    if self.ristrict:
      linkdetails = self._update_linkdetails(linkdetails)

    candidate_link_prop_list = []
    for linkdetail in linkdetails[:-1]:
      head, _, pos, func = linkdetail.phrase_content
      if pos != '名詞' or head in self.stopwords:
        continue                

      else:
        if func in BASE_PATTERN_WORDS:
          candidate_link_prop_list.append(linkdetail)

    last_linkdetail = linkdetails[-1]
    if last_linkdetail.phrase_content.pos == '名詞':
      candidate_link_prop_list.append(last_linkdetail)

    return tuple(candidate_link_prop_list)

  def _update_linkdetails(self, 
      linkdetails: Tuple[LinkDetail, ...]) -> Tuple[LinkDetail, ...]:
    """係り受け関係の更新を行うためのヘルパーメソッド

    Args:
      linkdetails (Tuple[LinkDetails, ...]): 更新したい係り受け関係

    Returns:
      更新後の係り受け関係
    """
    length = len(linkdetails) - 1
    old_updated_linkdetails = linkdetails[:]
    while True:
      updated_linkdetails = []
      for curr_idx, curr_linkdetail in enumerate(linkdetails[:-1]):
        c_head, c_words, c_pos, c_func = curr_linkdetail.phrase_detail
        is_not_noun = c_pos != '名詞'
        is_noun_and_good = c_pos == '名詞' and _is_good_functional_word(c_func)
        is_stopword = c_head in self.stopwords
        if is_not_noun and is_noun_and_good and is_stopword:
          updated_linkdetails = curr_linkdetail

        # 属性候補語と思われる語句が含まれる文節の処理
        else:
          n_head, _, n_pos, n_func = linkdetails[curr_idx+1].phrase_detail
          if n_pos != '名詞':
            updated_linkdetail = curr_linkdetail

          else:  # 機能語が一致しないことで抽出できない主辞や単語を減らすための処理
            if c_func == 'の':  # 助詞「の」における処理
              if n_head in self.stopwords:
                # 次の主辞がストップワードなら次の機能語を現在の機能語とする
                # そうすることで、機能語が一致しないことで抽出できない主辞や単語を減らせる
                updated_linkdetail = LinkDetail(
                    curr_linkdetail.chunk_id, 
                    PhraseDetail(c_head, c_pos, c_words, n_func))

              else:
                updated_linkdetail = curr_linkdetail

            elif c_func in PAEALLEL_PRESENTATION_WORDS:  # 助詞「と」「や」における処理
              # 並列に述べられているので機能語を合わせても問題ない
              updated_linkdetail = LinkDetail(
                  curr_linkdetail.chunk_id, 
                  PhraseDetail(c_head, c_pos, c_words, n_func))
                
            else:  # 今のところ対処できないものは更新しない
              updated_linkdetail = curr_linkdetail

        updated_linkdetails.append(updated_linkdetail)
      
      updated_linkdetails.append(linkdetails[length])
      if updated_linkdetails == old_updated_linkdetails:  # もう更新できないなら処理をやめる
        break

      old_updated_linkdetails = tuple(updated_linkdetails[:])
      
    return tuple(updated_linkdetails)

  def _analyze(self, sentence: str) -> DependencyAnalysisResult:
    chunk_dict, token_dict, _ = self._analyzer.analyze(sentence)
    alloc_dict = self._analyzer.allocate_token_for_chunk(
        chunk_dict, token_dict)
    repr_dict  = self._analyzer.extract_representation(chunk_dict, alloc_dict)
    link_dict  = self._analyzer.make_link_dict(chunk_dict, repr_dict)
    return DependencyAnalysisResult(chunk_dict, token_dict,
                                    alloc_dict, repr_dict, link_dict)

  def _update_attr_dictionary(self, category: str) -> NoReturn:
    """属性辞書の更新
    """
    self._category_to_attrdict = OrderedDict()
    self._category_to_attrdict[category] \
        = self._attrdict_handler.attr_dict(category)
    self._category_to_attrdict[COMMON_DICTIONARY_NAME] = self._common_attr_dict
    self._ja2en = OrderedDict()
    for _category, attrdict in self._category_to_attrdict:
      for attr in attrdict:
        self._ja2en[attr] = self._attrdict_handler.ja2en(_category)[attr]

    self._en2ja = OrderedDict()
    for ja, en in self.ja2en.items():
      self._en2ja[en] = ja

    self._attr_dict = dict()
    for _category, attrdict in self._category_to_attrdict.items():
      for attr, words in attrdict.items():
        self._attr_dict[attr] = words


# ヘルパー関数群
def _is_good_functional_word(functional_word: str) -> bool:
  """数珠繋ぎをしないような機能語であるかをチェックする

  Args:
    functional_word (str): 機能語

  Returns:
    数珠つなぎをしないような機能語ならば True, それ以外は False を返す
  """
  return functional_word != 'の' and \
         functional_word not in PAEALLEL_PRESENTATION_WORDS

def _convert_link_to_flagment(
    link_list: Tuple[int, ...], chunk_dict: ChunkDict) -> str:
  """係り順に文節をつなげる

  Args:
    link_list (Tuple[int, ...]): 係り順を格納したもの
    chunk_dict (ChunkDict): 出現順に文節情報を格納した辞書

  Returns:
    つながった文節
  """
  return ''.join(chunk_dict[link].phrase for link in link_list)
  
def _unique_sort_by_index(iterable: Iterable[Any]) -> Iterable[Any]:
  """重複をなくして出現順にソートする

  Args:
    iterable (Iterable[Any]): 複数の要素をもつオブジェクト

  Returns:
    与えられたiterableから重複をなくして出現順にソートしたもののリスト
  """
  yield from sorted(set(iterable), key=iterable.index)