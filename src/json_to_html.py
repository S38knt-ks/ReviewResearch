"""
    様々なプログラムで作られたjsonファイルをhtmlファイルに変換するプログラム
    input_dir配下のすべてのjsonファイルを変換する
"""


import argparse
import json
import glob
import pandas
import os

from tqdm import tqdm
from pprint import pprint
from html_convertor import HtmlConvertor


def main(args):
    input_dir = args.input_dir
    json_list = [
        os.path.abspath(f) 
        for f in glob.glob('{}\\**'.format(input_dir), recursive=True)
        if f.endswith('.json') and os.path.basename(f).startswith('review')
    ]

    normalize = args.normalize
    mark = args.no_mark
    hc = HtmlConvertor(normalize_mode=normalize, mark=mark)
    print(hc.__repr__())
    out_dir = args.out_dir
    for f in tqdm(json_list, ascii=True):
        tqdm.write('\n[file] {}'.format(f))
        html = hc.convert(f)
        # break
        # pprint(html)
        out_name = f.replace('.json', '.html')
        if normalize:
            out_name = out_name.replace('.html', '_normalized.html')

        if mark:
            out_name = out_name.replace('.html', '_mark.html')

        product_dir = '{}\\{}\\{}'.format(
            out_dir, *f.split('\\')[-3:-1]
        )

        if not os.path.exists(product_dir):
            os.makedirs(product_dir)

        out_name = '{}\\{}'.format(
            product_dir, out_name.split('\\')[-1]
        )
    
        with open(out_name, mode='w', encoding='utf-8') as fp:
            fp.write(html)

        # break





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_dir'
    )
    parser.add_argument(
        'out_dir'
    )
    parser.add_argument(
        '--normalize',
        action='store_true',
        default=False
    ),
    parser.add_argument(
        '--no-mark',
        action='store_false',
        default=True
    )

    main(parser.parse_args())