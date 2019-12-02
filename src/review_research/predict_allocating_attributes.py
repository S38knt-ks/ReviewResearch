import argparse
import json
import pathlib
import glob
from functools import partial
from collections import namedtuple, OrderedDict

from tqdm import tqdm

from .nlp import Splitter
from .nlp import normalize
from .nlp import AttributionExtractor
from .evaluation import ReviewTextInfo
from .evaluation import AttrPredictionResult
from .review import ReviewPageJSON

def main(args):
  splitter = Splitter()

  dic_dir = pathlib.Path(args.dic_dir)
  review_dir = pathlib.Path(args.review_dir)

  glob_recursively = partial(glob.glob, recursive=True)
  all_files = glob_recursively('{}/**'.format(review_dir))
  review_jsons = [pathlib.Path(f).resolve() for f in all_files
                  if pathlib.Path(f).name == 'review.json']

  OPTION_FIELD = ['is_extended', 'is_ristrict']
  Option = namedtuple('Option', OPTION_FIELD)

  option_list = [Option(False, False), 
                 Option(False, True),
                 Option(True, False),
                 Option(True, True)]
          
  file_fmt = 'prediction{}{}.json'
  for json_path in tqdm(review_jsons, ascii=True):
    for option in option_list:
      extention    = '_extended' if option.is_extended else ''
      restricition = '_ristrict' if option.is_ristrict else ''

      extractor = AttributionExtractor(dic_dir, extend=option.is_extended,
                                       ristrict=option.is_ristrict)

      out_file = json_path.parent / file_fmt.format(extention, restricition)

      review_data = ReviewPageJSON.load(json_path)
      reviews = review_data.reviews
      category = review_data.category
      product_name = review_data.product
      link = review_data.link
      maker = review_data.maker
      ave_star = review_data.average_stars
      stars_dist = review_data.stars_distribution

      extractor.category = category
      total_review = len(reviews)
      last_review_id = total_review
      review_text_info_list = []
      for idx, review_info in enumerate(reviews):
        star   = review_info.star
        title  = review_info.title
        review = review_info.review
        review_id = idx + 1

        sentences = splitter.split_sentence(normalize(review))
        last_sentence_id = len(sentences)
        for sidx, sentence in sentences.items():
          sentence_id = sidx + 1
          result_dict = extractor.extract_attribution(sentence)
          editted_dict = OrderedDict()
          for attr, flagment in result_dict.items():
            editted_dict[extractor.ja2en[attr]] = flagment

          review_text_info_list.append(
              ReviewTextInfo(review_id, last_review_id,
                             sentence_id, last_sentence_id,
                             star, title, review, sentence, editted_dict))

      total_sentence = len(review_text_info_list)
      result = AttrPredictionResult(
          json_path, product_name, link, maker, ave_star, stars_dist,
          total_review, total_sentence, tuple(review_text_info_list)
      )
      result.dump(out_file)
      

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('dic_dir',
                      help='属性辞書を格納しているフォルダパス')
  parser.add_argument('review_dir',
                      help='review.json を格納しているフォルダパス')