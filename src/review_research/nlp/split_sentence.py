import re
from collections import OrderedDict

REP_MARK = '<SENTENCE>'
class Splitter:
    
  def __init__(self, pattern=r'。+\s*'):
    self._sep_pat = re.compile(pattern)


  def split_sentence(self, text: str) -> OrderedDict:
    sentence_list = self._split(text)
    return self._align_sentence(text, sentence_list)


  def _split(self, text: str):
    sentence_list = self._sep_pat.split(text)
    return sentence_list

  def _align_sentence(self, text: str, sentence_list: list):
    rep_text = text[:]
    for s in sentence_list:
      if s != '':
        rep_text = rep_text.replace(s, REP_MARK, 1)

    separators = [sep for sep in rep_text.split(REP_MARK) if sep != '']
    
    if len(sentence_list) != len(separators):
      diff = len(sentence_list) - len(separators)
      for _ in range(diff):
        separators.append('')

    sentences = OrderedDict()
    sentence_index = 0
    for sentence, separator in zip(sentence_list, separators):
      if sentence != '':
        text = sentence + separator
        sentences[sentence_index] = text.strip()
        sentence_index += 1

    return sentences