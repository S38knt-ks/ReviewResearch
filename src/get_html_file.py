import argparse
import os
import pandas
import time
import random
import urllib.request

from bs4 import BeautifulSoup
from pprint import pprint
from tqdm import tqdm


def read_txt(txt: str, encode='utf-8') -> (list, pandas.DataFrame):
    with open(txt, mode='r', encoding=encode) as fp:
        content = [
            line.strip().split(', ') for line in fp.readlines()
            if not(line == ('\n')) and not(line.startswith('# '))
        ]

    columns, data = content[0],content[1:]
    return columns, pandas.DataFrame(data, columns=columns) 


def search_target(category: str, df: pandas.DataFrame, header: list) -> list:
    category_list = df[header[0]].values.tolist()
    if category not in category_list:
        print()
        print('[Error] your category "{}" is invalid...'.format(category))
        print('valid categories are below')
        pprint(sorted(category_list), indent=4)
        quit()

    return df.query('{} == "{}"'.format(header[0], category)).values.tolist()[0]


def replace_page(url: str, page: int) -> str:
    _ref = 'ref=sr_pg_{}'
    _pag = 'page={}'
    ref_target  = _ref.format(page - 1)
    pag_target = _pag.format(page - 1)
    ref = _ref.format(page)
    pag = _pag.format(page)
    return url.replace(ref_target, ref).replace(pag_target, pag)

def main(args):
    link_txt = args.link_txt
    # print('[link txt]', link_txt)

    print('reading...')
    header, df = read_txt(link_txt)

    # print('[header]')
    # print(header)
    # print('[content]')
    # print(df)

    category = args.category
    target_list = search_target(category, df, header)
    # pprint(target_list)

    last_page = int(target_list[1])
    url = target_list[2]

    out_dir = args.out_dir
    out_dir = '{}/{}'.format(out_dir, category)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    digit = int(len(str(last_page)))
    for page in tqdm(range(1, last_page + 1), ascii=True):
        time.sleep(random.randint(7500, 12500)/1000)
        url = replace_page(url, page)
        html = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(html, 'lxml')

        out_file = '{}/page_{}.html'.format(out_dir, str(page).zfill(digit))
        with open(out_file, mode='w', encoding='utf-8') as fp:
            fp.write(soup.prettify())


    print('done!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'link_txt'
    )
    parser.add_argument(
        'out_dir'
    )
    parser.add_argument(
        'category'
    )
    main(parser.parse_args())
