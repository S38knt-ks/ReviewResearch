import MeCab
import re

from collections import namedtuple, OrderedDict
from remove_stopwords import StopwordRemover

TOKEN_LIST = [
    'surface',
    'pos',
    'pos_detail1',
    'pos_detail2',
    'pos_detail3',
    'infl_type',
    'infl_form',
    'base_form',
    'reading',
    'phonetic'
]
Token = namedtuple('Token', TOKEN_LIST)
TOKEN_TUPLE = Token(*TOKEN_LIST)

WORD_FIELDS = [TOKEN_TUPLE.surface, 'word']
Word = namedtuple('Word', WORD_FIELDS)

POS_LIST = [
    '名詞',
    # '動詞',
    '形容詞',
    '形容動詞',
    # '副詞'
]


class Tokenizer:
    """
        usage

        tokenizer = Tokenizer()
        text = '何らかの文章'
        word_list = tokenizer.get_baseforms(text)
    """

    TOTAL_FEATURES = 9

    def __init__(self):
        self._tagger  = MeCab.Tagger('Ochasen')
        self._pat_obj = re.compile('\t|,')
        self._correspond_words = OrderedDict()
        self.remover = StopwordRemover()
        self._alignment_list = None


    def get_baseforms(self, text: str, remove=True, pos_list=POS_LIST) -> list:
        """
            形態素解析で得られた結果における原形(または表層)をリスト化して返す
            @param
                text: str
                    形態素解析にかけたい文

                pos_list: list (default ['名詞', '動詞', '形容詞', '形容動詞', '副詞'])
                    品詞のフィルタリングに使うリスト

            @return
                words: list
                    pos_listでフィルタリングされて残った、原形(または表層)の単語リスト
        """
        words = [
            Word(t.surface, t.base_form) if t.base_form != '*' else Word(t.surface, t.surface)
            for t in self._tokenize(text) if t.pos in pos_list
        ]

        if remove:
            return self.remover.remove(words)
                
        else:
            return words


    def _tokenize(self, text: str):
        self._tagger.parse('')

        result = self._tagger.parse(text)
        chunk_list = [
            self._pat_obj.split(line)
            for line in result.strip().split('\n')
            if line is not u'EOS'
        ]

        for chunks in chunk_list:
            if len(chunks) <= 1:
                # print(chunks, len(chunks))
                continue

            surface, *feature = chunks
            num_features = len(feature)
            if num_features == self.TOTAL_FEATURES:
                yield Token(surface, *feature)

            # print(feature)
            elif num_features < self.TOTAL_FEATURES:
                lack = self.TOTAL_FEATURES - num_features
                feature.extend(['' for _ in range(lack)])
                yield Token(surface, *feature)

            else:
                yield Token(surface, *feature[:self.TOTAL_FEATURES])
