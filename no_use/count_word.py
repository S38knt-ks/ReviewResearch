import argparse
import glob
import json
import pandas

from pprint import pprint
from collections import OrderedDict
from tokenizer import Tokenizer
from decide_polarity import PolarityDecision
from normalize import normalize

def main(args):
    input_dir = args.input_dir
    # review_

    # nd_file = 'pn.csv.m3.120408.trim'
    # dd_file = 'wago.121808.pn'

    tokenizer = Tokenizer()
    # pd = PolarityDecision(nd_file, dd_file)

    product_dict = OrderedDict()
    whole_word_list = []
    columns = ['word', 'count']
    for json_file in (f for f in glob.glob('{}/**'.format(input_dir), recursive=True) if f.endswith('review.json')):
        review_info = json.load(
            open(json_file, mode='r', encoding='utf-8'),
            object_pairs_hook=OrderedDict
        )

        product = review_info['product']
        print('[product] {}'.format(product))
        average_stars = review_info['average_stars']

        review_dict_list = review_info['reviews']
        review_df = pandas.DataFrame(review_dict_list)
        # print(review_df)
        print('[mean star]\t{:.3}\t[reviews]\t{}'.format(average_stars, review_df['review'].count()))

        # polarity_dict = OrderedDict()
        # polarity_dict['Positive'] = 0
        # polarity_dict['Neutral']  = 0
        # polarity_dict['Negative'] = 0

        word_list = [
            w
            for r in review_df['review'].values.tolist()
            for w in tokenizer.get_baseforms(normalize(r))
        ]

        # word_list = []
        # for review in review_df['Review'].values.tolist():
        #     result_df = otdt.to_dataframe(normalize(review))[['morpheme', 'phrase', 'prototype']]
        #     pprint(result_df)
        #     print()

        #     word_df = result_df.query('phrase in ["名詞", "形容詞", "形容動詞", "副詞"]')['prototype']
        #     word_list.extend(word_df.values.tolist())
        #     # value, polarity = pd.judge(review)
        #     # polarity_dict[polarity] += value

        whole_word_list.extend(word_list)


        count_list = list(
            [word, word_list.count(word)]
            for word in sorted(set(word_list))
        )
        # pprint(polarity_dict)

        count_df = pandas.DataFrame(count_list, columns=columns)
        sorted_count_df = count_df.sort_values('count', ascending=False)
        print(sorted_count_df.head(20))
        print()

        product_dict[product] = count_df


    whole_df = pandas.DataFrame(
        [[w, whole_word_list.count(w)] for w in sorted(set(whole_word_list))],
        columns=columns
    )

    print('-'*79)
    print('[whole word counts]')
    print(whole_df.sort_values('count', ascending=False))

            




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_dir'
    )

    main(parser.parse_args())