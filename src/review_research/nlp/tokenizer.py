import re
from collections import namedtuple, OrderedDict
from typing import List

import MeCab

from ..nlp import StopwordRemover

TOKEN_LIST = ['surface',
              'pos',
              'pos_detail1',
              'pos_detail2',
              'pos_detail3',
              'infl_type',
              'infl_form',
              'base_form',
              'reading',
              'phonetic']
Token = namedtuple('Token', TOKEN_LIST)
TOKEN_TUPLE = Token(*TOKEN_LIST)

WORD_FIELDS = [TOKEN_TUPLE.surface, 'word']
Word = namedtuple('Word', WORD_FIELDS)

DEFAULT_POS = tuple(['名詞', '動詞', '形容詞'])
ALL_POS     = DEFAULT_POS + tuple(['副詞', '助詞', '助動詞', '記号'])

TOTAL_FEATURES = 9

class Tokenizer:
  """
  Usage:
    >>> tokenizer = Tokenizer()
    >>> text = '何らかの文章'
    >>> word_list = tokenizer.get_baseforms(text)
  """

  def __init__(self):
    self._tagger  = MeCab.Tagger('Ochasen')
    self._pat_obj = re.compile('\t|,')
    self.remover = StopwordRemover()

  def get_baseforms(self, text: str, 
                    remove_stopwords=True, remove_a_hiragana=True, 
                    pos_list: List[str]=DEFAULT_POS) -> List[Word]:
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
      words = [decide_word(t) for t in self._tokenize(text)]

    else:  
      words = [decide_word(t) for t in self._tokenize(text) 
               if t.pos in pos_list]

    if remove_stopwords:
        words = self.remover.remove(words)
            
    if remove_a_hiragana:
        words = [w for w in words if not is_a_hiragana(w)]

    return words


  def _tokenize(self, text: str):
    self._tagger.parse('')
    result = self._tagger.parse(text)
    sentences = result.strip().split('\n')
    chunk_list = [self._pat_obj.split(line) for line in sentences 
                  if line != u'EOS']
    for chunks in chunk_list:
      if len(chunks) <= 1:
        continue

      surface, *feature = chunks
      num_features = len(feature)
      if num_features == TOTAL_FEATURES:
        yield Token(surface, *feature)

      # print(feature)
      elif num_features < TOTAL_FEATURES:
        lack = TOTAL_FEATURES - num_features
        feature.extend(['' for _ in range(lack)])
        yield Token(surface, *feature)

      else:
        yield Token(surface, *feature[:TOTAL_FEATURES])


def decide_word(token: Token) -> Word:
  if token.base_form == '*':
    return Word(token.surface, token.surface)

  else:
    return Word(token.surface, token.base_form)

ONE_HIRAGANA_REGEX = re.compile(r'[ぁ-ん]')
HIRAGANAS_REGEX = re.compile(r'[ぁ-ん]{2,}')

def is_a_hiragana(word: Word) -> bool:
  one_match = ONE_HIRAGANA_REGEX.match(word.word)
  series_match = HIRAGANAS_REGEX.match(word.word)
  is_a_hiragana_word = one_match is not None and series_match is None
  return is_a_hiragana_word and len(word.surface) == 1