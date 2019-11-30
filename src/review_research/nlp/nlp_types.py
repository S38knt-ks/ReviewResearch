from typing import NamedTuple, Tuple, Optional, Dict, List, Set

import CaboCha

from ..nlp import ONE_HIRAGANA_REGEX

# CaboChaの解析結果に存在するfeatureの文字列定数
BEGIN_HEAD_SURFACE_MARK = 'RL'
END_HEAD_SURFACE_MARK = 'RH'
BEGIN_FUNC_SURFACE_MARK = 'LF'
END_FUNC_SURFACE_MARK = 'RF'
POS_MARK1 = 'SHP0'
POS_MARK2 = 'DHP0'
POS_MARK3 = 'FHP0'
# 単語として取り出したい品詞一覧
REQUIREMENT_POS_LIST = ('名詞', '形容詞', '動詞', '副詞')

class TokenFeature(NamedTuple):
  """形態素の表層系を除いた情報

  Attributes:
    pos (str): 品詞
    pos_detail1 (str): 品詞細分類1
    pos_detail2 (str): 品詞細分類2
    pos_detail3 (str): 品詞細分類3
    infl_type (str): 活用形
    infl_form (str): 活用型
    base_form (str): 原形
    reading (str): 読み
    phonetic (str): 発音
  """
  pos: str
  pos_detail1: str
  pos_detail2: str
  pos_detail3: str
  infl_type: str
  infl_form: str
  base_form: str
  reading: str
  phonetic: str

  @classmethod
  def from_result(cls, *features: Tuple[str, ...]):
    """解析の結果からTokenを作成

    Args:
      features (Tuple[str]): 表層以外の情報

    Returns:
      TokenFeatureインスタンス
    """
    try:
      token_feature = cls(*features)

    except TypeError:
      num_fields = len(cls._fields)
      dif_fields = len(features) - num_fields
      if dif_fields < 0:
        features = list(features)
        features.extend(['*' for _ in range(abs(dif_fields))])
        return cls(*features)

      else:
        return cls(*features[:num_fields])

    else:
      return token_feature

class Token(NamedTuple):
  """形態素の情報

  参考元: https://github.com/jordwest/mecab-docs-en#usage
  
  Attributes:
    surface (str): 表層形
    pos (str): 品詞
    pos_detail1 (str): 品詞細分類1
    pos_detail2 (str): 品詞細分類2
    pos_detail3 (str): 品詞細分類3
    infl_type (str): 活用形
    infl_form (str): 活用型
    base_form (str): 原形
    reading (str): 読み
    phonetic (str): 発音
  """
  surface: str
  pos: str
  pos_detail1: str
  pos_detail2: str
  pos_detail3: str
  infl_type: str
  infl_form: str
  base_form: str
  reading: str
  phonetic: str

  @classmethod
  def from_mecab_result(cls, surface: str, *features: Tuple[str, ...]):
    """MeCabの形態素解析の結果からTokenを作成

    Args:
      surface (str): 形態素の表層
      features (Tuple[str]): 表層以外の情報

    Returns:
      Tokenインスタンス
    """
    token_feature = TokenFeature.from_result(*features)
    return cls(surface, *token_feature)


class TokenDetail(NamedTuple):
  """形態素情報の詳細

  Attributes:
    surface (str): 表層形
    normalized: 正規化後の形
    feature (TokenFeature): 表層形を除いた形態素情報
    named_entity (str): 固有表現
    chunk (CaboCha.Chunk): 複合語内の単語
  """
  surface: str
  normalized: str
  feature: TokenFeature
  named_entity: str
  info: str
  chunk: CaboCha.Chunk

  @classmethod
  def from_cabocha_token(cls, token: CaboCha.Token):
    feature = token.feature
    token_feature = TokenFeature.from_result(feature.split(','))
    if token_feature.base_form == '*':
      token_feature._replace(base_form=token.surface)

    return cls(token.surface, token.normalized_surface, token_feature,
               token.ne, token.chunk)

