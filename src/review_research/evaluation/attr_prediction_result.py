import pathlib
import json
from collections import OrderedDict
from typing import Tuple, Dict, Any, Union, NamedTuple, NoReturn

from review_research.review import StarsDistribution
from ..evaluation import ReviewTextInfo

class AttrPredictionResult(NamedTuple):
  """属性抽出予測の結果

  Attributes:
    input_file (Union[str, pathlib.Path]): 入力に使ったファイル名
    product (str): 商品名
    link (str): 商品レビューページへの URL
    maker (str): 企業名
    average_stars (float): 平均評価
    stars_distribution (StarsDistribution): 評価分布
    total_review (int): 総レビュー数
    total_sentence (int): 総文数
    sentences (Tuple[ReviewTextInfo, ...]): 抽出情報
  """
  input_file: Union[str, pathlib.Path]
  product: str
  link: str
  maker: str
  average_stars: float
  stars_distribution: StarsDistribution
  total_review: int
  total_sentence: int
  sentences: Tuple[ReviewTextInfo, ...]

  @classmethod
  def load(cls, json_path: Union[str, pathlib.Path]):
    json_path = pathlib.Path(json_path)
    data = json.load(json_path.open('r', encoding='utf-8'),
                     object_pairs_hook=OrderedDict)
    input_file = data['input_file']
    product = data['product']
    link = data['link']
    maker = data['maker']
    average_stars = data['average_stars']
    stars_distribution = StarsDistribution(**data['stars_distribution'])
    total_review = data['total_review']
    total_sentence = data['total_sentence']
    sentences = tuple(ReviewTextInfo._make(sentence) 
                      for sentence in data['sentences'])
    return cls(input_file, product, link, maker, average_stars,
               stars_distribution, total_review, total_sentence, sentences)

  def dump(self, json_path: Union[str, pathlib.Path]) -> NoReturn:
    """JSON形式で保存する

    Args:
      json_path (Union[str, pathlib.Path]): 保存ファイル名
    """
    out_data = OrderedDict()
    out_data['input_file'] = str(self.input_file)
    out_data['product'] = self.product
    out_data['link'] = self.link
    out_data['maker'] = self.maker
    out_data['average_stars'] = self.average_stars
    out_data['stars_distribution'] = self.stars_distribution
    out_data['total_review'] = self.total_review
    out_data['total_sentence'] = self.total_sentence
    out_data['sentences'] = [sentence._asdict() for sentence in self.sentences]

    json_path = pathlib.Path(json_path)
    json.dump(out_data, json_path.open('w', encoding='utf-8'),
              ensure_ascii=False, indent=4)
