import argparse
import os
import pprint
import random
from collections import OrderedDict

import pandas
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

def show_histogram(hist, label, title, out_name):
  plt.title(title)
  index = [i for i in range(len(hist))]
  plt.bar(index, hist, tick_label=label, align='center')
  plt.savefig(out_name, dpi=100)
  plt.show()
  plt.close()

def make_line(li):
  return '{}\n'.format(','.join([str(i) for i in li]))

def main(args):
  input_file = args.input_file.replace('\\', '/')
  temp_df = pandas.read_csv(input_file)
  # print(df)

  header = temp_df.columns.values.tolist()
  # for h in header:
  #     print(df[h])

  # key = header[:-1]
  review_key = header[0]
  star_key = header[1]

  df = temp_df.astype({star_key: float})

  # class_0_df = df[df[star_key] > 4.0].sort_values(review_key)
  class_0_df = df.query('{} > 4.0'.format(star_key)).sort_values(review_key)
  # star_class_0 = class_0_df[star_key]
  class_0 = class_0_df.values.tolist()
  print('[class 0]')
  print(class_0_df.describe())
  print()

  # class_1_df = df[(df[star_key] <= 4.0) & (df[star_key] > 3.0)].sort_values(review_key)
  class_1_df = df.query('3.0 < {} <= 4.0'.format(star_key)).sort_values(review_key)
  # star_class_1 = class_1_df[star_key]
  class_1 = class_1_df.values.tolist()
  print('[class 1]')
  print(class_1_df.describe())
  print()

  # class_2_df = df[(df[star_key] <= 3.0) & (df[star_key] > 2.0)].sort_values(review_key)
  class_2_df = df.query('2.0 < {} <= 3.0'.format(star_key)).sort_values(review_key)
  # star_class_2 = class_2_df[star_key]
  class_2 = class_2_df.values.tolist()
  print('[class 2]')
  print(class_2_df.describe())
  print()

  # class_3_df = df[df[star_key] <= 2.0].sort_values(review_key)
  class_3_df = df.query('{} <= 2.0'.format(star_key)).sort_values(review_key)
  # star_class_3 = class_3_df[star_key]
  class_3 = class_3_df.values.tolist()
  print('[class 3]')
  print(class_3_df.describe())
  print()

  histogram = np.array(
      [
          class_0_df[review_key].count(),
          class_1_df[review_key].count(),
          class_2_df[review_key].count(),
          class_3_df[review_key].count()
      ],
      dtype=int
  )
  labels = ['[5.0, 4.0)', '[4.0, 3.0)', '[3.0, 2.0)', '[2.0, 1.0]']

  hist_dict = OrderedDict()
  for h, l in zip(histogram, labels):
    hist_dict[l] = h

  print('[total] {}'.format(np.sum(histogram)))
  pprint.pprint(hist_dict)

  class_list = [class_0, class_1, class_2, class_3]
  class_label = ['class_0.csv', 'class_1.csv', 'class_2.csv', 'class_3.csv']
  class_dict = OrderedDict()
  for l, c in zip(class_label, class_list):
    class_dict[l] = c


  in_file = input_file.split('/')[-1]

  out_dir = '/'.join(input_file.split('/')[:-1])
  title = '{} histogram'.format(in_file)
  show_histogram(histogram, labels, title, '{}/histogram_4class.png'.format(out_dir))

  header_line = make_line(header)
  for cl in tqdm(class_dict, ascii=True):
    out_file = '{}/{}'.format(out_dir, cl)
    with open(out_file, mode='w', encoding='utf-8') as f:
      f.write(header_line)
      for data in class_dict[cl]:
        f.write(make_line(data))




if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      'input_file'
  )
  # parser.add_argument(
  #     '--extract',
  #     type=int,
  #     default=10
  # )

  main(parser.parse_args())
