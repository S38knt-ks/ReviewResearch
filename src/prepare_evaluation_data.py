import json
import argparse
import os
import glob

from tqdm import tqdm
from collections import OrderedDict, namedtuple

from alloc_attribute import AttributeAllocation
from split_sentence import Splitter

PRODUCT_NAME = 'product'
SENTENCES    = 'sentences'

ATTRIBUTE_FIELD = ['name', 'flag']
Attribute = namedtuple('Attribute', ATTRIBUTE_FIELD)

SENTENCE_FIELD = ['review_id', 'last_review_id', 'review', 'sentence_id', 'last_sentence_id', 'sentence', 'attributes']

def set_classes(dic_dir: str, category: str):
    common_dic_dir_name = AttributeAllocation.COMMON_DIR
    common_dic_dir = '{}\\{}'.format(dic_dir, common_dic_dir_name)
    common_dics = [dic for dic in glob.glob('{}\\*.txt'.format(common_dic_dir)) if os.path.isfile(dic)]

    category_dic_dir = '{}\\{}'.format(dic_dir, category)
    category_dics = [dic for dic in glob.glob('{}\\*.txt'.format(category_dic_dir)) if os.path.isfile(dic)]

    attr_dict = OrderedDict()
    all_dics = common_dics + category_dics
    for dic in all_dics:
        attr_key, _ = os.path.splitext(os.path.basename(dic))
        with open(dic, mode='r', encoding='utf-8') as fp:
            attr_name = fp.readline().strip().replace('name:', '')

        attr_dict[attr_key] = attr_name

    return attr_dict


def main(args):
    data_dir = args.data_dir
    json_file_list = [
        f for f in glob.glob('{}\\**'.format(os.path.abspath(data_dir)), recursive=True)
        if os.path.isfile(f) and f.endswith('review.json')
    ]

    splitter = Splitter()



    dic_dir = args.dic_dir
    for json_file in tqdm(json_file_list, ascii=True):
        product_dir, _ = os.path.split(json_file)
        category_dir, _ = os.path.split(product_dir)
        category = os.path.basename(category_dir)

        attribute_dict = set_classes(dic_dir, category)
        attribute_list = [*attribute_dict.keys()]
        Attributes = namedtuple('Attributes', attribute_list)
        attribute_pairs = [Attribute(name, 0) for name in attribute_dict.values()]
        attributes = Attributes(
            *[attr._asdict() for attr in attribute_pairs]
        )

        Sentence = namedtuple('Sentence', SENTENCE_FIELD)

        evaluation_data = OrderedDict()

        product_name = os.path.basename(product_dir)
        evaluation_data[PRODUCT_NAME] = product_name

        review_data = json.load(open(json_file, mode='r', encoding='utf-8'), object_pairs_hook=OrderedDict)
        reviews = review_data['reviews']
        total_review = len(reviews)

        all_sentence_list = []
        for idx, review_info in enumerate(reviews):
            review_id = idx
            review = review_info['review']

            sentences = splitter.split_sentence(review)
            last_sentence_id = len(sentences)
            sentence_list = [
                Sentence(review_id + 1, total_review, review, sentence_id + 1, last_sentence_id, sentence, attributes)
                for sentence_id, sentence in sentences.items()
            ]
            all_sentence_list.extend(sentence_list)
        

        total_sentence = len(all_sentence_list)

        evaluation_data['total_review']   = total_review
        evaluation_data['total_sentence'] = total_sentence

        evaluation_data[SENTENCES] = [OrderedDict(s._asdict()) for s in all_sentence_list]

        out_file = '{}\\eval.json'.format(product_dir)
        json.dump(
            evaluation_data,
            open(out_file, mode='w', encoding='utf-8'),
            ensure_ascii=False,
            indent=4
        )







if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'data_dir'
    )

    parser.add_argument(
        'dic_dir'
    )

    main(parser.parse_args())