class WordRepr(NamedTuple):
  """単語の表現情報
  
  Attributes:
    surface (str): 表層形
    base_form (str): 原形
  """
  surface: str
  base_form: str

  @classmethod
  def from_token(cls, token: Token):
    """TokenインスタンスからWordReprインスタンスを作成

    Args:
      token (Token): Tokenインスタンス

    Returns:
      WordReprインスタンス
    """
    if token.base_form == '*':
      return WordRepr(token.surface, token.surface)

    else:
      return WordRepr(token.surface, token.base_form)

  @classmethod
  def from_token_detail(cls, token_detail: TokenDetail):
    """TokenDetailインスタンスからWordReprインスタンスを作成

    Args:
      token_detail (TokenDetail): TokenDetailインスタンス

    Returns:
      WordReprインスタンス
    """
    base_form = token_detail.feature.base_form
    if base_form == '*':
      return WordRepr(token_detail.surface, token_detail.surface)

    else:
      return WordRepr(token_detail.surface, base_form)


class AttrName(NamedTuple):
  """属性名

  Attributes:
    english (str): 属性の英名
    japanese (str): 属性の和名
  """
  english: str
  japanese: str

class AttrDictInfo(NamedTuple):
  """属性辞書の情報

  Attributes:
    category (str): 商品カテゴリ
    name (AttrName): 属性名
    words (Tuple[str, ...]): 属性語一覧
  """
  category: str
  name: AttrName
  words: Tuple[str, ...]

class Alignment(NamedTuple):
  """表層形と原形の対応付けと、それは単語なのかを表す

  Attributes:
    surface (str): 表層形
    base_form (Optional[str]): 原形または None
    is_word (bool): 単語ならTrue、そうでなければFalse
  """
  surface: str
  base_form: Optional[str]
  is_word: bool

class ChunkDetail(NamedTuple):
  """文節情報

  Attributes:
    phrase (str): 節
    score (float): 接続先との結合度
    next_link (int): 接続先の番号
    number_tokens (int): 形態素の数
    token_position (int): 節の先頭の形態素の文頭からの位置
    head_begin (int): 主辞の先頭位置
    func_begin (int): 機能語の先頭位置
    features (Dict[str, str]): 節内の形態素の詳細
  """
  phrase: str
  score: float
  next_link: int
  number_tokens: int
  token_position: int
  head_begin: int
  func_begin: int
  features: Dict[str, str]

  @classmethod
  def from_phrase_and_chunk(cls, phrase: str, chunk: CaboCha.Chunk):
    features = tuple(str(chunk.feature_list(i))
                     for i in range(chunk.feature_list_size))

    features = dict()
    for feature in features:
      tmp = feature.split(':')
      key = tmp[0]
      val = ''.join(t for t in tmp[1:])
      features[key] = val

    return cls(phrase, chunk.score, chunk.link, chunk.token_size,
               chunk.token_pos, chunk.head_pos, chunk.func_pos, features)

class PhraseDetail(NamedTuple):
  """文節の詳細情報

  head_surface (str): 主辞の表層
  head_words (Tuple[WordRepr, ...]): 主辞内の単語
  part_of_speech (str): 主辞の品詞
  functional_word (str): 機能語
  """
  head_surface: str
  head_words: Tuple[WordRepr, ...]
  part_of_speech: str
  functional_word: str

  @classmethod
  def from_analysis_result(cls, chunk_detail: ChunkDetail, 
                           tokens: Tuple[TokenDetail, ...]):
    """CaboChaが解析した情報から、人間がわかりやすい文節情報を取り出す

    Args:
      chunk_detail (ChunkDetail): 文節情報
      tokens (Tuple[TokenDetail, ...]): 文節内の形態素

    Returns:
      詳細な文節情報を格納したPhraseDetailインスタンス
    """
    chunk_feature = chunk_detail.features
    begin_head_surface = chunk_feature[BEGIN_HEAD_SURFACE_MARK]
    end_head_surface   = chunk_feature[END_HEAD_SURFACE_MARK]
    begin_func_surface = chunk_feature[BEGIN_FUNC_SURFACE_MARK]
    end_func_surface   = chunk_feature[END_FUNC_SURFACE_MARK]

    head_tokens = _search_tokens_range(begin_head_surface, 
                                       end_head_surface,
                                       tokens)
    func_tokens = _search_tokens_range(begin_func_surface,
                                       end_func_surface,
                                       tokens)

    head_words = []
    for token in head_tokens:
      is_one_hiragana = ONE_HIRAGANA_REGEX.match(token.surface)
      if token.feature.pos in REQUIREMENT_POS_LIST and not is_one_hiragana:
        head_words.append(WordRepr.from_token_detail(token))

    head_words = tuple(head_words)
    functional_word = ''.join(ft.surface for ft in func_tokens)
    part_of_speech = _extract_phrase_part_of_speech(chunk_feature)

    if len(head_tokens) == 1:
      head_surface = head_tokens[0].surface
      return cls(head_surface, head_words, part_of_speech, functional_word)

    else:
      # 主辞としたいものの周りに記号がある場合は、その記号を除去する
      if head_tokens[0].feature.pos == '記号':
        head_tokens.remove(head_tokens[0])

      if head_tokens[-1].feature.pos == '記号':
        head_tokens.remove(head_tokens[-1])

      # 形態素の表層をくっつけて文節の主辞とする
      head_surface = ''.join(t.surface for t in head_tokens)
      return cls(head_surface, head_words, part_of_speech, functional_word)

