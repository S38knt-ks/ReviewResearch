"""
    様々なプログラムで作られたjsonファイルをhtmlファイルに変換するプログラム
    input_dir配下のすべてのjsonファイルを変換する
"""


import argparse
import json
import glob
import pandas
import os
import pathlib

from tqdm import tqdm
from pprint import pprint
from html_convertor import HtmlConvertor


def main(args):
    input_dir = args.input_dir
    json_list = [pathlib.Path(f).resolve() for f in glob.glob('{}\\**'.format(input_dir), recursive=True)
                                           if pathlib.Path(f).name == 'review.json']

    normalize = args.normalize
    mark = args.no_mark
    hc = HtmlConvertor(normalize_mode=normalize, mark=mark)
    out_dir = pathlib.Path(args.out_dir)
    for path in tqdm(json_list, ascii=True):
        tqdm.write('\n[file] {}'.format(path))
        html = hc.convert(path)
        # break
        # pprint(html)
        out_name = path.name.replace('.json', '.html')
        if normalize:
            out_name = out_name.replace('.html', '_normalized.html')

        if mark:
            out_name = out_name.replace('.html', '_mark.html')

        product_dir = out_dir.parent
        out_name = product_dir / out_name
        with out_name.open(mode='w', encoding='utf-8') as fp:
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