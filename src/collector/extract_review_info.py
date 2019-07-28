import argparse
import os
import glob
import json
import re
import time
import traceback

import numpy as np

from pprint import pprint, pformat
from collections import namedtuple, OrderedDict
from bs4 import BeautifulSoup
from tqdm import tqdm

INFO_FIELDS = [
    'date', 'star', 'vote', 'name', 'title', 'review'
]
ReviewInfo = namedtuple('ReviewInfo', INFO_FIELDS)


LANDMARKS = ['link', 'maker', 'average_stars', 'total_reviews']
ReviewLandmarks = namedtuple('ReviewLandmarks', LANDMARKS)


STARS_DISTRIBUTION = ['star1', 'star2', 'star3', 'star4', 'star5']
StarsDistribution = namedtuple('StarsDistribution', STARS_DISTRIBUTION)


JSON_KEYS = [
    'product', 'category', *LANDMARKS, 'real_reviews', 'stars_distribution', 'reviews'
]
ReviewJsonKeys = namedtuple('ReviewJsonKeys', JSON_KEYS)
REVIEW_JSON_KEYS = ReviewJsonKeys(*JSON_KEYS)


class ReviewInfoExtractor:

    def __init__(self, code='utf-8', parser='lxml'):
        self.code   = code
        self.parser = parser

        # BeautifulSoup#find or #findAllの引数を登録するためのタプルの用意
        FIND_ATTRS = ['name', 'attrs']
        FindAttrs = namedtuple('find_attrs', FIND_ATTRS)

        # ReviewLandmarksを取得するための用意
        LANDMARKS_PROP = [LANDMARKS[0], 'div', *LANDMARKS[1:]]
        LandmarksProp = namedtuple('landmarks_prop', LANDMARKS_PROP)
        self.landmarks_prop = LandmarksProp(
            FindAttrs('link', {'rel': 'canonical'}),
            FindAttrs('div', {'role': 'main'}),
            FindAttrs('div', {'class': 'a-row product-by-line'}),
            FindAttrs('i', {'data-hook': 'average-star-rating'}),
            FindAttrs(
                'span',
                {
                    'class': 'a-size-medium totalReviewCount',
                    'data-hook': 'total-review-count'
                }
            )
        )

        # ReviewInfoの範囲を絞るための用意
        self.review_div_fa = FindAttrs(
            'div',
            {
                # 'class': 'a-section review aok-relative',
                'data-hook': 'review'
            }
        )

        # 日付の正規表現
        self.date_pat = re.compile(r'(?P<year>[0-9]*)年(?P<month>[0-9]*)月(?P<day>[0-9]*)日')

        # ReviewInfoを取得するための用意
        ReviewInfoProp = namedtuple('review_info_prop', INFO_FIELDS)
        self.review_info_prop = ReviewInfoProp(
            FindAttrs(
                'span',
                {
                    'class': 'a-size-base a-color-secondary review-date',
                    'data-hook': 'review-date'
                }
            ),
            FindAttrs('i', {'data-hook': 'review-star-rating'}),
            FindAttrs(
                'span',
                {
                    'class': 'a-size-base a-color-tertiary cr-vote-text',
                    'data-hook': 'helpful-vote-statement'
                }
            ),
            FindAttrs('span', {'class': 'a-profile-name'}),
            FindAttrs(
                'a',
                {
                    # 'class': 'a-size-base a-link-normal review-title a-color-base a-text-bold',
                    'data-hook': 'review-title'
                }
            ),
            FindAttrs(
                'span',
                {
                    # 'class': 'a-size-base review-text',
                    'data-hook': 'review-body'
                }
            )
        )

    def extract_all_info(self, html_list: list):
        """
            商品レビューで重要だと思われる情報をすべて抽出する

            @param
                html_list: list
                    商品のhtmlファイルリスト
        """
        self._initialize_data()

        first_html = html_list[0]
        self.category = self._decide_category(first_html)
        self.review_landmarks = self._extract_landmarks(first_html)
        self.all_info = [
            ri
            for h in html_list
            for ri in self._extract_review_info_list(h)
        ]

        
    def save_json(self, out_name: str, product: str):
        """
            抽出した情報をjsonファイルに保存

            @param
                out_name: str
                    出力するjsonファイルの名前

                product: str
                    商品名
        """
        data_dict = OrderedDict()
        data_dict[REVIEW_JSON_KEYS.product]  = product
        data_dict[REVIEW_JSON_KEYS.category] = self.category

        data_dict[REVIEW_JSON_KEYS.link]          = self.review_landmarks.link
        data_dict[REVIEW_JSON_KEYS.maker]         = self.review_landmarks.maker
        data_dict[REVIEW_JSON_KEYS.average_stars] = self.review_landmarks.average_stars 
        data_dict[REVIEW_JSON_KEYS.total_reviews] = self.review_landmarks.total_reviews
        data_dict[REVIEW_JSON_KEYS.real_reviews]  = len(self.all_info)

        stars_distribution = StarsDistribution(*self.stars_distibution_dict.values())
        data_dict[REVIEW_JSON_KEYS.stars_distribution] = OrderedDict(stars_distribution._asdict())
        
        data_dict[REVIEW_JSON_KEYS.reviews] = [OrderedDict(d._asdict()) for d in self.all_info]

        json.dump(
            data_dict,
            open(out_name, mode='w', encoding=self.code),
            ensure_ascii=False,
            indent=4
        )

    
    def _initialize_data(self):
        self.category         = None
        self.review_landmarks = None
        self.all_info         = None

        star_list = np.arange(1, 5+1).astype(float)
        self.stars_distibution_dict = OrderedDict()
        for s in star_list:
            self.stars_distibution_dict[s] = 0


    def _decide_category(self, html_path):
        html_path = os.path.abspath(html_path)
        product_dir, _  = os.path.split(html_path)
        categoty_dir, _ = os.path.split(product_dir)
        _, category     = os.path.split(categoty_dir)
        return category


    def _extract_landmarks(self, html) -> ReviewLandmarks:
        bs = BeautifulSoup(
            open(html, mode='r', encoding=self.code),
            self.parser
        )

        link_fa, div_fa, maker_fa, ave_stars_fa, total_reviews_fa = self.landmarks_prop

        link = bs.find(link_fa.name, link_fa.attrs)['href']

        landmarks_div = bs.find(div_fa.name, div_fa.attrs)

        maker = landmarks_div.find(
            maker_fa.name, maker_fa.attrs
        ).text.strip()

        ave_stars = self._extract_stars(
            landmarks_div.find(ave_stars_fa.name, ave_stars_fa.attrs)
        )

        total_reviews = int(landmarks_div.find(
                total_reviews_fa.name, total_reviews_fa.attrs
            ).text.strip().replace(',', '')
        )

        return ReviewLandmarks(link, maker, ave_stars, total_reviews)


    def _extract_review_info_list(self, html) -> list:
        bs = BeautifulSoup(
            open(html, mode='r', encoding=self.code),
            self.parser
        )

        review_div_list = bs.findAll(
            self.review_div_fa.name,
            self.review_div_fa.attrs
        )

        # tqdm.write(pformat(review_div_list))

        return [self._get_review_info(rv) for rv in review_div_list]


    def _get_review_info(self, review_div) -> ReviewInfo:
        date_fa, star_fa, vote_fa, name_fa, title_fa, review_fa = self.review_info_prop

        date = ''
        star = 0
        vote = 0
        name = ''
        title = ''
        review = ''

        try:
            date = self._extract_date(
                review_div.find(date_fa.name, date_fa.attrs)
            )

            star = self._extract_stars(
                review_div.find(star_fa.name, star_fa.attrs)
            )
            self.stars_distibution_dict[star] += 1

            vote = self._extract_vote(
                review_div.find(vote_fa.name, vote_fa.attrs)
            )

            name = review_div.find(
                name_fa.name, name_fa.attrs
            ).text.strip()

            title = review_div.find(
                title_fa.name, title_fa.attrs
            ).text.strip()

            review = review_div.find(
                review_fa.name, review_fa.attrs
            ).text.strip()

        except AttributeError:
            tqdm.write('<Attribute Error>')
            tqdm.write('{}'.format(traceback.format_exc()))

        return ReviewInfo(date, star, vote, name, title, review)


    def _extract_date(self, content) -> str:
        text = content.text.strip()
        date_text = self.date_pat.match(text)
        date = '{}/{}/{}'.format(
            date_text.group('year'),
            date_text.group('month').zfill(2),
            date_text.group('day').zfill(2)
        )
        return date

    
    def _extract_stars(self, content) -> float:
        text = content.text.strip()
        stars = float(text.replace('5つ星のうち', ''))
        return stars

    
    def _extract_vote(self, content) -> int:
        vote = 0
        if content:
            vote_text = content.text.strip()
            vote = int(vote_text.replace('人のお客様がこれが役に立ったと考えています', ''))

        return vote

        


