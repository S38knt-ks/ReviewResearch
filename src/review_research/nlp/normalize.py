"""文書の前処理として、正規化を行うための関数群
ここでいう正規化は、カタカナの種類をそろえたり、英文の大文字を小文字にしたりする処理のこと
"""

import re
import unicodedata

NUMBERS_REGEX = re.compile(r'\d+')
NORMAL_FORMS = ('NFC', 'NFKC', 'NFD', 'NFKD')

def normalize(text: str):
  """与えられた文を正規化する  
  行う正規化は以下の通り

  - 英大文字を英子文字に変換
  - 半角カタカナを全角カタカナに変換

  Args:
    text (str): 正規化対象の文字列

  Returns:
    正規化された文字列
  """
  normalized_text = lower_text(normalize_unicode(text))
  # normalized_text = lower_text(normalize_number(normalize_unicode(text)))
  return normalized_text

def lower_text(text: str):
  """英大文字を英子文字に変換する

  Args:
    text (str): 対象の文字列

  Returns:
    変換後の文字列
  """
  return text.lower()

def normalize_unicode(text: str, form: str = 'NFKC'):
  """Unicode正規化を行う  
  選択できる標準形は以下の通り

  - NFC
  - NFKC
  - NFD
  - NFKD

  Args:
    text (str): 対象の文字列
    form (str): 正規化の標準形(デフォルトでは'NFKC')

  Returns:
    正規化後の文字列

  Raises:
    ValueError: formの標準形の指定が間違っていた場合に発生
  """
  try:
    normalized_text = unicodedata.normalize(form, text)

  except ValueError:
    forms = str(NORMAL_FORMS).replace('(', '').replace(')', '')
    msg = "'{}' is invalid normalization form. only use one of {}."
    raise ValueError(msg.format(form, forms))

  else:
    return normalized_text

def normalize_number(text: str):
  """数字表現を0に置換する

  Examples:
    >>> text = '2019年5月1日は令和元年初日です'
    >>> normalize_number(text)
        0年0月0日は令和元年初日です

  Args:
    text (str): 対象の文字列

  Returns:
    置換後の文字列
  """
  replaced_text = NUMBERS_REGEX.sub('0', text)
  return replaced_text