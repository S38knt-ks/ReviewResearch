import os
from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint

from tqdm import tqdm

from ..nlp import DependencyAnalyzer
from ..nlp import PhraseContent
from ..nlp import LinkProp
from ..nlp import REQUIREMENT_POS_LIST
from ..nlp import AttrDictHandler

DICTIONARY_PROP_FIELD = ['name', 'path']
DictionaryProp = namedtuple('DictionaryProp', DICTIONARY_PROP_FIELD)

ANALYSIS_RESULT_FIELD = ['chunk_dict', 'token_dict', 'alloc_dict',
                         'phrase_dict', 'link_dict']
AnalysisResult = namedtuple('AnalysisResult', ANALYSIS_RESULT_FIELD)

EXTRACTION_RESULT_FIELD = ['attrs', 'flagment', 'candidate_terms', 
                           'hit_terms', 'cooccurrence_words', 
                           'phrases', 'phrase_num']
ExtractionResult = namedtuple('ExtractionResult', EXTRACTION_RESULT_FIELD)

EXTRACTION_DETAIL_RESULT = [*EXTRACTION_RESULT_FIELD[1:]]
ExtractionDetail = namedtuple('ExtractionDetail', EXTRACTION_DETAIL_RESULT)

STOPWORD_DIC_PATH = 'JapaneseStopWord.txt'

PAEALLEL_PRESENTATION_WORDS = ['や', 'と']

BASE_PATTERN_WORDS = ['が', 'は', 'も', 'に', 'を']

WORD_SEPARATOR = '<WORDSEP>'

