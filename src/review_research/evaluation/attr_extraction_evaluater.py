import pathlib
import json
from collections import namedtuple, OrderedDict
from typing import Union, Dict, Tuple, NamedTuple, NoReturn, Any

import numpy as np

from ..nlp import AttributionExtractor
from ..evaluation import AttrAnnotation
from ..evaluation import TextWithAttrAnnotation
from ..evaluation import AttrEvaluationData
from ..evaluation import AttrPredictionResult
from ..evaluation import QuantitativeEvaluation
from ..evaluation import MeanQuantitativeEvaluation
from ..evaluation import MetricsCalculator

class DataForEvaluation(NamedTuple):
  """定量評価または、エラー分析に使いやすいようにフォーマットを定めたクラス

  Attributes:
    review_id (int): レビュー番号
    last_review_id (int): 最後のレビュー番号
    text_id (int): レビュー文中の文番号
    last_text_id (int): レビュー文中の最後の文番号
    review (str): レビュー本文
    text (str): 評価対象の文
    label (int): 正解ラベル
    pred (int): 属性抽出結果
    label_attrs (Tuple[AttrAnnotation, ...]): 正解アノテーション
    pred_attrs (Tuple[AttrAnnotation, ...]): 属性ごとの抽出結果
  """
  review_id: int
  last_review_id: int
  text_id: int
  last_text_id: int
  review: str
  text: str
  label: int
  pred: int
  label_attrs: Tuple[AttrAnnotation, ...]
  pred_attrs: Tuple[AttrAnnotation, ...]

  @classmethod
  def iterator_from_text_with_annotation_pair(
      cls, pred: TextWithAttrAnnotation, label: TextWithAttrAnnotation):
    """正解データと属性抽出結果データからインスタンス化し、属性ごとにインスタンスを返すジェネレータ関数

    Args:
      pred (TextWithAttrAnnotation): 属性抽出結果データ
      label (TextWithAttrAnnotation): 正解データ

    Returns:
      属性とそれに対応するDataForEvaluationインスタンスのジェネレータ
    """
    review_id = label.review_id
    last_review_id = label.last_review_id
    text_id = label.text_id
    last_text_id = label.last_text_id
    review = label.review
    text = label.text
    label_attrs = label.attributes
    pred_attrs = pred.attributes
    attr_annotation_pairs = zip(label_attrs, pred_attrs)
    for label_attr_annotation, pred_attr_annotation in attr_annotation_pairs:
      this = cls(
          review_id, last_review_id, text_id, last_text_id, review, text, 
          label_attr_annotation.label, pred_attr_annotation.label,
          label_attrs, pred_attrs)
      yield (label_attr_annotation.name, this)

  def to_dict(self) -> Dict[str, Any]:
    """DataForEvaluationインスタンスをJSONデータに合うように辞書化する"""
    label_attrs = [attr_annotation._asdict()
                   for attr_annotation in self.label_attrs]
    pred_attrs = [attr_annotation._asdict()
                  for attr_annotation in self.pred_attrs]
    this = DataForEvaluation._make(self)
    this = this._replace(label_attrs=label_attrs, pred_attrs=pred_attrs)
    return this._asdict()

class Errata(NamedTuple):
  """正誤表

  Attributes:
    tp (Tuple[DataForEvaluation, ...]): 真陽性
    tn (Tuple[DataForEvaluation, ...]): 真陰性
    fp (Tuple[DataForEvaluation, ...]): 偽陽性
    fn (Tuple[DataForEvaluation, ...]): 偽陰性
    counts (Tuple[int, int, int, int]): それぞれの数をカウントしたもの
  """
  tp: Tuple[DataForEvaluation, ...]
  tn: Tuple[DataForEvaluation, ...]
  fp: Tuple[DataForEvaluation, ...]
  fn: Tuple[DataForEvaluation, ...]

  @property
  def counts(self) -> Tuple[int, int, int, int]:
    """tp, tn, fp, fn それぞれの数をカウントしたものを返す"""
    return (len(self.tp), len(self.tn), len(self.fp), len(self.fn))

class EvaluationResult(NamedTuple):
  """評価結果を格納するクラス

  Attributes:
    pred_file (Union[str, pathlib.Path]): 抽出結果を格納しているファイル
    label_file (Union[str, pathlib.Path]): 正解データを格納しているファイル
    quantitative_evaluation (Dict[str, QuantitativeEvaluation]): 属性ごとの定量的評価
    mean_quantitative_evaluation (MeanQuantitativeEvaluation): 属性ごとの定量的評価の平均
    errata_dict (Dict[str, Errata]): 属性ごとの正誤表
  """
  pred_file: Union[str, pathlib.Path]
  label_file: Union[str, pathlib.Path]
  quantitative_evaluation: Dict[str, QuantitativeEvaluation]
  mean_quantitative_evaluation: MeanQuantitativeEvaluation
  errata_dict: Dict[str, Errata]

  def dump(self, jsonpath: Union[str, pathlib.Path]) -> NoReturn:
    """評価結果を JSON 形式で保存する

    Args:
      jsonpath (Union[str, pathlib.Path]): 保存ファイル名
    """
    data = OrderedDict()
    data['pred_file'] = str(self.pred_file)
    data['label_file'] = str(self.label_file)
    data['quantitative_evaluation'] = {
        attr: qe._asdict()
        for attr, qe in self.quantitative_evaluation.items()
    }
    mean_dict = self.mean_quantitative_evaluation._asdict()
    data['mean_quantitative_evaluation'] = mean_dict
    attr_to_errata = OrderedDict()
    for attr_key, _errata in self.errata_dict.items():
      errata_dict = OrderedDict()
      for errata_key, data in _errata._asdict().items():
        errata_dict[errata_key] = data.to_dict()

      attr_to_errata[attr_key] = errata_key

    data['errata'] = attr_to_errata
    jsonpath = pathlib.Path(jsonpath)
    json.dump(data, jsonpath.open('w', encoding='utf-8'),
              ensure_ascii=False, indent=4)      

