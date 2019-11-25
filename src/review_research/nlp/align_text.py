import argparse
import re
from collections import namedtuple
from typing import List

import emoji

from ..nlp import Tokenizer, Word

ALIGNMENT_FIELDS = ['surface', 'word', 'is_token']
Alignment = namedtuple('Alignment', ALIGNMENT_FIELDS)

REPLACE_MARK = '<<REPL>>'

class TextAlignment:


  def __init__(self):
    self._alignment_list  = None
    self._words           = None
    self._text            = ''
    self._tokenizer       = Tokenizer()

    self._periods_pat = re.compile(r'。{2,}')
  
  @property
  def alignment(self) -> List[Alignment]:
    return self._alignment_list

  @property
  def words(self) -> List[Word]:
    return self._words

  @property
  def text(self) -> str:
    return self._text

  def align(self, text: str):
    """表層と単語の原形を対応付ける
    表層と単語の原形が同じ場合はそのまま対応付ける
    """
    self._text = self._adjust_text(text)
    self._words = self._tokenizer.get_baseforms(text)
    self._alignment_list = []
    target = self.text[:]
    for w in self.words:
      start_idx = target.find(w.surface)
      if start_idx == -1:
          continue

      target = target.replace(w.surface, REPLACE_MARK, 1)

      if start_idx > 0:
        part = target.split(REPLACE_MARK)[0]
        self._alignment_list.append(Alignment(part, part, False))
        target = target.replace(part, REPLACE_MARK, 1)

      self._alignment_list.append(Alignment(w.surface, w.word, True))
      target = target.replace(REPLACE_MARK, '')

    if len(target) > 0:
      self._alignment_list.append(Alignment(target, target, False))

  
  def _adjust_text(self, text: str) -> str:
    """絵文字を消したり「。」が2つ以上続いている箇所を「。」1つに直す

    Params:
      text: レビュー文
    Return:
      修正された文章
    """
    if text.find('\n') == -1:
      return text

    adjusted_text = ''.join(c for c in text if c not in emoji.UNICODE_EMOJI)
    if text.find('。') != -1:
      adjusted_text = self._periods_pat.sub('。', adjusted_text)

    adjusted_text = ''.join(sentence.strip() for sentence in text.split('\n'))
    return adjusted_text



