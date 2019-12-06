import argparse
import re
from collections import namedtuple
from typing import List, NoReturn

import emoji

from ..nlp import PERIOD_SEQ_REGEX
from ..nlp import Tokenizer
from ..nlp import WordRepr
from ..nlp import Alignment

REPLACE_MARK = '<<REPL>>'

class TextAlignment:
  """文と文中の単語を対応付けるためのクラス

  Attributes:
    text (str): 対応付けに使用した文
    alignment (List[Alignment]): 文(self.text)中の対応関係
    words (List[WordRepr]): 文(self.text)中の単語
  """

  def __init__(self):
    self._alignment_list = None
    self._words          = None
    self._text           = ''
    self._tokenizer      = Tokenizer()
  
  @property
  def alignment(self) -> List[Alignment]:
    return self._alignment_list

  @property
  def words(self) -> List[WordRepr]:
    return self._words

  def __call__(self, text: str) -> NoReturn:
    """alignメソッドを呼び出す

    Args:
      text (str): 文
    """
    self.align(text)

  @property
  def text(self) -> str:
    return self._text

  def align(self, text: str) -> NoReturn:
    """与えられた文における表層形と単語の原形を対応付ける
    表層と単語の原形が同じ場合はそのまま対応付ける

    Args:
      text (str): 文
    """
    self._text = _fix_text(text)
    self._words = self._tokenizer.get_baseforms(text)
    self._alignment_list = []
    target = self.text[:]
    for w in self.words:
      start_idx = target.find(w.surface)
      if start_idx == -1:
          continue

      target = target.replace(w.surface, REPLACE_MARK, 1)
      if start_idx > 0:
        # 文の先頭に単語の表層形がなければ、その単語までの部分を元の文と対応付ける
        part = target.split(REPLACE_MARK)[0]
        self._alignment_list.append(Alignment(part, None, False))
        target = target.replace(part, REPLACE_MARK, 1)

      self._alignment_list.append(Alignment(w.surface, w.base_form, True))
      target = target.replace(REPLACE_MARK, '')

    # すべての単語を対応付けた後に文が残っていれば、その部分を元の文と対応付ける
    if len(target) > 0:
      self._alignment_list.append(Alignment(target, None, False))

  
def _fix_text(text: str) -> str:
  """絵文字を消したり「。」が2つ以上続いている箇所を「。」1つに直す

  Args:
    text (str): レビュー文

  Returns:
    修正された文章
  """
  fixed_text = ''.join(c for c in text if c not in emoji.UNICODE_EMOJI)

  match = PERIOD_SEQ_REGEX.search(fixed_text)
  if match:
    print(match)
    fixed_text = PERIOD_SEQ_REGEX.sub('。', fixed_text)

  if fixed_text.find('\n') == -1:
    return fixed_text

  else:
    fixed_text = ''.join(sentence.strip() for sentence in text.split('\n'))
    return fixed_text



