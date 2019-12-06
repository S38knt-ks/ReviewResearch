import sys
import os
import pathlib
import json
import re
import inspect
from collections import OrderedDict
from functools import partial
from itertools import product, combinations

import numpy as np
import pandas as pd

HIGHEST = '5-4'
HIGHER  = '4-3'
LOWER   = '3-2'
LOWEST  = '2-1'
EvalClasses = tuple([HIGHEST, HIGHER, LOWER, LOWEST])

def classify_evalclass(avg_star):
  evalclass = LOWEST
  if avg_star > 4.0:
    evalclass = HIGHEST

  elif avg_star > 3.0:
    evalclass = HIGHER

  elif avg_star > 2.0:
    evalclass = LOWER

  return evalclass


class Review2Variable:
  """Reviewデータを統計で扱いやすいように変えるクラス

  Attributes:
    vote: 投票数
    date: 日付
    text_length: レビュー文の長さ
    token_num: レビュー文内の単語数
  """

  def __init__(self, review_json_path, tokenizer):
    self.review_json = pathlib.Path(review_json_path)
    self.review_data = json.load(self.review_json.open(mode='r', encoding='utf-8'),
                                  object_pairs_hook=OrderedDict)

    self.product  = self.review_data['product']
    self.category = self.review_data['category']
    self.avg_star = self.review_data['average_stars']
    self.evalclass = classify_evalclass(self.avg_star)

    self.reviews = [review for review in self.review_data['reviews']]
    self.N_review = len(self.reviews)

    self.tokenizer = tokenizer

  @property
  def vote(self):
    vote = [review['vote'] for review in self.reviews]
    return np.array(vote, dtype=int)

  @property
  def date(self):
    date = [review['date'] for review in self.reviews]
    return np.array(date)

  def text_length(self, ignore_space=True):
    space_pat = re.compile(r'\s+')
    text_length = np.zeros(self.N_review, dtype=int)
    for idx, review_text in enumerate(review['review'] for review in self.reviews):
      if ignore_space:
        review_text = space_pat.sub('', review_text)

      text_length[idx] = len(review_text)

    return text_length

  def token_num(self, poslist, remove_stopwords=True, remove_hiragana=True):
    get_baseforms = partial(self.tokenizer.get_baseforms,
                            remove_stopwords=remove_stopwords,
                            remove_a_hiragana=remove_hiragana,
                            pos_list=poslist)
    token_num = np.array([len(get_baseforms(review_text)) for review_text in self.reviews['review']],
                          dtype=int)
    return token_num

