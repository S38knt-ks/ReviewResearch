import sys
from threading import Lock

import MeCab

from review_research.nlp import NeologdDirectoryPathBuilder

class MecabTaggerSingleton(object):
  """形態素解析器のシングルトンを有するクラス

  複数MeCab.Taggerインスタンスを起動させると期待する出力をしない可能性があるため、  
  シングルトンパターンによる実装を行った
  """

  _mecab_tagger = None  # type: MeCab.Tagger
  _lock = Lock()

  def __new__(cls):
    raise NotImplementedError('Cannot initialize using constructor.')

  @classmethod
  def __internal_new__(cls):
    return super().__new__(cls)

  @classmethod
  def get_instance(cls) -> MeCab.Tagger:
    if not cls._mecab_tagger:
      with cls._lock:
        # わずかに前に初期化されている可能性があるため、ifブロックを追加
        if not cls._mecab_tagger:
          neologd_path = NeologdDirectoryPathBuilder.get_path()
          try:
            arg = 'Ochasen -d {}'.format(neologd_path)
            cls._mecab_tagger = MeCab.Tagger(arg)

          except RuntimeError:
            msg = 'Cannot use dictionary in "{}". So use default dictionary.'
            print(msg.format(neologd_path), file=sys.stderr)
            cls._mecab_tagger = MeCab.Tagger('Ochasen')

    return cls._mecab_tagger
