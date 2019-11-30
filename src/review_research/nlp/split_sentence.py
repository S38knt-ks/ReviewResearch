import re
from collections import OrderedDict
from typing import Dict, List

REP_MARK = '<SENTENCE>'

class Splitter(object):
  """文章分割を行う

  Usage:
    >>> sentence = '分割したい文章。デフォルトは句点が1個以上連続している箇所を区切りとする。'
    >>> splitter = Splitter()
    >>> result = splitter.split_sentence(sentence)
    
    分割は以下の呼び出しでも可能
    >>> result = splitter(sentence)
  """
    
  def __init__(self, pattern: str = r'。+\s*'):
    """文章の分割に使う正規表現を指定

    Args:
      pattern (str): 分割の正規表現
    """
    self._sep_regex = re.compile(pattern)

  def __call__(self, sentence: str) -> Dict[int, str]:
    """split_sentenceメソッドの呼び出し

    Args:
      sentence (str): 文章

    Returns:
      split_sentenceメソッドの戻り値
    """
    return self.split_sentence(sentence)

  def split_sentence(self, sentence: str) -> Dict[int, str]:
    """文章を一文毎に区切る

    Args:
      sentence (str): 文章

    Returns:
      文の出現順に文とその文を区切ったもの（空白の場合もある）を結合したものを格納した辞書
    """
    text_list = self._sep_regex.split(sentence)
    rep_text = sentence[:]
    for s in text_list:
      if s != '':
        rep_text = rep_text.replace(s, REP_MARK, 1)

    separators = [sep for sep in rep_text.split(REP_MARK) if sep != '']
    
    # 区切り文字の数が文章中の文の数と対応付かない場合
    if len(text_list) != len(separators):
      diff = len(text_list) - len(separators)
      for _ in range(diff):
        separators.append('')

    id_to_text = OrderedDict()
    text_index = 0
    for text, separator in zip(text_list, separators):
      if text:
        sentence = text + separator
        id_to_text[text_index] = sentence.strip()
        text_index += 1

    return id_to_text