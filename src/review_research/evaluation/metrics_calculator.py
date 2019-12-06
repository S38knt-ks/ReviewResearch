from typing import NamedTuple, Tuple

import numpy as np

class MetricsCalculator(object):
  """評価指標を計算する

  Attributes:
    tp (int): 真を真として当てられたものの数
    tn (int): 偽を偽として当てられたものの数
    fp (int): 偽を真としてしまったものの数
    fn (int): 真を偽としてしまったものの数
    accuracy (float): 精度
    precision (float): 適合率
    recall (float): 再現率
    specificity (float): 特異値
    f1 (float): F1 値
  """
  
  def __init__(self, tp: int, tn: int, fp: int, fn: int):
    self.tp = tp
    self.tn = tn
    self.fp = fp
    self.fn = fn

  @property
  def accuracy(self) -> float:
    """精度を返す"""
    dominator = float(self.tp + self.tn + self.fp + self.fn)
    try:
      accuracy = (self.tp + self.tn) / dominator
    except ZeroDivisionError:
      return 0.0
    else:
      return accuracy

  @property
  def precision(self) -> float:
    """適合率を返す"""
    dominator = float(self.tp + self.fn)
    try:
      precision = self.tp / dominator
    except ZeroDivisionError:
      return 0.0
    else:
      return precision

  @property
  def recall(self) -> float:
    """再現率を返す"""
    dominator = float(self.tp + self.fn)
    try:
      recall = self.tp / dominator
    except ZeroDivisionError:
      return 0.0
    else:
      return recall

  @property
  def specificity(self) -> float:
    """特異値を返す"""
    dominator = float(self.fp + self.tn)
    try:
      specificity = self.tn / dominator
    except ZeroDivisionError:
      return 0.0
    else:
      return specificity

  @property
  def f1(self) -> float:
    """F1 値を返す"""
    precision = self.precision
    recall = self.recall
    dominator = precision + recall
    try:
      f1 = (2 * precision * recall) / dominator
    except ZeroDivisionError:
      return 0.0
    else:
      return f1
  
class QuantitativeEvaluation(NamedTuple):
  """定量評価をまとめたクラス

  Attributes:
    tp (int): 真を真として当てられたものの数
    tn (int): 偽を偽として当てられたものの数
    fp (int): 偽を真としてしまったものの数
    fn (int): 真を偽としてしまったものの数
    accuracy (float): 精度
    precision (float): 適合率
    recall (float): 再現率
    specificity (float): 特異値
    f1 (float): F1 値
  """
  tp: int
  tn: int
  fp: int
  fn: int
  accuracy: float
  precision: float
  recall: float
  specificity: float
  f1: float

  @classmethod
  def from_metrics(cls, metrics: MetricsCalculator):
    """MetricsCalculatorインスタンスからインスタンス化

    Args:
      metrics (MetricsCalculator): MetricsCalculatorインスタンス

    Returns:
      QuantitativeEvaluationインスタンス
    """
    return cls(
        metrics.tp, metrics.tn, metrics.fp, metrics.fn, metrics.accuracy,
        metrics.precision, metrics.recall, metrics.specificity, metrics.f1)

class MeanQuantitativeEvaluation(NamedTuple):
  """
  定量的評価の平均値を格納するためのクラス

  Attributes:
    accuracy (float): 精度
    precision (float): 適合率
    recall (float): 再現率
    specificity (float): 特異値
    f1 (float): F1 値
  """
  accuracy: float
  precision: float
  recall: float
  specificity: float
  f1: float

  @classmethod
  def from_quantitative_evaluations(
      cls, quantitative_evaluations: Tuple[QuantitativeEvaluation, ...]):
    """QuantitativeEvaluationインスタンス一覧から平均値を求める

    Args:
      quantitative_evaluations (Tuple[QuantitativeEvaluation, ...]): QuantitativeEvaluationインスタンス一覧

    Returns:
      MeanQuantitativeEvaluationインスタンス
    """
    results = tuple(
        tuple(qe.accuracy, qe.precision, qe.recall, qe.specificity, qe.f1)
        for qe in quantitative_evaluations
    )
    cls(*np.mean(results, axis=0))