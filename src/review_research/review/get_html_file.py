import argparse
import os
import time
import random
import urllib.request
from pprint import pprint
from typing import List, Tuple

import pandas
from bs4 import BeautifulSoup
from tqdm import tqdm


def read_txt(txt: str,
             encoding: str = 'utf-8') -> Tuple(List[str], pandas.DataFrame):
  """指定されたフォーマットで書かれた、 txt ファイルを読み込む
  フォーマットに関しては次の通り

  # 「# 」から始まる行はコメントとして扱われる
  # DetaFrameのヘッダ情報(商品カテゴリ, 商品一覧ページのページ数, 商品一覧ページ)
  category, last_page, link
  # 次の行から「, 」区切りでヘッダ情報に基づいた値が埋められる(下記は例)
  camera, 10, https://www.amazon.com

  Args:
    txt (str): 上記フォーマットで記述された txt ファイル
    encoding (str): ファイルエンコーディング

  Returns:
    txt で与えられた情報をまとめたもの
  """
  with open(txt, mode='r', encoding=encoding) as fp:
    content = [line.strip().split(', ') for line in fp.readlines()
               if not(line == ('\n')) and not(line.startswith('# '))]

  columns, data = content[0], content[1:]
  return columns, pandas.DataFrame(data, columns=columns) 


def search_target(category: str, df: pandas.DataFrame, 
                  header: List[str]) -> List[str]:
  """指定された商品カテゴリと一致した情報を取得

  Args:
    category (str): 商品カテゴリ
    df (pandas.DataFrame): txt ファイル内の情報を格納したもの
    header (List[str]): df のヘッダ

  Returns:
    商品カテゴリ, 商品一覧ページのページ数, 商品一覧ページのURL
  """
  category_list = df[header[0]].values.tolist()
  if category not in category_list:
    print()
    print('[Error] your category "{}" is invalid...'.format(category))
    print('valid categories are below')
    pprint(sorted(category_list), indent=4)
    quit()

  return df.query('{} == "{}"'.format(header[0], category)).values.tolist()[0]


def replace_page(url: str, page: int) -> str:
  """URL を部分的に置換する

  Args:
    url (str): 対象となる URL
    page (int): ページ番号

  Returns:
    置換された URL
  """
  ref_fmt = 'ref=sr_pg_{}'
  page_fmt = 'page={}'
  ref_target  = ref_fmt.format(page - 1)
  pag_target = page_fmt.format(page - 1)
  ref = ref_fmt.format(page)
  pag = page_fmt.format(page)
  return url.replace(ref_target, ref).replace(pag_target, pag)

def main(args):
  link_txt = args.link_txt
  # print('[link txt]', link_txt)

  print('reading...')
  header, df = read_txt(link_txt)

  category = args.category
  target_list = search_target(category, df, header)
  # pprint(target_list)

  last_page = int(target_list[1])
  url = target_list[2]

  out_dir = args.out_dir
  out_dir = os.path.join(out_dir, category)
  if not os.path.exists(out_dir):
      os.makedirs(out_dir)

  digit = int(len(str(last_page)))
  for page in tqdm(range(1, last_page + 1), ascii=True):
    time.sleep(random.randint(7500, 12500)/1000)
    url = replace_page(url, page)
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'lxml')

    htmlfile = 'page_{}.html'.format(str(page).zfill(digit))
    out_file = os.path.join(out_dir, htmlfile)
    with open(out_file, mode='w', encoding='utf-8') as fp:
      fp.write(soup.prettify())


  print('done!')

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('link_txt')
  parser.add_argument('out_dir')
  parser.add_argument('category')
  main(parser.parse_args())
