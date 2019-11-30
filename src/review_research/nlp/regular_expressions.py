import re

# 1文字の平仮名
ONE_HIRAGANA_REGEX = re.compile(r'[ぁ-ん]')

# 平仮名とカタカナ1文字も除外対象
# TODO どこでこの処理を行うかが不明瞭
ONE_HIRAKANA_REGEX = re.compile(r'[ぁ-んァ-ヶ]')

# MeCabの形態素解析の結果を区切る正規表現
MECAB_RESULT_SPLIT_REGEX = re.compile('\t|,')

# 2文字以上の平仮名
HIRAGANAS_REGEX = re.compile(r'[ぁ-ん]{2,}')

# 2個以上の句点
PERIOD_SEQ_REGEX = re.compile(r'。{2,}')