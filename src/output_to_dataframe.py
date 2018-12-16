import MeCab
import pandas
import re

from access_dict import AccessDictionary

class OutputToDataFrame:

    def __init__(self, parser='Ochasen'):
        self.tagger = MeCab.Tagger(parser)
        self.tagger.parse('')

        self.columns = [
            'morpheme',
            'phrase',
            'detail1',
            'detail2',
            'detail3',
            'inflection',
            'conjugation',
            'prototype',
            'reading',
            'pronunciation'
        ]

        self._pattern = '\t|,'
        self._pat_obj = re.compile(self._pattern)

    def to_dataframe(self, text: str, cols=None):
        output = self.tagger.parse(text)
        output_list = [
            self._pat_obj.split(line)
            for line in output.strip().split('\n')
            if line is not u'EOS'
        ]

        count = len(self.columns)

        return pandas.DataFrame(
            [li for li in output_list if len(li) == count],
            columns=self.columns, dtype=str
        )


if __name__ == '__main__':
    otdt = OutputToDataFrame()

    ad = AccessDictionary('pn.csv.m3.120408.trim', 'wago.121808.pn')

    # print('[Noun Dictionary]\n', ad.ND, '\n')

    # print('[Decl Dictionary]\n', ad.DD, '\n')



    text = '''
    母の日に70代の母に贈りました。

シンプルな操作と価格に見合わないくらいの（？）高画質。
6畳の自室で見るだけで、大画面も高機能も不要なので大満足です。母も薄くてキレイと喜んでいました。

あえて言うなら、プラスチックの白枠が少々安っぽいかも。
メタリックな白のほうが良かったですが
値段相応なので許容範囲です。
    '''.strip()

    print(text)

    out_df = otdt.to_dataframe(text)
    print('[dataframe]\n', out_df)

    key_phrase = otdt.columns[1]
    key_proto = otdt.columns[-3]
    content_word_df = out_df.query(
        '{0} in ["形容動詞", "名詞", "動詞", "形容詞", "副詞"] and not({0} == "感動詞")'.format(
            key_phrase
        )
    )[[key_proto, key_phrase]]

    print()

    print('[content_word]\n', content_word_df)

    polar_value = 0
    for content in content_word_df.itertuples():
        
        phrase = content.phrase
        term = content.prototype

        if phrase == "名詞":
            result = ad.ND.query('noun == "{}"'.format(term))['value'].values.tolist()


        else:
            result = ad.DD.query('decl == "{}"'.format(term))['value'].values.tolist()

        if result:
            print('[content word]\n', term, '({}) -> [polar] {}'.format(phrase, result[0]))
            polar_value += result[0]
            

        
    print()
    print('[polar value]', polar_value)

