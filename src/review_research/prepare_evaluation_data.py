import json
import argparse
import os
import pathlib
import glob
from collections import OrderedDict, namedtuple

from tqdm import tqdm

from review_research.nlp import Splitter
from review_research.nlp import COMMON_DICTIONARY_NAME
from review_research.nlp import AttrDictHandler
from review_research.review import ReviewPageJSON
from review_research.evaluation import AttrAnnotation
from review_research.evaluation import TextWithAttrAnnotation
from review_research.evaluation import AttrEvaluationData
from review_research.misc import get_all_jsonfiles

def set_classes(dic_dir: str, category: str):
  dict_handler = AttrDictHandler(dic_dir)
  attr_dict = OrderedDict()
  common_attr_en_name = [*dict_handler.common_en2ja][0]
  common_attr_ja_name = dict_handler.common_en2ja[common_attr_en_name]
  attr_dict[common_attr_en_name] = common_attr_ja_name
  for attr_en_name, attr_ja_name in dict_handler.en2ja(category).items():
    attr_dict[attr_en_name] = attr_ja_name

  return attr_dict

def main(args):
  data_dir = pathlib.Path(args.data_dir)
  json_filepaths = get_all_jsonfiles(data_dir, 'review.json')
  splitter = Splitter()
  dic_dir = args.dic_dir
  for json_file in tqdm(json_filepaths, ascii=True):
    product_dir = json_file.parent
    product_name = product_dir.name
    category = product_dir.parent.name

    attribute_dict = set_classes(dic_dir, category)
    attribute_list = [*attribute_dict]
    Attributes = namedtuple('Attributes', attribute_list)
    attribute_pairs = [AttrAnnotation(name, 0) 
                       for name in attribute_dict.values()]
    attributes = Attributes(*[attr._asdict() for attr in attribute_pairs])

    review_data = ReviewPageJSON.load(json_file)
    total_review = review_data.total_reviews
    all_text_list = []
    for idx, review_info in enumerate(review_data.reviews):
      review_id = idx
      review = review_info.review

      texts = splitter.split_sentence(review)
      last_text_id = len(texts)
      sentence_list = [
          TextWithAttrAnnotation(
              review_id + 1, total_review, review, sentence_id + 1, 
              last_text_id, sentence, attributes)
          for sentence_id, sentence in texts.items()
      ]
      all_text_list.extend(sentence_list)
  
    total_text = len(all_text_list)
    evaluation_data = AttrEvaluationData(
        category, product_name, total_review, total_text, all_text_list)

    out_file = product_dir / 'eval.json'
    evaluation_data.dump(out_file)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('dic_dir',
                      help='属性辞書を格納しているフォルダパス')
  parser.add_argument('data_dir', 
                      help='review.json を格納しているフォルダパス')

  main(parser.parse_args())