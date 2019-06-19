import json
import os
import glob
import argparse
import numpy as np

from collections import OrderedDict, namedtuple
from pprint import pprint

from prepare_evaluation_data import PRODUCT_NAME, SENTENCES
from alloc_attribute import AttributeAllocation


EVALUATION_FIELD = ['review_id', 'sentence_id', 'sentence', 'answer', 'prediction', 'jaccard_index', 'dice_index']
Evaluation = namedtuple('Evaluation', EVALUATION_FIELD)


def load_eval_json(json_file: str) -> (str, list):
    eval_data = json.load(
        open(json_file, mode='r', encoding='utf-8'),
        object_pairs_hook=OrderedDict
    )

    product_name = eval_data[PRODUCT_NAME]
    sentences = eval_data[SENTENCES]

    return product_name, sentences


def arrange_label(label_list: list) -> OrderedDict:
    label_dict = OrderedDict()
    for label in label_list:
        label_dict[label['name']] = label['flag']

    return label_dict


def predict(allocation: list, labels: list) -> OrderedDict:
    prediction_dict = OrderedDict()
    if len(allocation) == 0:
        for label in labels:
            prediction_dict[label] = 0

    else:
        allocated_attr = [sa.attribute for sa in allocation]
        for label in labels:
            if label in allocated_attr:
                prediction_dict[label] = 1

            else:
                prediction_dict[label] = 0

    return prediction_dict


def make_values(dic: OrderedDict) -> set:
    
    values = set([attr for attr, val in dic.items() if val == 1])
    return values

def calc_jaccard_index(label: OrderedDict, prediction: OrderedDict) -> float:
    label_values = make_values(label)
    pred_values  = make_values(prediction)

    pprint(label_values)
    pprint(pred_values)

    union        = len(set.union(label_values, pred_values))
    intersection = len(set.intersection(label_values, pred_values))

    if union == 0:
        return 1.0
        

    jaccard_index = intersection / float(union)
    return jaccard_index


def calc_dice_index(label: OrderedDict, prediction: OrderedDict) -> float:
    label_values = make_values(label)
    pred_values  = make_values(prediction)

    label_num = len(label_values)
    pred_num  = len(pred_values)

    temp = float(label_num + pred_num)

    if temp == 0:
        return 1.0

    intersection = len(set.intersection(label_values, pred_values))

    dice_index = 2 * intersection / float(label_num + pred_num)
    return dice_index


def main(args):
    eval_json = args.eval_json
    product_name, sentences = load_eval_json(eval_json)

    product_dir, _ = os.path.split(eval_json)
    category_dir, _ = os.path.split(product_dir)
    category = os.path.basename(category_dir)
    allocator = AttributeAllocation(args.dic_dir, category)

    jaccard_index_list = []
    dice_index_list    = []
    evaluations = []
    for sentence in sentences:
        review_id   = sentence['review_id']
        sentence_id = sentence['sentence_id']
        s = sentence['sentence']

        if s == '':
            continue

        # print(s)
        label_list = sentence['attributes']
        label_dict = arrange_label(label_list)
        labels = [*label_dict.keys()]
        # pprint(label_dict)

        allocation = allocator.alloc_attribute(s)
        # pprint(allocation)

        prediction_dict = predict(allocation, labels)

        jaccard_index = calc_jaccard_index(label_dict, prediction_dict)
        jaccard_index_list.append(jaccard_index)

        dice_index    = calc_dice_index(label_dict, prediction_dict)
        dice_index_list.append(dice_index)

        evaluation = Evaluation(
            review_id, sentence_id, s, label_dict, prediction_dict, jaccard_index, dice_index
        )

        evaluations.append(evaluation)

    # pprint(evaluations)

    jaccard_indexes = np.array(jaccard_index_list)
    mean_jaccard_index = np.mean(jaccard_indexes)

    dice_indexes = np.array(dice_index_list)
    mean_dice_index = np.mean(dice_indexes)

    result_data = OrderedDict()
    result_data[PRODUCT_NAME] = product_name
    result_data['total_sentences'] = len(evaluations)
    result_data['mean_jaccard_index'] = mean_jaccard_index
    result_data['mean_dice_index']    = mean_dice_index
    result_data[SENTENCES] = [OrderedDict(e._asdict()) for e in evaluations]

    out_file = '{}\\result.json'.format(product_dir)
    json.dump(result_data, open(out_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=4)
                

        




if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'eval_json'
    )
    parser.add_argument(
        'dic_dir'
    )

    main(parser.parse_args())