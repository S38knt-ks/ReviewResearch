import json
import math
from pathlib import Path
from pprint import pprint
from collections import OrderedDict

import pandas
import numpy as np
from tqdm import tqdm

from ..nlp import normalize
from ..nlp import TextAlignment

COLUMNS = ['word', 'tfidf']

class TFIDF:

  def __init__(self):
    self._ta        = TextAlignment()
    self.word_dict  = OrderedDict()
    self.df_dict    = OrderedDict()
    self.idf_dict   = OrderedDict()
    self.tfidf_dict = OrderedDict()
    self.N          = 0

    self._text_dict      = OrderedDict()
    self._alignment_dict = OrderedDict()


  @property
  def alignment_dict(self) -> OrderedDict:
    return self._alignment_dict
  
  def compute(self, doc_list: list, sort=False):
    # tfとdfの計算
    # print('calculate tf and df...')
    for idx, doc in enumerate(doc_list):
      tf_dict = self._compute_tf(normalize(doc))
      self._alignment_dict[idx] = self._ta.alignment
      self._text_dict[idx]      = self._ta.text
      # pprint(self.correspond_words_dict)
      self.word_dict[idx] = tf_dict

      for w in tf_dict:
        if w in self.df_dict:
          self.df_dict[w] += 1

        else:
          self.df_dict[w] = 1

    # idfの計算
    self.N = len(doc_list)
    for w, df in self.df_dict.items():
      self.idf_dict[w] = math.log(self.N / df) + 1

    # tfidfの計算
    self.sorted_tfidf_dict = OrderedDict()
    for idx in range(self.N):
      target_tf_dict = self.word_dict[idx]
      tfidf = [idf * target_tf_dict[w] if w in target_tf_dict else 0
               for i, (w, idf) in enumerate(self.idf_dict.items())]
      tfidf = np.array(tfidf)
      tfidf_list = np.array([[*self.df_dict], tfidf]).T

      tfidf_df = pandas.DataFrame(tfidf_list, columns=COLUMNS)
      tfidf_df = tfidf_df.astype({'tfidf': float})
      self.tfidf_dict[idx] = tfidf_df
      self.sorted_tfidf_dict[idx] = tfidf_df.sort_values(COLUMNS[1],
                                                         ascending=False)

    if sort:
      return self.sorted_tfidf_dict

    else:
      return self.tfidf_dict
      

  def to_csv(self, out_file, code='utf-8'):
    text_list = []
    header = ['review_index']
    header.extend([*self.df_dict.keys()])
    text_list.append(header)
    for idx, df in self.tfidf_dict.items():
      content = [idx]
      content.extend(df[COLUMNS[1]].values.tolist())
      text_list.append(content)

    text_array = np.array(text_list).T
    with open(out_file, mode='w', encoding=code) as fp:
      for text in text_array:
        fp.write('{}\n'.format(','.join(str(t) for t in text)))
  
  def _compute_tf(self, text: str) -> np.ndarray:
    self._ta.align(text)
    result_list = [w.word for w in self._ta.words]
    word_count_list = np.array([[w, result_list.count(w)]
                                for w in set(result_list)])

    word_list = word_count_list[:, 0]
    count_list = np.array(word_count_list[:, 1], dtype=float)
    tf = count_list / np.sum(count_list)
    tf_dict = OrderedDict()
    for w, tf in zip(word_list, tf):
      tf_dict[w] = tf

    return tf_dict


def main(args):
  input_dir = args.input_dir
  all_files = glob.glob('{}\\**'.format(input_dir), recursive=True)
  json_list = [f for f in all_files if Path(f).suffix == '.json']

  for f in json_list:
    data = json.load(open(f, mode='r', encoding='utf-8'),
                      object_pairs_hook=OrderedDict)

    reviews = data['reviews']
    doc_list = [r['review'] for r in reviews]
    tfidf = TFIDF()
    tfidf.compute(doc_list)
    pprint(tfidf.tfidf_dict)
    break

if __name__ == "__main__":
  import argparse
  import glob

  parser = argparse.ArgumentParser()
  parser.add_argument('input_dir')

  main(parser.parse_args())


    