class LinkDetail(NamedTuple):
  """係り受け構造

  Attributes:
    phrase_id (int): 文節の出現番号
    phrase_detail (PhraseDetail): 文節情報
  """
  phrase_id: int
  phrase_detail: PhraseDetail

class AttrExtractionResult(NamedTuple):
  """属性抽出の結果を格納

  Attributes:
    attributions (Set[str]): 抽出できた属性
    flagment (str): 係り受け関係をつなげたもの
    candidate_terms (Set[str]): 属性候補語一覧
    hit_terms (Set[str]): 属性語として抽出された語群
    phrases (Set[str]): 文節一覧
    num_phrases (int): 文節数
  """
  attributions: Set[str]
  flagment: str
  candidate_terms: Set[str]
  hit_terms: Set[str]
  phrases: Set[str]
  num_phrases: int

class AttrExtractionInfo(NamedTuple):
  """属性抽出の結果を格納

  Attributes:
    flagment (str): 係り受け関係をつなげたもの
    candidate_terms (Set[str]): 属性候補語一覧
    hit_terms (Set[str]): 属性語として抽出された語群
    phrases (Set[str]): 文節一覧
    num_phrases (int): 文節数
  """
  flagment: str
  candidate_terms: Set[str]
  hit_terms: Set[str]
  phrases: Set[str]
  num_phrases: int

  @classmethod
  def from_result(cls, attr_extraction_result: AttrExtractionResult):
    """属性抽出の結果からインスタンスを生成する

    Args:
      attr_extraction_result (AttrExtractionResult): 属性抽出の結果

    Returns:
      AttrExtractionInfoインスタンス
    """
    return cls(attr_extraction_result.fragment,
               attr_extraction_result.candidate_terms,
               attr_extraction_result.hit_terms,
               attr_extraction_result.phrases,
               attr_extraction_result.num_phrases)


## ヘルパー関数
def _extract_phrase_part_of_speech(chunk_feature: Dict[str, str]) -> str:
  """文節内の主辞の品詞を抽出

  Args:
    chunk_feature: 節内の形態素の詳細

  Returns:
    主辞の品詞
  """
  pos = ''
  try:
    pos = chunk_feature[POS_MARK1]
  except KeyError:
      try:
        pos = chunk_feature[POS_MARK2]
      except KeyError:
        try:
          pos = chunk_feature[POS_MARK3]
        except:
          return pos
        else:
          return pos
      else:
        return pos
  else:
    return pos

def _search_tokens_range(begin_surface: str, end_surface: str,
                         tokens: Dict[str, TokenDetail]) -> List[TokenDetail]:
  """与えられた形態素で囲まれた形態素を返す

  Args:
    begin_surface (str): 始まりの形態素の表層
    end_surface (str): 終わりの形態素の表層
    tokens (Dict[str, TokenDetail]): 出現する全ての形態素
  
  Returns:
    begin_surfaceからend_surfaceまでの形態素
  """
  begin_index = 0
  for token_id, token in tokens.items():
    if token.surface == begin_surface:
      begin_index = token_id

  if begin_surface == end_surface:
    end_index = begin_index

  else:
    end_index = 0
    for token_id, token in reversed(tokens.items()):
      if token.surface == end_surface:
        end_index = token_id

  searched_tokens = [t for i, t in tokens.items()
                     if i in range(begin_index, end_index+1)]
  return searched_tokens