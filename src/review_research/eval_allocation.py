import os
import argparse
import json
import pathlib
from collections import OrderedDict, namedtuple
from pprint import pprint

import numpy as np

from .nlp import AttributionExtractor

TP = 'tp'
TN = 'tn'
FP = 'fp'
FN = 'fn'

SENTENCE_PROP_FIELD = ['review_id', 'last_review_id', 'sentence_id', 'last_sentence_id', 'review', 'sentence', 'attr_dict']
SentencePropWithoutDict = namedtuple('SentencePropWithoutDict', SENTENCE_PROP_FIELD[:-1])
SentenceProp = namedtuple('SentenceProp', SENTENCE_PROP_FIELD)

INTEGRATED_SENTENCE_PROP_FIELD = [*SENTENCE_PROP_FIELD[:-1], 'label', 'pred']
IntegratedSentenceProp = namedtuple('IntegratedSentenceProp', INTEGRATED_SENTENCE_PROP_FIELD)

EVALUATION_VALUE_FIELD = ['label', 'pred']
EvaluationValue = namedtuple('EvaluationValue', EVALUATION_VALUE_FIELD)

EVALUATION_MEASURES = ['accuracy', 'precision', 'recall', 'specificity', 'f_value']

EVALUATION_RESULT_FIELD = [TP, TN, FP, FN, 'errata', *EVALUATION_MEASURES]
EvaluationResult = namedtuple('EvaluationResult', EVALUATION_RESULT_FIELD)

EVALUATION_RESULT_WITHOUT_ERRATA_FIELD = [TP, TN, FP, FN, *EVALUATION_MEASURES]
EvaluationResultWithoutErrata = namedtuple('EvaluationResultWithoutErrata', EVALUATION_RESULT_WITHOUT_ERRATA_FIELD)

EVALUATED_SENTENCE_PROP_FIELD = [*SENTENCE_PROP_FIELD[:-1], 'error_or_correct']
EvaluatedSentenceProp = namedtuple('EvaluatedSentenceProp', EVALUATED_SENTENCE_PROP_FIELD)

