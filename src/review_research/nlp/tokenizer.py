import sys
from collections import namedtuple, OrderedDict
from typing import List, Iterator

from ..nlp import ONE_HIRAGANA_REGEX
from ..nlp import HIRAGANAS_REGEX
from ..nlp import MECAB_RESULT_SPLIT_REGEX
from ..nlp import MecabTaggerSingleton
from ..nlp import Token
from ..nlp import WordRepr
from ..nlp import StopwordRemover

DEFAULT_POS = tuple(['名詞', '動詞', '形容詞'])
ALL_POS     = DEFAULT_POS + tuple(['副詞', '助詞', '助動詞', '記号'])

class Tokenizer(object):
  """
  形態素解析器のラッパー

  Usage:
    >>> tokenizer = Tokenizer()
    >>> text = '何らかの文章'
    >>> word_list = tokenizer.get_baseforms(text)
  """
  _tagger = None

  def __init__(self):
    self.remover = StopwordRemover()

  @property
  def tagger(self):
    return MecabTaggerSingleton.get_instance()

  def get_baseforms(self, text: str, 
                    remove_stopwords = True, remove_a_hiragana = True, 
                    pos_list: List[str] = DEFAULT_POS) -> List[WordRepr]:
    """形態素解析で得られた結果における原形(または表層)をリスト化して返す

    Params:
      text (str): 形態素解析にかけたい文

      pos_list (List[str]): 
        品詞のフィルタリングに使うリスト
        (default ['名詞', '動詞', '形容詞'])

    Returns
      pos_listでフィルタリングされて残った、原形(または表層)の単語リスト
    """
    if pos_list is None:
      words = [WordRepr.from_token(t) for t in self._tokenize(text)]

    else:  
      words = [WordRepr.from_token(t) for t in self._tokenize(text) 
               if t.pos in pos_list]

    if remove_stopwords:
      words = self.remover(words)
            
    if remove_a_hiragana:
      words = [w for w in words if not is_a_hiragana(w)]

    return words

  def _tokenize(self, text: str) -> Iterator[Token]:
    """形態素解析のラッパーメソッド

    Args:
      text (str): 文

    Yields:
      Tokenインスタンスのジェネレータ
    """
    self.tagger.parse('')  # 形態素解析器の初期設定
    result = self.tagger.parse(text)
    lines = result.strip().split('\n')
    chunk_list = [MECAB_RESULT_SPLIT_REGEX.split(line) for line in lines 
                  if line != u'EOS']
    for chunks in chunk_list:
      if len(chunks) <= 1:
        continue

      surface, *features = chunks
      yield Token.from_mecab_result(surface, *features)


def is_a_hiragana(word: WordRepr) -> bool:
  """与えられた単語が1文字の平仮名かどうかのチェック

  Args:
    word (WordRepr): 単語

  Returns:
    wordが1文字の平仮名ならTrue、そうでなければFalse
  """
  one_match = ONE_HIRAGANA_REGEX.match(word.base_form)
  series_match = HIRAGANAS_REGEX.match(word.base_form)
  is_a_hiragana_word = one_match is not None and series_match is None
  return is_a_hiragana_word and len(word.surface) == 1