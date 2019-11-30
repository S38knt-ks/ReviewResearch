import re
from pprint import pprint
from typing import List
from pathlib import Path

from ..nlp import WordRepr
from ..nlp import StopwordDictionaryPathBuilder

class StopwordRemover(object):
  """ストップワードを削除するクラス
  
  Usage:
    >>> stopword_remover = StopwordRemover()
    >>> applied = stopword_remover.remove(words)  # wordsはWordインスタンスのリスト
  """

  def __init__(self):
    
    dictionary_path = StopwordDictionaryPathBuilder.get_path()
    with dictionary_path.open(mode='r', encoding='utf-8') as fp:
      stopword_list = [w.strip() for w in fp.readlines()]

    self.stopwords = [w for w in stopword_list if w is not '']

  def __call__(self, word_list: List[WordRepr]) -> List[WordRepr]:
    return self.remove(word_list)

  def remove(self, word_list: List[WordRepr]) -> List[WordRepr]:
    """ストップワードを削除する

    Args:
      word_list (List[WordRepr]): 単語一覧

    Returns
      word_listからストップワードを削除した単語一覧
    """
    removed_word_list = [w for w in word_list if w.base_form not in self.stopwords]
    return removed_word_list

StopwordRemover.__call__.__doc__ = StopwordRemover.remove.__doc__

def main():
  sr = StopwordRemover()
  pprint(sr.stopwords)

if __name__ == "__main__":
  main()