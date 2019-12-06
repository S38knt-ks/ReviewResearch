import pathlib
import json
from collections import OrderedDict
from typing import Tuple, Dict, Any, Union, NamedTuple, NoReturn, Optional

from review_research.review import StarsDistribution
from ..nlp import AttrExtractionResult

class ReviewTextInfo(NamedTuple):
  """商品レビュー内の1文に関する情報

  Attributes:
    review_id (int): レビュー番号
    last_review_id (int): 最後のレビュー番号
    text_id (int): 文番号
    last_text_id (int): 最後の文番号
    star (float): 評価
    title (str): レビューのタイトル
    review (str): レビュー全文
    text (str): 対象としている文
    result Optional(Dict[str, Tuple(AttrExtractionResult, ...)]): 抽出結果
  """
  review_id: int
  last_review_id: int
  text_id: int
  last_text_id: int
  star: float
  title: str
  review: str
  text: str
  result: Optional(Dict[str, Tuple(AttrExtractionResult, ...)])

  @classmethod
  def from_dictionary(cls, dictionary: Dict[str, Any]):
    this = cls(**dictionary)
    result_dict = this.result
    for attr, results in result_dict.items():
      result_dict[attr] = AttrExtractionResult(*results)

    return this._replace(result=result_dict)

class AttrPredictionResult(NamedTuple):
  """属性抽出予測の結果

  Attributes:
    input_file (Union[str, pathlib.Path]): 入力に使ったファイル名
    category (str): 商品カテゴリ
    product (str): 商品名
    link (str): 商品レビューページへの URL
    maker (str): 企業名
    average_stars (float): 平均評価
    stars_distribution (StarsDistribution): 評価分布
    total_review (int): 総レビュー数
    total_text (int): 総文数
    texts (Tuple[ReviewTextInfo, ...]): 抽出情報
  """
  input_file: Union[str, pathlib.Path]
  category: str
  product: str
  link: str
  maker: str
  average_stars: float
  stars_distribution: StarsDistribution
  total_review: int
  total_text: int
  texts: Tuple[ReviewTextInfo, ...]

  @classmethod
  def load(cls, json_path: Union[str, pathlib.Path]):
    json_path = pathlib.Path(json_path)
    data = json.load(json_path.open('r', encoding='utf-8'),
                     object_pairs_hook=OrderedDict)
    input_file = data['input_file']
    category = data['category']
    product = data['product']
    link = data['link']
    maker = data['maker']
    average_stars = data['average_stars']
    stars_distribution = StarsDistribution(**data['star_distribution'])
    total_review = data['total_review']
    total_text = data['total_text']
    texts = tuple(ReviewTextInfo.from_dictionary(text) 
                  for text in data['texts'])
    return cls(input_file, category, product, link, maker, average_stars,
               stars_distribution, total_review, total_text, texts)

  def dump(self, json_path: Union[str, pathlib.Path]) -> NoReturn:
    """JSON形式で保存する

    Args:
      json_path (Union[str, pathlib.Path]): 保存ファイル名
    """
    out_data = OrderedDict()
    out_data['input_file'] = str(self.input_file)
    out_data['category'] = self.category
    out_data['product'] = self.product
    out_data['link'] = self.link
    out_data['maker'] = self.maker
    out_data['average_stars'] = self.average_stars
    out_data['stars_distribution'] = self.stars_distribution
    out_data['total_review'] = self.total_review
    out_data['total_text'] = self.total_text
    out_data['texts'] = [sentence._asdict() for sentence in self.texts]

    json_path = pathlib.Path(json_path)
    json.dump(out_data, json_path.open('w', encoding='utf-8'),
              ensure_ascii=False, indent=4)