class AttrExtractionEvaluater(object):
  """属性抽出の評価を行う"""

  def __init__(self, dic_dir: Union[str, pathlib.Path], category: str):
    self._extractor = AttributionExtractor(dic_dir)  # 属性辞書のために使用
    self.category = category

  @property
  def category(self) -> str:
    return self.__category

  @category.setter
  def category(self, value: str):
    self.__category = value
    self._extractor.category = value

  @property
  def ja2en(self) -> Dict[str, str]:
    return self._extractor.ja2en

  @property
  def en2ja(self) -> Dict[str, str]:
    return self._extractor.en2ja

  @property
  def attrdict(self) -> Dict[str, Tuple[str, ...]]:
    return self._extractor.attrdict

  def __call__(self, eval_jsonfile: Union[str, pathlib.Path],
               pred_jsonfile: Union[str, pathlib.Path]) -> EvaluationResult:
    return self.evaluate(eval_jsonfile, pred_jsonfile)

  def evaluate(self, eval_jsonfile: Union[str, pathlib.Path],
               pred_jsonfile: Union[str, pathlib.Path]) -> EvaluationResult:
    """属性抽出結果と正解を比べ、評価する

    Args:
      eval_jsonfile (Union[str, pathlib.Path]): 正解データ
      pred_jsonfile (Union[str, pathlib.Path]): 属性抽出結果を格納したデータ

    Returns:
      評価結果
    """
    eval_data = AttrEvaluationData.load(eval_jsonfile).texts
    attributes = eval_data[0].attributes
    pred_data = self._make_pred_data_look_like_eval_data(
        attributes, pred_jsonfile)

    # 属性ごとに抽出結果をまとめる
    evaluation_values_dict = OrderedDict()
    eval_data = sorted(eval_data, key=_extract_ids_as_key)
    pred_data = sorted(pred_data, key=_extract_ids_as_key)
    for eval_text_data, pred_text_data in zip(eval_data, pred_data):
      data_gen = DataForEvaluation.iterator_from_text_with_annotation_pair(
          pred_text_data, eval_text_data)
      for attr, data_for_evaluation in data_gen:
        evaluation_values_dict.setdefault(attr, []).append(data_for_evaluation)

    key_fmt = '{}_errata'
    attr_to_errata = OrderedDict()
    attr_to_quantitative_evaluation = OrderedDict()
    quantitative_evaluations = list()
    for attr, eval_results in evaluation_values_dict.items():
      key = key_fmt.format(self.ja2en[attr])
      errata = _make_errata(eval_results)
      attr_to_errata[key] = errata
      metrics = MetricsCalculator(*errata.counts)
      quantitative_evaluation = QuantitativeEvaluation.from_metrics(metrics)
      attr_to_quantitative_evaluation[attr] = quantitative_evaluation
      quantitative_evaluations.append(quantitative_evaluation)

    means = MeanQuantitativeEvaluation.from_quantitative_evaluations(
        quantitative_evaluations)
    
    return EvaluationResult(pred_jsonfile, eval_jsonfile, 
                            attr_to_quantitative_evaluation, means, 
                            attr_to_errata)
    
  def _make_pred_data_look_like_eval_data(
      self,
      attributes: Tuple[AttrAnnotation, ...],
      pred_jsonfile: Union[str, pathlib.Path]
  ) -> Tuple[TextWithAttrAnnotation, ...]:
    """比較しやすいように属性抽出の結果を正解データのフォーマットに整える

    Args:
      attributes (Tuple[AttrAnnotation, ...]): 正解データの属性一覧
      pred_jsonfile (Union[str, pathlib.Path]): 属性抽出の結果が格納されている JSON ファイル

    Returns:
      TextWithAttrAnnotationのフォーマットに整えられた結果一覧
    """
    pred_result = AttrPredictionResult.load(pred_jsonfile)
    texts = []
    for text_data in pred_result.texts:
      review_id = text_data.review_id
      last_review_id = text_data.last_review_id
      review = text_data.review
      text_id = text_data.text_id
      last_text_id = text_data.last_text_id
      text = text_data.text
      
      pred_attributes = []
      for attribute in attributes:
        en_attr = self.ja2en[attribute.name]
        label = 1 if en_attr in text_data.result else 0
        pred_attributes.append(AttrAnnotation(en_attr, label))

      texts.append(
          TextWithAttrAnnotation(
            review_id, last_review_id, review, text_id, last_text_id, text,
            tuple(pred_attributes)))
    
    return tuple(texts)
  

def _extract_ids_as_key(
    item: TextWithAttrAnnotation) -> Tuple[int, int, int, int]:
  return (item.review_id, item.last_review_id, item.text_id, item.last_text_id)

def _make_errata(results: Tuple[DataForEvaluation, ...]) -> Errata:
  """正誤表を作成する

  Args:
    results (Tuple[DataForEvaluation, ...]): DataForEvalutationインスタンス一覧

  Returns:
    Errataインスタンス
  """
  tp = list()
  tn = list()
  fp = list()
  fn = list()
  for result in results:
    label, pred = result.label, result.pred
    if label == pred:  # 抽出成功
      if label == 1:
        tp.append(result)
      else:
        tn.append(result)

    else:  # 抽出失敗
      if pred == 1:  # 偽陽性
        fp.append(result)
      else:
        fn.append(result)

  return Errata(tuple(tp), tuple(tn), tuple(fp), tuple(fn))