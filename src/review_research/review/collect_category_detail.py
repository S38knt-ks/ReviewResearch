import argparse
import os
import glob
import pathlib
from collections import namedtuple

import pandas
from tqdm import tqdm
from bs4 import BeautifulSoup

DETAIL_CSV_HEADER = tuple(['review_num', 'star', 'link'])
DetailData = namedtuple('DetailData', DETAIL_CSV_HEADER)

def get_items(html):
  bs = BeautifulSoup(open(html, mode='r', encoding='utf-8'), 'lxml')
  items = bs.findAll(name='li',
                     attrs={'class': "s-result-item s-result-card-for-container-noborder s-carded-grid celwidget "})

  return items if items else bs.findAll(name='li', attrs={'class': 's-result-item celwidget '})


def extract_detail(item):
  item_review_num = item.find_all('a', attrs={'class': 'a-size-small a-link-normal a-text-normal'})
  if len(item_review_num) == 1:
    item_review_num = item_review_num[0].text.strip()

  else:
    item_review_num = [ir for ir in item_review_num if ir.text.strip().isdecimal()]
    item_review_num = item_review_num[0].text.strip()

  item_star = item.findAll('a', attrs={'class': 'a-popover-trigger a-declarative'})
  if len(item_star) == 1:
    item_star = item_star[0].text.strip()

  else:
    item_star = item_star[-1].text.strip()

  item_review_num = int(item_review_num.replace(',', ''))
  item_star       = item_star.split(' ')[-1]
  item_link       = item.find('a', attrs={'class': 'a-link-normal s-access-detail-page s-color-twister-title-link a-text-normal'}).get('href')
  return DetailData(item_review_num, item_star, item_link)


def main(args):
  category_dir = pathlib.Path(args.category_dir)
  html_list = glob.glob('{}/*.html'.format(category_dir))

  print('extracting data...')
  detail_list = [extract_detail(item) for html in tqdm(html_list, ascii=True)
                                      for item in get_items(html)]
  except_link = 'https://www.amazon.co.jp/gp/slredirect/picassoRedirect.html'
  detail_list = [detail for detail in detail_list if not except_link in detail.link]
  print('done')

  category_name = category_dir.name
  outdir = pathlib.Path(args.out_dir)
  outdir = outdir / category_name
  if not outdir.exists():
    outdir.mkdir(parents=True)

  out_file = outdir / '{}_detail.csv'.format(category_name)
  print('saving data...')
  detail_df = pandas.DataFrame(detail_list)
  detail_df.to_csv(out_file, encoding='utf-8', index=False)
  print('done')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('category_dir')
  parser.add_argument('out_dir')
  main(parser.parse_args())
