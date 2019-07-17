import argparse
import pathlib
import glob
import json
import shutil

from collections import OrderedDict, namedtuple
from pprint import pprint
from tqdm import tqdm

JsonDirectory = namedtuple('JsonDirectory', ['product', 'category'])

def main(args):
    result_dir = args.result_dir
    review_jsons = [f for f in glob.glob('{}/**'.format(result_dir), recursive=True)
                    if pathlib.Path(f).name == 'review.json']

    # 評価クラスごとに分ける
    classdiv_dict = OrderedDict()
    for review_json in review_jsons:
        review_json_path = pathlib.Path(review_json)
        product_dir = review_json_path.parent
        category = product_dir.parent.name
        review_data = json.load(review_json_path.open(mode='r', encoding='utf-8'),
                                object_pairs_hook=OrderedDict)
        avg_stars = review_data['average_stars']
        if avg_stars > 4.0:
            classdiv_dict.setdefault('5-4', []).append(JsonDirectory(product_dir, category))

        if avg_stars <= 4.0 and avg_stars > 3.0:
            classdiv_dict.setdefault('4-3', []).append(JsonDirectory(product_dir, category))

        if avg_stars <= 3.0 and avg_stars > 2.0:
            classdiv_dict.setdefault('3-2', []).append(JsonDirectory(product_dir, category))

        if avg_stars <= 2.0:
            classdiv_dict.setdefault('2-1', []).append(JsonDirectory(product_dir, category))


    outdir = pathlib.Path(args.outdir)
    if not outdir.exists():
        outdir.mkdir(parents=True)

    for classdiv, directories in tqdm(classdiv_dict.items(), ascii=True):
        classdiv_dir = outdir / classdiv
        if not classdiv_dir.exists():
            classdiv_dir.mkdir()

        for product_dir, category in directories:
            category_dir = classdiv_dir / category
            if not category_dir.exists():
                category_dir.mkdir()

            product = product_dir.name
            new_product_dir = category_dir / product
            if not new_product_dir.exists():
                shutil.copytree(product_dir, new_product_dir)            


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('result_dir')
    parser.add_argument('outdir')
    
    main(parser.parse_args())