def main(args):
    input_dir = args.input_dir
    page_pat = re.compile(r'.*\\page_(\d+)\.html')
    review_html_list = sorted(
        [
            os.path.abspath(review_html).replace('\\', '/') for review_html in glob.glob('{}/**'.format(input_dir), recursive=True)
            if page_pat.match(review_html)
        ]
    )

    product_dict = OrderedDict()
    for review_html in review_html_list:
        product_key = '/'.join(review_html.split('/')[:-1])
        product_dict.setdefault(product_key, []).append(review_html)


    print('[products]\t{}'.format(len(product_dict.keys())))
    print('[htmls]\t{}'.format(len(review_html_list)))
    print()

    print('extracting...')
    rie = ReviewInfoExtractor()        
    for product_key, review_html_list in tqdm(product_dict.items(), ascii=True):
        tqdm.write('[product]\t{}'.format(product_key))
        
        tqdm.write('htmls = {}'.format(len(review_html_list)))
        tqdm.write(pformat(review_html_list))

        rie.extract_all_info(review_html_list)

        product = product_key.split('/')[-1]
        out_file = os.path.join(product_key, 'review.json')
        tqdm.write(out_file)
        # out_file = '{}/review.json'.format(product_key)
        rie.save_json(out_file, product)

    print('done!')

        
            


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input_dir'
    )

    main(parser.parse_args())
