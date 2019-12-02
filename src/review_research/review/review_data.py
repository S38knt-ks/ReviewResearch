import json
import pathlib
import inspect
from collections import namedtuple, OrderedDict
from collections.abc import Sequence, Mapping
from typing import Union, Tuple, Iterable, NoReturn

INFO_FIELDS = ['date',    # 日付
               'star',    # 評価の星の数
               'vote',    # 投票数(「 x 人のお客様がこれが役に立ったと考えています」における x)
               'name',    # レビュアー名
               'title',   # レビューのタイトル
               'review',] # レビュー文
ReviewInfo = namedtuple('ReviewInfo', INFO_FIELDS)

STARS_DISTRIBUTION = ['star1', 'star2', 'star3', 'star4', 'star5']
StarsDistribution = namedtuple('StarsDistribution', STARS_DISTRIBUTION)

class ReviewPageJSON(object):
  """Amazonのレビューページに記載されている情報を格納するためのデータオブジェクト
  JSON形式で保存したり、JSONからインスタンス化することもできる

  Attributes:
    link (str): レビューページのURL
    maker (str): 製造企業名
    product (str): 商品名
    category (str): 商品カテゴリ名
    average_stars (float): 平均評価
    total_reviews (int): 総レビュー数
    real_reviews (int): 実際のレビュー数(ある程度の数だけ抽出したときは、total_reviewsと一致しない)
    stars_distribution (StarsDistribution): 評価分布
    reviews (Union[Tuple[()], Tuple[ReviewInfo, ...]]): レビュー文の一覧

  Usage:
    インスタンス生成
    >>> review_data = ReviewPageJSON()
    >>> review_data.link = 'https://www.amazon.com'
    >>> ...

    JSON形式で保存
    >>> review_data.dump('review.json')

    JSONファイルからインスタンス化
    >>> review_data = ReviewPageJSON.load('review.json')
  """
  codec = 'utf-8'
  
  def __init__(
      self, link: str = '', maker: str = '', product: str = '', 
      category: str = '', average_stars: float = 0.0, 
      total_reviews: int = 0, real_reviews: int = 0, 
      stars_distribution:StarsDistribution = StarsDistribution(0, 0, 0, 0, 0),
      reviews: Union[Tuple[()], Tuple[ReviewInfo, ...]] = tuple()):
    self.link = link
    self.maker = maker
    self.product = product
    self.category = category
    self.average_stars = average_stars
    self.total_reviews = total_reviews
    self.real_reviews = real_reviews
    self.stars_distribution = stars_distribution
    self.reviews = reviews
    
    # JSONに保存するための辞書型オブジェクト
    self._data = OrderedDict()

  @property
  def stars_distribution(self) -> StarsDistribution:
    return self.__stars_distribution

  @stars_distribution.setter
  def stars_distribution(self, value: Iterable[float]):
    value_class = value.__class__
    if isinstance(value, StarsDistribution):
      self.__stars_distribution = value

    elif issubclass(value_class, Sequence):
      self.__stars_distribution = StarsDistribution._make(value)

    elif issubclass(value_class, Mapping):
      self.__stars_distribution = StarsDistribution._make(value.values())

    else:
      msg = '{}"" requires Sequence or Mapping instance'
      raise ValueError(msg.format('stars_distribution'))

  @property
  def reviews(self) -> Tuple[str, ...]:
    return self.__reviews

  @reviews.setter
  def reviews(self, values: Iterable[str]):
    values = tuple(values)
    if len(values) == 0:
      self.__reviews = values

    else:
      if issubclass(values[0].__class__, Sequence):
        self.__reviews = tuple(ReviewInfo(*v) for v in values)

      else:  
        self.__reviews = tuple(ReviewInfo(**v) for v in values)

    self.real_reviews = len(self.__reviews)

  def build(self) -> NoReturn:
    """JSONファイルへのデータ準備を行うメソッド"""
    self._data.update([(k, v) for k, v in self.__dict__.items()
                       if not str(k).startswith('_')])

    property_attrs = dict()
    property_names = inspect.getmembers(ReviewPageJSON, 
                                        lambda o: isinstance(o, property))
    for property_name, _ in property_names:
      for name, obj in self.__dict__.items():
        if name.endswith(property_name):
          property_attrs[property_name] = obj

    properties = sorted(property_attrs.items(),
                        key=lambda item: item[0], reverse=True)
    for name, obj in properties:
      if isinstance(obj, StarsDistribution):
        self._data[name] = OrderedDict(obj._asdict())

      else:
        self._data[name] = [OrderedDict(review_info._asdict()) 
                            for review_info in obj]

  @classmethod
  def load(cls, json_path: Union[str, pathlib.Path]):
      """JSONで保存されているデータをインスタンスに登録する

      Params:
        json_path: .jsonファイルのパス

      Returns:
        ReviewPageJSONインスタンス
      """
      json_path = pathlib.Path(json_path)
      review_page = json.load(json_path.open(mode='r', encoding=cls.codec),
                              object_pairs_hook=OrderedDict)
      return cls(**review_page)
      

  def dump(self, path: Union[str, pathlib.Path]) -> NoReturn:
    """インスタンスに登録されているデータをJSON形式で保存する

    Params:
      path: jsonの保存パス
    """
    path = pathlib.Path(path)
    self.build()
    json.dump(self._data, path.open(mode='r', encoding=self.codec),
              ensure_ascii=False, indent=4)
      