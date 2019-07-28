"""
    文書の前処理として、正規化を行うための関数群

    ここでいう正規化は、
    カタカナの種類をそろえたり、英文の大文字を小文字にしたりする処理のこと
"""


import re
import unicodedata


def normalize(text: str):
    normalized_text = lower_text(normalize_unicode(text))
    # normalized_text = lower_text(normalize_number(normalize_unicode(text)))
    return normalized_text



def lower_text(text: str):
    return text.lower()


def normalize_unicode(text: str, form='NFKC'):
    normalized_text = unicodedata.normalize(form, text)
    return normalized_text


def normalize_number(text: str):
    replacer = re.compile(r'\d+')
    replaced_text = replacer.sub('0', text)
    return replaced_text