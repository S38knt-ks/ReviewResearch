import json
import pathlib
import inspect

from collections import namedtuple, OrderedDict
from collections.abc import Sequence, Mapping

INFO_FIELDS = ['date',   # 日付
               'star',   # 評価の星の数
               'vote',   # 投票数（「x人のお客様がこれが役に立ったと考えています」におけるx）
               'name',   # レビュアー名
               'title',  # レビューのタイトル
               'review'] # レビュー文
ReviewInfo = namedtuple('ReviewInfo', INFO_FIELDS)

STARS_DISTRIBUTION = ['star1', 'star2', 'star3', 'star4', 'star5']
StarsDistribution = namedtuple('StarsDistribution', STARS_DISTRIBUTION)

class ReviewPageJSON:
  """Amazonのレビューページに記載されている情報を格納するためのデータオブジェクト
  JSON形式で保存したり、JSONからインスタンス化することもできる
  """
  codec = 'utf-8'
  
  def __init__(self, link='', maker='', product='', category='', 
                average_stars=0.0, total_reviews=0, real_reviews=0,
                stars_distribution=StarsDistribution(0, 0, 0, 0, 0),
                reviews=tuple()):
    self.link               = link
    self.maker              = maker
    self.product            = product
    self.category           = category
    self.average_stars      = average_stars
    self.total_reviews      = total_reviews
    self.real_reviews       = real_reviews
    self.stars_distribution = stars_distribution
    self.reviews            = reviews
    
    # JSONに保存するための辞書型オブジェクト
    self._data = OrderedDict()

  @property
  def stars_distribution(self):
    return self.__stars_distribution

  @stars_distribution.setter
  def stars_distribution(self, value):
    value_class = value.__class__
    if isinstance(value, StarsDistribution):
      self.__stars_distribution = value

    elif issubclass(value_class, Sequence):
      self.__stars_distribution = StarsDistribution._make(value)

    elif issubclass(value_class, Mapping):
      self.__stars_distribution = StarsDistribution._make(value.values())

    else:
        raise ValueError("'{}' requires Sequence or Mapping instance".format('stars_distribution'))

  @property
  def reviews(self):
    return self.__reviews

  @reviews.setter
  def reviews(self, values):
    values = tuple(values)
    if len(values) == 0:
      self.__reviews = values

    else:
      self.__reviews = tuple(ReviewInfo(*v) if issubclass(v.__class__, Sequence) else ReviewInfo(**v) for v in values)

    self.real_reviews = len(self.__reviews)

  def build(self):
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

    for name, obj in sorted(property_attrs.items(), key=lambda item: item[0], reverse=True):
      if isinstance(obj, StarsDistribution):
        self._data[name] = OrderedDict(obj._asdict())

      else:
        self._data[name] = [OrderedDict(review_info._asdict()) for review_info in obj]

  @classmethod
  def load(cls, json_path):
      """JSONで保存されているデータをインスタンスに登録する

      Params:
        json_path: .jsonファイルのパス
      Return
        ReviewPageJSONインスタンス
      """
      json_path = pathlib.Path(json_path)
      review_page = json.load(json_path.open(mode='r', encoding=cls.codec),
                              object_pairs_hook=OrderedDict)
      return cls(**review_page)
      

  def dump(self, path):
    """インスタンスに登録されているデータをJSON形式で保存する

    Params:
      path: jsonの保存パス
    """
    path = pathlib.Path(path)
    self.build()
    json.dump(self._data, path.open(mode='r', encoding=self.codec),
              ensure_ascii=False, indent=4)
      