class AttributionExtractor:
  """属性抽出器"""

  def __init__(self, dic_dir: str, code='utf-8', extend=True, ristrict=True):
      self.category  = None
      self._code     = code
      self._extend   = extend
      self._ristrict = ristrict

      self._category_to_attrdict = None
      self._ja2en = None
      self._en2ja = None

      self._read_stopword_dic()

      self._attr_dict_handler = AttrDictHandler(dic_dir)
      self._common_attr_dict = self._attr_dict_handler.common_attr_dict

      self._analyzer = DependencyAnalyzer()


  @property
  def extend(self) -> bool:
      return self._extend


  @property
  def ristrict(self) -> bool:
      return self._ristrict

  @property
  def category(self) -> str:
      """現在扱っている商品カテゴリ"""
      return self.__category

  @category.setter
  def category(self, category):
      if category is not None and self.category != category:
          self.__category = category
          self._build_dictionary()

  def _build_dictionary(self):
      self._category_to_attrdict = OrderedDict()
      self._category_to_attrdict[self.category] = self._attr_dict_handler.attr_dict(self.category)
      self._category_to_attrdict[AttrDictHandler.COMMON_DICTIONARY] = self._common_attr_dict
      self._ja2en = OrderedDict()
      for category, attrdict in self._category_to_attrdict:
          for attr in attrdict:
              self._ja2en[attr] = self._attr_dict_handler.ja2en(category)[attr]

      self._en2ja = OrderedDict()
      for ja, en in self.ja2en.items():
          self._en2ja[en] = ja
          

  @property
  def code(self) -> str:
      return self._code

  @property
  def ja2en(self):
      """日本語属性名を英語属性名に変換する辞書"""
      return self._ja2en

  @property
  def en2ja(self):
      return self._en2ja

  # @property
  # def category_to_attrdict(self) -> OrderedDict:
  #     return self._category_to_attrdict


  @property
  def attrdict(self):
      return {attr: words for category, attrdict in self._category_to_attrdict.items()
                          for attr, words in attrdict.items()}

  @property
  def stopwords(self) -> list:
      return self._stopwords


          

  def extract_attrribution(self, sentence: str) -> OrderedDict:
      analysis_result = self._analyze(sentence)
      result_list = []
      for link_prop_list in analysis_result.link_dict.values():
          attrs = []
          candidate_term_list = []
          hit_terms = []
          link_list = [link_prop.chunk_id for link_prop in link_prop_list]
          flagment = self._link_to_flagment(link_list, analysis_result.chunk_dict)
          candidate_link_prop_list = self._get_canndidate_terms(link_prop_list)
          for link_prop in candidate_link_prop_list:
              main_term, words, _, _ = link_prop.phrase_content
              
              candidate_terms = [main_term]
              if self.extend and words:
                  candidate_terms.extend(words)

              candidate_term_list.extend(candidate_terms)

              for attr, words in self.attrdict.items():
                  for term in candidate_terms:
                      if term in words :
                          hit_terms.append(term)
                          attrs.append(attr)            

          candidate_terms = WORD_SEPARATOR.join(sorted(set(candidate_term_list), key=candidate_term_list.index))
          hit_terms       = WORD_SEPARATOR.join(sorted(set(hit_terms), key=hit_terms.index))
          cooccurrences   = self._extract_cooccurrence(link_prop_list)
          phrases         = WORD_SEPARATOR.join(link_prop.phrase_content.main for link_prop in link_prop_list)

          result_list.append(ExtractionResult(attrs, flagment, candidate_terms, hit_terms, cooccurrences, phrases, len(link_list)))

      result_dict = defaultdict(list)
      for result in result_list:
          for attr in result.attrs:
              detail = ExtractionDetail(result.flagment, result.candidate_terms, result.hit_terms, result.cooccurrence_words, result.phrases, result.phrase_num)
              result_dict[attr].append(detail)

      temp_dict = dict(result_dict)
      result_dict = OrderedDict()
      for attr in self.attrdict:
          if attr in temp_dict.keys():
              details = temp_dict[attr]
              detail_set = sorted(set(details), key=details.index)
              result_dict[attr] = [OrderedDict(detail._asdict()) for detail in detail_set]

      return result_dict

          
  def _read_stopword_dic(self):
      with open(STOPWORD_DIC_PATH, mode='r', encoding=self.code) as fp:
          self._stopwords = [line.strip() for line in fp.readlines() if line.strip() != '']


  def _get_canndidate_terms(self, link_list: list) -> list:
      if self.ristrict:
          link_list = self._update_link_prop_list(link_list)

      candidate_link_prop_list = []
      for link_prop in link_list[:-1]:
          main_term, _, pos, sub = link_prop.phrase_content
          if pos != '名詞':
              continue

          elif main_term in self.stopwords:
              continue                

          else:
              if sub in BASE_PATTERN_WORDS:
                  candidate_link_prop_list.append(link_prop)

      last_lp = link_list[-1]
      if last_lp.phrase_content.pos == '名詞':
          candidate_link_prop_list.append(last_lp)

      return candidate_link_prop_list


  def _update_link_prop_list(self, link_prop_list: list) -> list:
      length = len(link_prop_list) - 1
      old_updated_list = link_prop_list[:]
      while True:
        updated_lp_list = []
        for curr_idx, curr_link_prop in enumerate(link_prop_list[:-1]):
          c_term, c_words, c_pos, c_sub = curr_link_prop.phrase_content
          if c_pos != '名詞':
            updated_link_prop = curr_link_prop

          elif c_pos == '名詞' and self._is_good_pp(c_sub):
            updated_link_prop = curr_link_prop

          elif c_term in self.stopwords:
            updated_link_prop = curr_link_prop

          # 属性候補語(名詞)と思われる語句が含まれる文節の処理
          else:
            n_term, _, n_pos, n_sub = link_prop_list[curr_idx+1].phrase_content
            if n_pos != '名詞':
              updated_link_prop = curr_link_prop

            else:
              # 助詞「の」における処理
              if c_sub == 'の':
                if n_term in self.stopwords:
                  updated_link_prop = LinkProp(
                      curr_link_prop.chunk_id, PhraseContent(c_term, c_pos, c_words, n_sub))

                else:
                  updated_link_prop = curr_link_prop

              # 助詞「と」「や」における処理
              elif c_sub in PAEALLEL_PRESENTATION_WORDS:
                updated_link_prop = LinkProp(
                  curr_link_prop.chunk_id, PhraseContent(c_term, c_pos, c_words, n_sub))
                  
              # 例外
              else:
                updated_link_prop = curr_link_prop

          updated_lp_list.append(updated_link_prop)
        
        updated_lp_list.append(link_prop_list[length])
        if updated_lp_list == old_updated_list:
          break

        old_updated_list = updated_lp_list[:]
        
      return updated_lp_list


  def _is_good_pp(self, sub: str) -> bool:
    return sub != 'の' and sub not in PAEALLEL_PRESENTATION_WORDS

  def _extract_cooccurrence(self, link_prop_list: list) -> str:
    cooccurrences = []
    for link_prop in link_prop_list:
      main_term, _, pos, _ = link_prop.phrase_content
      if pos in REQUIREMENT_POS_LIST and main_term not in self.stopwords:
        cooccurrences.append(main_term)

    cooccurrence = WORD_SEPARATOR.join(sorted(set(cooccurrences), key=cooccurrences.index))
    return cooccurrence


  def _analyze(self, sentence: str) -> AnalysisResult:
    chunk_dict, token_dict, _ = self._analyzer.analyze(sentence)
    alloc_dict  = self._analyzer.allocate_token_for_chunk(chunk_dict, token_dict)
    phrase_dict = self._analyzer.extract_representation(chunk_dict, alloc_dict)
    link_dict   = self._analyzer.make_link_dict(chunk_dict, phrase_dict)

    return AnalysisResult(chunk_dict, token_dict, alloc_dict, phrase_dict, link_dict)


  @staticmethod
  def _link_to_flagment(link_list: list, chunk_dict: OrderedDict) -> str:
    flagment = ''.join(chunk_dict[link].phrase for link in link_list)
    return flagment




