import argparse
import glob

from output_to_dataframe import OutputToDataFrame
from access_dict import AccessDictionary
from collections import OrderedDict

class PolarityDecision():
    """
        入力された文字列から極性判定を行うという処理をラップしたクラス
    """

    def __init__(self, noun_dict=None, decl_dict=None):
        # 極性辞書の登録
        access_dictionary = AccessDictionary(noun_dict, decl_dict)
        self.ND = access_dictionary.ND
        self.DD = access_dictionary.DD

        # 形態素解析の準備
        self.OTDT = OutputToDataFrame()
        self.phrase_key = self.OTDT.columns[1]
        self.proto_key  = self.OTDT.columns[-3]



    def judge(self, text: str, shown=False) -> (int, str):
        """
            入力された文字列の極性判定
            return (極性値, 極性(Positive, Neutral, or Negative))
        """

        # 形態素解析
        out_df = self.OTDT.to_dataframe(text)
        if shown:
            print('[Morphological Analysys Result]\n', out_df, '\n')

        # 形態素解析結果から必要な情報(形態素の原形と品詞)を取り出す
        content_word_df = out_df.query(
            '{0} in ["形容動詞", "形容詞", "名詞", "動詞", "副詞"] and not({0} == "感動詞")'.format(
                self.phrase_key
            )
        )[[self.proto_key, self.phrase_key]]
        if shown:
            print('[Content Words List]\n', content_word_df, '\n')
            print('[Polarity Calculation]')

        # 各形態素の極性値の合計を文字列の極性値とする
        polarity = sum([
                self._calc_polarity(word, phrase, shown) for _, word, phrase in content_word_df.itertuples()
            ]
        )

        # 極性の判定
        if polarity == 0:
            judge = 'Neutral'

        else:
            judge = 'Positive' if polarity > 0 else 'Negative'

        return polarity, judge


    def _calc_polarity(self, word: str, phrase: str, shown=False) -> int:
        """
            辞書を参照して極性値を求める
        """
        polarity = 0
        if phrase == "名詞":
            # 体言用の辞書
            result = self.ND.query('noun == @word')['value'].values.tolist()

        else:
            # 用言用の辞書
            result = self.DD.query('decl == @word')['value'].values.tolist()
        
        if result:
            polarity += result[0]
            if shown:
                print('\t[result]{:4}\t{}\t{}'.format(polarity, phrase, word))

        return polarity



def main(args):

    text_dir = args.text_dir
    text_list = glob.glob('{}/*{}'.format(text_dir, args.ext))

    result_dict = OrderedDict()

    for text_file in text_list:
        with open(text_file, mode='r', encoding='utf-8') as fp:
            text = ''.join(fp.readlines())

        print('[input]')
        print(text)
        print()

        pd = PolarityDecision('pn.csv.m3.120408.trim', 'wago.121808.pn')
        polarity, judge = pd.judge(text)
        print('\n[polarity]{:4}\t{}\t{}\n'.format(polarity, '---->', judge))

        result_dict[text_file] = (polarity, judge)

    for key, val in result_dict.items():
        print('[{}]\t{}'.format(key, val))

    






if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'text_dir'
    )

    parser.add_argument(
        '--ext',
        default=''
    )
    
    main(parser.parse_args())