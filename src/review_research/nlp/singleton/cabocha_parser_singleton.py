from threading import Lock

import CaboCha

from review_research.nlp import NeologdDirectoryPathBuilder

class CabochaParserSingleton(object):
  """係り受け解析器のシングルトンを有するクラス

  複数Cabocha.Parserインスタンスを起動させると期待する出力をしない可能性があるため、  
  シングルトンパターンによる実装を行った
  """

  _cabocha_parser = None  # type: CaboCha.Parser
  _lock = Lock()

  def __new__(cls):
    raise NotImplementedError('Cannot initialize using constructor.')

  @classmethod
  def __internal_new__(cls):
    return super().__new__(cls)

  @classmethod
  def get_instance(cls) -> CaboCha.Parser:
    if not cls._cabocha_parser:
      with cls._lock:
        # わずかに前に初期化されている可能性があるため、ifブロックを追加
        if not cls._cabocha_parser:
          neologd_path = NeologdDirectoryPathBuilder.get_path()
          try:
            arg = 'Ochasen -d {}'.format(neologd_path)
            cls._cabocha_parser = CaboCha.Parser(arg)

          except RuntimeError:
            cls._cabocha_parser = CaboCha.Parser('Ochasen')

    return cls._cabocha_parser