def main(args):
  sp = Splitter()

  SENTENCE_PROP_FIELD = ['review_id', 'last_review_id', 
                         'sentence_id', 'last_sentence_id',
                         'star', 'title', 'review', 'sentence', 'result']
  SentenceProp = namedtuple('SentenceProp', SENTENCE_PROP_FIELD)

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
          
  extractor = AttributionExtractor(dic_dir)

  for json_path in tqdm(review_jsons, ascii=True):
    for option in option_list:
      extention    = '_extended' if option.is_extended else ''
      restricition = '_ristrict' if option.is_ristrict else ''

      extractor._extend = option.is_extended
      extractor._ristrict = option.is_ristrict

      out_file = json_path.parent / 'prediction{}{}.json'.format(extention, restricition)            

      review_data = json.load(json_path.open(mode='r', encoding='utf-8'),
                              object_pairs_hook=OrderedDict)
      reviews = review_data['reviews']
      category = review_data['category']
      product_name = review_data['product']
      link = review_data['link']
      maker = review_data['maker']
      ave_star = review_data['average_stars']
      stars_dist = review_data['stars_distribution']

      extractor.category = category
      total_review = len(reviews)
      last_review_id = total_review
      sentence_prop_list = []
      for idx, review_info in enumerate(reviews):
        star   = review_info['star']
        title  = review_info['title']
        review = review_info['review']
        # vote   = review_info['vote']
        review_id = idx + 1

        sentences = sp.split_sentence(normalize(review))
        last_sentence_id = len(sentences)
        for sidx, sentence in sentences.items():
          sentence_id = sidx + 1
          result_dict = extractor.extract_attrribution(sentence)
          editted_dict = OrderedDict()
          for attr, flagment in result_dict.items():
            editted_dict[extractor.ja2en[attr]] = flagment

          sentence_prop_list.append(
            SentenceProp(review_id, last_review_id,
                         sentence_id, last_sentence_id,
                         star, title, review, sentence, editted_dict))

      total_sentence = len(sentence_prop_list)
      out_data = OrderedDict()
      out_data['input_file'] = str(json_path)
      out_data['product'] = product_name
      out_data['link'] = link
      out_data['maker'] = maker
      out_data['average_stars'] = ave_star
      out_data['star_distribuition'] = stars_dist
      out_data['total_review'] = total_review
      out_data['total_sentence'] = total_sentence
      out_data['sentences'] = [sentence_prop._asdict() for sentence_prop in sentence_prop_list]

      json.dump(out_data, out_file.open(mode='w', encoding='utf-8'), 
                ensure_ascii=False, indent=4)


if __name__ == "__main__":
  import argparse
  import json
  import pathlib
  import glob
  from functools import partial

  from split_sentence import Splitter
  from normalize import normalize
  
  parser = argparse.ArgumentParser()
  parser.add_argument('dic_dir')
  parser.add_argument('review_dir')