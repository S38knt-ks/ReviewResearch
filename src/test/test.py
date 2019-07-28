import json
import os

from pprint import pprint
from collections import OrderedDict

from alloc_attribute import AttributeAllocation
from split_sentence import Splitter
from normalize import normalize


def main():
    out_file = 'output.txt'

    dic_dir  = r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\doc\dictionary'

    review_path = r'result\water_purifying_pot\三菱レイヨン・クリンスイ-CP006-BL-ポット型浄水器-アルカリポットクリンスイCP006\review_distribution_23.json'
    review_data = json.load(open(review_path, mode='r', encoding='utf-8'), object_pairs_hook=OrderedDict)
    # category = review_data['category']
    product_dir, _ = os.path.split(review_path)
    category_dir, _ = os.path.split(product_dir)
    category = os.path.basename(category_dir)
    # category = 'mens_shaver'
    reviews = review_data['reviews']

    attr_allocation = AttributeAllocation(dic_dir, category)
    splitter = Splitter()

    with open(out_file, mode='w', encoding='utf-8') as fp:
        fp.write('review_path:{}\n'.format(review_path))

    total_review = len(reviews)
    sep = '--*--'*20 + '\n'
    for review_no, review in enumerate(reviews):
        review_text = review['review']
        normalized_review = normalize(review_text)
        sentences = splitter.split_sentence(normalized_review)
        total_sentence = len(sentences)
        for idx, sentence in sentences.items():
            with open(out_file, mode='a', encoding='utf-8') as fp:
                fp.write('[review#{} / {}] : star {}, vote {}, sentence#{} / {}\n"{}"\n'.format(review_no + 1, total_review, review['star'], review['vote'], idx + 1, total_sentence, sentence))
                word_list = attr_allocation._tokenizer.get_baseforms(sentence, remove_stopwords=False)
                fp.write('<words>\n')
                pprint(word_list, fp)
                fp.write('\n')

                result = attr_allocation.alloc_attribute(sentence)

                fp.write('<sentence attributes>\n')
                pprint(result, fp)
            
                fp.write('<attributes>\n')
                attrs = [sa.attribute for sa in result]
                pprint(attrs, fp)
                fp.write('\n')
            
        with open(out_file, mode='a', encoding='utf-8') as fp:
            fp.write(sep)



if __name__ == "__main__":
    main()