class Evaluater:

  def __init__(self, dic_dir: str, category: str, code='utf-8'):
    self._code = code
    self._extractor = AttributionExtractor(dic_dir)
    self._extractor.category = category
    self.category = category

  @property
  def code(self) -> str:
    return self._code

  @property
  def ja2en(self) -> OrderedDict:
    return self._extractor.ja2en

  @property
  def attr_dict(self) -> OrderedDict:
    return self._extractor.attrdict

  def evaluate(self, eval_json_file: str, pred_json_file: str) -> OrderedDict:
    print('<evaluate>\t{}'.format(os.path.basename(os.path.dirname(eval_json_file))))
    
    label_sentence_list = self._read_eval_json(eval_json_file)
    pred_sentence_list  = self._read_pred_json(pred_json_file)

    evaluation_values_dict = OrderedDict()
    for attr in self.attr_dict.keys():
      evaluation_values_dict[attr] = []

    integrated_list = self._integrate_sentence_prop(label_sentence_list, pred_sentence_list)
    for data in integrated_list:
      label = data.label
      pred  = data.pred
      for attr in self.attr_dict.keys():
        evaluation_values_dict[attr].append(EvaluationValue(label[attr], pred[attr]))

    errata_dict = OrderedDict()        
    evaluation_result_dict = OrderedDict()
    for attr in self.attr_dict.keys():
      evaluation_values = evaluation_values_dict[attr]
      evaluation_result = self._calc_evaluation_result(evaluation_values)
      evaluation_result_dict[attr] = evaluation_result
      errata_dict[attr] = evaluation_result.errata

    # total_attr = len(self.attr_dict)
    eval_dict = OrderedDict()
    for name in EVALUATION_MEASURES:
      eval_dict[name] = list()

    begin_index = len(EVALUATION_RESULT_FIELD) - len(EVALUATION_MEASURES)
    for attr, evaluation_result in evaluation_result_dict.items():
      evaluation_measures = evaluation_result[begin_index:]
      if evaluation_result.fn == 0 and evaluation_result.tp == 0:
        print('\tremove attr: {}'.format(attr))
        continue

      for i, val in enumerate(evaluation_measures):
        eval_dict[EVALUATION_MEASURES[i]].append(val) 

    mean_eval_dict = OrderedDict()
    for name, values in eval_dict.items():
      mean_eval_dict[name] = np.mean(np.array(values))
    
    eval_data = OrderedDict()

    eval_data['pred_file']  = pred_json_file
    eval_data['label_file'] = eval_json_file

    temp_dict = OrderedDict()
    en_dict = self._ja_attr_to_en_attr(evaluation_result_dict)
    for attr, evaluation_result in en_dict.items():
      evaluation_without_errata = EvaluationResultWithoutErrata(
          *evaluation_result[:4], *evaluation_result[5:])
      temp_dict[attr] = OrderedDict(evaluation_without_errata._asdict())

    eval_data['evaluation_measure'] = temp_dict
    eval_data['mean_evaluation'] = mean_eval_dict

    end_index = len(SENTENCE_PROP_FIELD[:-1])
    errata_sentence_dict = OrderedDict()
    for attr, _errata in errata_dict.items():
      key = '{}_errata'.format(self.ja2en[attr])
      sentence_dict = OrderedDict()
      for name, idx_list in _errata.items():
        sentence_prop_dict_list = list()
        for idx in idx_list:
          esp = EvaluatedSentenceProp(*integrated_list[idx][:end_index], name)
          sentence_prop_dict_list.append(OrderedDict(esp._asdict()))

        sentence_dict[name] = sentence_prop_dict_list

      errata_sentence_dict[key] = sentence_dict

    eval_data['errata'] = errata_sentence_dict
    eval_data['sentences'] = [OrderedDict(d._asdict()) 
                              for d in integrated_list]
    return eval_data


  @staticmethod
  def _eval_attr_to_dict(attrs: list) -> OrderedDict:
    label_dict = OrderedDict()
    for attr in attrs:
      label_dict[attr['name']] = attr['flag']

    return label_dict


  def _ja_attr_to_en_attr(self, j_attr_dict: OrderedDict) -> OrderedDict:
    e_attr_dict = OrderedDict()
    for j_attr, val in j_attr_dict.items():
      e_attr = self.ja2en[j_attr]
      e_attr_dict[e_attr] = val

    return e_attr_dict


  def _allocate_sentence_prop_without_dict(self, sentence_dict: OrderedDict) -> SentencePropWithoutDict:
    review_id      = sentence_dict['review_id']
    last_review_id = sentence_dict['last_review_id']

    sentence_id      = sentence_dict['sentence_id']
    last_sentence_id = sentence_dict['last_sentence_id']

    review   = sentence_dict['review']
    sentence = sentence_dict['sentence']

    return SentencePropWithoutDict(review_id, last_review_id, sentence_id, last_sentence_id, review, sentence)


  def _allocate_label_sentence_prop(self, sentence_dict: OrderedDict) -> SentenceProp:
    sentence_prop_without_dict = self._allocate_sentence_prop_without_dict(sentence_dict)        
    label_dict = self._eval_attr_to_dict(sentence_dict['attributes'])

    return SentenceProp(*sentence_prop_without_dict, label_dict)


  def _read_eval_json(self, eval_json_file: str) -> list:
    eval_json_file = pathlib.Path(eval_json_file)
    eval_data = json.load(eval_json_file.open(mode='r', encoding=self.code),
                          object_pairs_hook=OrderedDict)

    sentences = eval_data['sentences']
    label_sentence_list = [self._allocate_label_sentence_prop(sentence)
                           for sentence in sentences]
    return label_sentence_list

  def _pred_result_to_dict(self, pred_result: OrderedDict) -> OrderedDict:
    pred_dict = OrderedDict()
    if pred_result:
      for attr in self.attr_dict.keys():
        en_attr = self.ja2en[attr]
        pred_dict[attr] = 1 if en_attr in pred_result.keys() else 0

      return pred_dict

    else:
      for attr in self.attr_dict.keys():
        pred_dict[attr] = 0

      return pred_dict 


  def _allocate_pred_sentence_prop(self, sentence_dict: OrderedDict) -> SentenceProp:
    sentence_prop_without_dict = self._allocate_sentence_prop_without_dict(sentence_dict)
    pred_dict = self._pred_result_to_dict(sentence_dict['result'])
    return SentenceProp(*sentence_prop_without_dict, pred_dict)

  def _read_pred_json(self, pred_json_file: str) -> list:
    pred_json_file = pathlib.Path(pred_json_file)
    pred_data = json.load(pred_json_file.open(mode='r', encoding=self.code),
                          object_pairs_hook=OrderedDict)

    sentences = pred_data['sentences']
    pred_sentence_list = [self._allocate_pred_sentence_prop(sentence)
                          for sentence in sentences]
    return pred_sentence_list


  def _integrate_sentence_prop(self, label_data: list, pred_data: list) -> list:
    integrated_list = list()
    for label_prop, pred_prop in zip(label_data, pred_data):
      isp = IntegratedSentenceProp(*label_prop[:-1], 
                                   label_prop.attr_dict, 
                                   pred_prop.attr_dict)
      integrated_list.append(isp)

      return integrated_list


  @staticmethod
  def _calc_accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
    dominator = float(tp + tn + fp + fn)
    if dominator == 0:
      return 0

    return (tp + tn) / dominator

  @staticmethod
  def _calc_precision(tp: int, fp: int) -> float:
    dominator = float(tp + fp)
    if dominator == 0:
      return 0

    return tp / dominator 


  @staticmethod
  def _calc_recall(tp: int, fn: int) -> float:
    dominator = float(tp + fn)
    if dominator == 0:
      return 0

    return tp / dominator


  @staticmethod
  def _calc_specificity(tn: int, fp: int) -> float:
    dominator = float(fp + tn)
    if dominator == 0:
      return 0

    return tn / dominator

  
  @staticmethod
  def _calc_f_value(precision: float, recall: float) -> float:
    dominator = precision + recall
    if dominator == 0:
      return 0

    return (2 * precision * recall) / dominator


  def _calc_evaluation_result(self, evaluation_values: list) -> EvaluationResult:
    errata = OrderedDict()
    for name in [TP, TN, FP, FN]:
      errata[name] = list()

    tp, tn, fp, fn = 0, 0, 0, 0
    for idx, (label, pred) in enumerate(evaluation_values):
      if label == pred:
        if label == 1:
          errata[TP].append(idx)
          tp += 1

        else:
          errata[TN].append(idx)
          tn +=1

      else:
        if label == 1:
          errata[FN].append(idx)
          fn += 1

        else:
          errata[FP].append(idx)
          fp += 1

    accuracy    = self._calc_accuracy(tp, tn, fp, fn)
    precision   = self._calc_precision(tp, fp)
    recall      = self._calc_recall(tp, fn)
    specificity = self._calc_specificity(tn, fp)
    f_value     = self._calc_f_value(precision, recall)

    return EvaluationResult(tp, tn, fp, fn, errata, accuracy, precision, recall, specificity, f_value)

      

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')
  parser.add_argument('dic_dir')
  args = parser.parse_args()

  import glob
  from pprint import pprint

  input_dir = args.input_dir
  all_files = glob.glob('{}\\**'.format(input_dir), recursive=True)
  json_file_list = [os.path.abspath(f) for f in all_files 
                    if os.path.isfile(f) and f.endswith('.json')]

  def is_target(path: str ,pattern: str):
    return os.path.basename(path) == pattern

  PATTERN_PAIR_FIELD = ['pred', 'result']
  PatternPair = namedtuple('PatternPair', PATTERN_PAIR_FIELD)
  PATTERN_PAIR_KEY = PatternPair(*PATTERN_PAIR_FIELD)
  pattern_pair_dict = OrderedDict()
  pattern_pair_dict['extend']            = PatternPair('prediction_extended.json', 'result_extended.json')
  pattern_pair_dict['extended_ristrict'] = PatternPair('prediction_extended_ristrict.json', 'result_extended_ristrict.json')
  pattern_pair_dict['ristrict']          = PatternPair('prediction_ristrict.json', 'result_ristrict.json')
  pattern_pair_dict['normal']            = PatternPair('prediction.json', 'result.json')

  product_dir_list = [os.path.dirname(f) for f in json_file_list]
  product_dir_list = sorted(set(product_dir_list), key=product_dir_list.index)
  product_file_dict = {product_dir: [] for product_dir in product_dir_list}
  for json_file in json_file_list:
    for product_dir in product_dir_list:
      if json_file.startswith(product_dir):
        product_file_dict[product_dir].append(json_file)

  io_file_dict = OrderedDict()
  for product_dir, file_list in product_file_dict.items():
    file_dict = OrderedDict()
    for pattern_name, pattern_pair in pattern_pair_dict.items():
      pred_pat, res_pat = pattern_pair
      pred_file, res_file = '', ''
      for json_file in file_list:
        if is_target(json_file, pred_pat):
          pred_file = json_file

        elif is_target(json_file, res_pat):
          res_file = json_file

      file_dict[pattern_name] = PatternPair(pred_file, res_file)

    io_file_dict[product_dir] = file_dict

  eval_file_dict = OrderedDict()
  for product_dir, file_list in product_file_dict.items():
    for json_file in file_list:
      if is_target(json_file, 'eval.json'):
        eval_file_dict[product_dir] = json_file

  # pprint(io_file_dict)

  category = os.path.basename(input_dir)
  print(category)
  evaluater = Evaluater(args.dic_dir, category)
  for product_dir, pattern_dict in io_file_dict.items():
    eval_file = eval_file_dict[product_dir]
    for pattern_name, pattern_pair in pattern_dict.items():
      print('[{}]'.format(pattern_name))
      pred_file, res_file = pattern_pair
      eval_data = evaluater.evaluate(eval_file, pred_file)
      # out_file = '{}\\{}'.format(product_dir, res_file)
      json.dump(eval_data, open(res_file, mode='w', encoding=evaluater.code), ensure_ascii=False, indent=4)