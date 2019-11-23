import argparse
import os
import urllib.request
import urllib.parse
import time
import random
import glob
import math
from pprint import pprint
from collections import OrderedDict, namedtuple

import pandas
from bs4 import BeautifulSoup
from tqdm import tqdm

from ..review import DetailData

ProductReviewURL = namedtuple('ProductReviewURL', ['review_num', 'url'])

def load_csv(csv_file):
  df = pandas.read_csv(csv_file)
  header = DetailData(*df.columns.values.tolist())
  review_num, link = header.review_num, header.link
  return df[[review_num, link]].values.tolist()

def make_review_url(url_list: list) -> OrderedDict:
  page_placeholder = 'ref=cm_cr_getr_d_paging_btm_{0}?ie=UTF8&reviewerType=all_reviews&pageNumber={0}'
  url_category = '/product-reviews/'
  url_dict = OrderedDict()

  for review_num, link in url_list:
    review_url = '{}/{}'.format(link.replace('/dp/', url_category), page_placeholder)
    product = urllib.parse.unquote(link.split('/')[3])
    url_dict[product] = ProductReviewURL(review_num, review_url)

  return url_dict

def calc_last_page(review):
  if review > 10:
    return math.ceil(review / 10.0)

  return 1

def get_current_page(product_dir):
  return len(glob.glob('{}/*.html'.format(product_dir)))

  
def request_url(url, page):
  url  = url.format(page)
  html = urllib.request.urlopen(url).read()
  bs   = BeautifulSoup(html, 'lxml')
  return bs


def save_html(out_dir, page, digit, text):
  out_file = '{}/page_{}.html'.format(out_dir, str(page).zfill(digit))
  with open(out_file, mode='w', encoding='utf-8') as fp:
    fp.write(text)


def main(args):
  csv_file = args.csv
  url_dict = make_review_url(load_csv(csv_file))

  in_dir = '/'.join(csv_file.split('\\')[:-1])
  page_fmt = '{0:{1}} / {2:{1}}'
  display_fmt = '[page]\t{}\t[interval]\t{}'
  for product, product_review_url in tqdm(url_dict.items(), ascii=True):
    review_num, url = product_review_url
    last_page = calc_last_page(review_num)
    out_dir = '{}/{}'.format(in_dir, product)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    page  = get_current_page(out_dir) + 1
    digit = len(str(last_page))
    if page > last_page:
        continue
    
    tqdm.write('[product]\t{}'.format(product)) 
    interval = random.randint(7500, 12500) / 1000.0
    time.sleep(interval)
    
    bs = request_url(url, page)
    save_html(out_dir, page, digit, bs.prettify())
    page = page_fmt.format(page, digit, last_page)
    tqdm.write(display_fmt.format(page, interval))

    if page != last_page:
      for i in range(page+1, last_page+1):
        interval = random.randint(10000, 20000) / 1000.0
        time.sleep(interval)
        bs = request_url(url, i)
        save_html(out_dir, i, digit, bs.prettify())
        page = page_fmt.format(i, digit, last_page)
        tqdm.write(display_fmt.format(page, interval))



if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('csv')

  main(parser.parse_args())
