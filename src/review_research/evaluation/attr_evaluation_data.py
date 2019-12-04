import pathlib
import json
from collections import OrderedDict
from typing import NamedTuple, Tuple, Union, NoReturn, Dict, Any

class AttrAnnotation(NamedTuple):
  """アノテーション用のデータ

  Attributes:
    name (str): 属性名
    label (int): 正解ラベル
  """
  name: str
  label: int

class TextWithAttrAnnotation(NamedTuple):
  """レビュー文中の各文にアノテーション用のデータを付与したもの

  Attributes:
    review_id (int): レビュー番号
    last_review_id (int): 最後のレビュー番号
    review (str): レビュー本文
    text_id (int): 文の番号
    last_text_id (int): 最後の文の番号
    text (str): アノテーションを付与したい文
    attributes (Tuple[AttrAnnotation, ...]): アノテーション用のデータ
  """
  review_id: int
  last_review_id: int
  review: str
  text_id: int
  last_text_id: int
  text: str
  attributes: Tuple[AttrAnnotation, ...]

  @classmethod
  def from_json_content(cls, content: Dict[str, Any]):
    """JSON ファイルから読み取った辞書情報を基にインスタンス化

    Args:
      content (Dict[str, Any]): JSON ファイルから読み取った辞書

    Returns:
      TextWithAttrAnnotationインスタンス
    """
    this = cls(**content)
    attributes = tuple(AttrAnnotation(**attribute) 
                       for attribute in this.attributes)
    return this._replace(attributes=attributes)

class AttrEvaluationData(NamedTuple):
  """属性抽出の評価をするためのデータ

  Attributes:
    category (str): 商品カテゴリ
    product (str): 商品名
    total_review (int): 総レビュー数
    total_text (int): 総文数
    texts (Tuple[TextWithAttrAnnotation, ...]): 正解データ一覧
  """
  category: str
  product: str
  total_review: int
  total_text: int
  texts: Tuple[TextWithAttrAnnotation, ...]

  @classmethod
  def load(cls, jsonpath: Union[str, pathlib.Path]):
    """JSON ファイルからインスタンス化

    Args:
      jsonpath (Union[str, pathlib.Path]): JSON ファイルのパス

    Returns:
      AttrEvaluationDataインスタンス
    """
    jsonpath = pathlib.Path(jsonpath)
    data = json.load(jsonpath.open('r', encoding='utf-8'),
                     object_pairs_hook=OrderedDict)
    # category = data['category']
    category = ''
    product = data['product']
    total_review = data['total_review']
    total_text = data['total_text']
    texts = tuple(TextWithAttrAnnotation.from_json_content(text)
                  for text in data['texts'])
    return cls(category, product, total_review, total_text, texts)

  def dump(self, jsonpath: Union[str, pathlib.Path]) -> NoReturn:
    """JSON 形式で保存する

    Args:
      jsonpath (Union[str, pathlib.Path]): 保存ファイルパス
    """
    out_data = OrderedDict()
    out_data['category'] = self.category
    out_data['product'] = self.product
    out_data['total_review'] = self.total_review
    out_data['total_text'] = self.total_text
    texts = []
    for text in self.texts:
      text_data = text._asdict()
      text_data['attributes'] = [attribute._asdict() 
                                 for attribute in text_data.attributes]
      texts.append(text_data)

    out_data['text'] = texts
    jsonpath = pathlib.Path(jsonpath)
    json.dump(out_data, jsonpath.open('w', encoding='utf-8'),
              ensure_ascii=False, indent=4)