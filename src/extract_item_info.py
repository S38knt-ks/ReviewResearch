import argparse
import os
import glob
import pprint

from bs4 import BeautifulSoup
from tqdm import tqdm


def get_items(html):
    bs = BeautifulSoup(open(html, mode='r', encoding='utf-8'), 'lxml')

    items = bs.findAll(
        name='li',
        attrs={
            'class': "s-result-item s-result-card-for-container-noborder s-carded-grid celwidget "
        }
    )

    if items:
        return items
    
    else:
        items = bs.findAll(
            name='li',
            attrs={
                'class': 's-result-item celwidget '
            }
        )

        return items


def extract_detail(item):
    # pprint.pprint(item)

    item_link = item.find(
        'a',
        attrs={
            'class': 'a-link-normal s-access-detail-page s-color-twister-title-link a-text-normal'
        }
    ).get('href')


    item_reviews = item.find_all(
        'a',
        attrs={
            'class': 'a-size-small a-link-normal a-text-normal'
        }
    )

    if len(item_reviews) == 1:
        item_reviews = item_reviews[0].text.strip()

    else:
        item_reviews = [
            ir for ir in item_reviews
            if ir.text.strip().isdecimal()
        ]
        item_reviews = item_reviews[0].text.strip()

    item_stars = item.findAll(
        'a',
        attrs={
            'class': 'a-popover-trigger a-declarative'
        }
    )
    if len(item_stars) == 1:
        item_stars = item_stars[0].text.strip()

    else:
        item_stars = item_stars[-1].text.strip()

    item_stars = item_stars.split(' ')[-1]

    return [item_reviews.replace(',', ''), item_stars, item_link]


def make_line(li):
    return '{}\n'.format(','.join([str(i) for i in li]))


def main(args):
    input_dir = args.input_dir
    html_list = glob.glob('{}/*.html'.format(input_dir))

    print('extracting data...')
    item_list = [
        extract_detail(item)
        for html in tqdm(html_list, ascii=True)
        for item in get_items(html)
    ]
    print('done')

    # item_list = [
    #     extract_detail(item)
    #     for item in get_items(html_list[-1])
    # ]

    # pprint.pprint(item_list)

    header = [
        'reviews',
        'stars',
        'link'
    ]

    in_dir = input_dir.replace('\\', '/').split('/')[-1]
    out_dir = '{}/{}'.format(args.out_dir, in_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    out_file = '{}/{}_detail.csv'.format(out_dir, in_dir)

    except_link = 'https://www.amazon.co.jp/gp/slredirect/picassoRedirect.html'
    item_line_list = [
        make_line(item)
        for item in item_list
        if not except_link in make_line(item)
    ]

    print('saving data...')
    with open(out_file, mode='w', encoding='utf-8') as f:
        f.write(make_line(header))
        for item_line in tqdm(item_line_list, ascii=True):
            f.write(item_line)

    print('done')





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input_dir'
    )
    parser.add_argument(
        'out_dir'
    )

    main(parser.parse_args())
