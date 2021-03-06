import argparse
import os
import pathlib
import glob
import inspect
from itertools import product, combinations

import numpy as np
import pandas as pd
from tqdm import tqdm

from review_research.nlp import Tokenizer
from review_research.nlp import ALL_POS
from review_research.nlp import DependencyAnalyzer
from review_research.analysis import CorrPlotter
from review_research.analysis import convert_nan_to_num
from review_research.analysis import Review2Variable

FLAGS = tuple([True, False])
TEXT_LENGTH_ARGS = list(dict(ignore_space=ignore_space) 
                        for ignore_space in product(FLAGS))

COMB_POS = list(pos for pos_num in range(1, len(ALL_POS))
                for pos in combinations(ALL_POS, pos_num))

REVIEW2VARIABLE_ATTRIBUTES = [
    name for name, _ in is_unique_attr(Review2Variable)
]

def is_unique_attr(obj):
  return isinstance(obj, property) or inspect.isfunction(obj)

def define_directory(parent, *children):
  directory = pathlib.Path(parent)
  for child in children:
    directory = directory / child

  if not directory.exists():
    directory.mkdir(parents=True)

  return directory


def plot_respectively(variables, outdir):
  pass

def plot_each_product(variables, outdir):
  outdir = define_directory(outdir, 'each_product')


def main(args):
  result_dir = args.result_dir
  all_files = glob.glob('{}/**'.format(result_dir), recursive=True)
  review_jsons = [f for f in all_files
                  if pathlib.Path(f).name == 'review.json']

  tokenizer = Tokenizer()

  variables = [Review2Variable(review_json, tokenizer) 
               for review_json in review_jsons]
  
  outdir = pathlib.Path(args.outdir)
  if not outdir.exists():
    outdir.mkdir(parents=True)

  outplot_dir = outdir / 'textlen_and_vote'
  plotter = CorrPlotter(figsize=(16, 9))
  textlen_params_to_dirname = {False: 'count_spece', True: 'ignore_space'}
  for v in tqdm(variables, ascii=True):
    vote = v.vote
    product = v.product
    for ignore_space, dirname in textlen_params_to_dirname.items():
      figdir = outplot_dir / dirname
      if not figdir.exists():
        figdir.mkdir(parents=True)

      text_length = v.text_length(ignore_space)
      figname = figdir / '{}.png'.format(product)
      plotter.plot(vote, text_length, 'vote', 'text_length', figname)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('result_dir')
  parser.add_argument('outdir')
  parser.add_argument('target_attr', 
                      choices=REVIEW2VARIABLE_ATTRIBUTES)

  main(parser.parse_args())