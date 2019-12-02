from typing import NamedTuple, Dict, List, Any

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
    result (Dict[str, str]): 抽出結果
  """
  review_id: int
  last_review_id: int
  text_id: int
  last_text_id: int
  star: float
  title: str
  review: str
  text: str
  result: Dict[str, str]