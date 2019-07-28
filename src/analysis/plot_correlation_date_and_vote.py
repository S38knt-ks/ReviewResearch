import argparse
import json
import pathlib
import glob
import pandas
import numpy as np
import matplotlib.pyplot as plt

from collections import OrderedDict, namedtuple
from tqdm import tqdm
from itertools import product

DateAndVote = namedtuple('DateAndVote', ['date', 'vote'])
CorrelationInfo = namedtuple('CorrelationInfo', ['target', 'R'])

def extract_date_and_vote(review_json_path, sort=True):
    review_data = json.load(review_json_path.open(mode='r', encoding='utf-8'),
                            object_pairs_hook=OrderedDict)

    date_and_vote_list = [DateAndVote(review['date'], review['vote']) for review in review_data['reviews']]
    if sort:
        date_and_vote_list = sorted(date_and_vote_list, key=lambda dav: dav.date)

    return date_and_vote_list

def split_date_and_vote(date_and_vote_list):
    date = np.array([dav.date for dav in date_and_vote_list])
    vote = np.array([dav.vote for dav in date_and_vote_list], dtype=int)
    return date, vote

def date_to_int_date(date):
    date_to_int = {date: idx for idx, date in enumerate(np.unique(date))}
    int_date = np.zeros(date.shape, dtype=int)
    for date_key in date_to_int:
        int_date[date == date_key] = date_to_int[date_key]

    return int_date

def calc_correlation_coefficients(int_date, vote):
    int_date_series = pandas.Series(int_date)
    vote_series     = pandas.Series(vote)
    return int_date_series.corr(vote_series)

def plot_correlation(int_date, vote, date, figname):
    plt.figure(figsize=(16, 9))
    plt.scatter(int_date, vote)
    plt.xticks(int_date, date, rotation=90)
    plt.xlabel('date')
    plt.ylabel('vote')
    correlation_coefficients = calc_correlation_coefficients(int_date, vote)
    plt.title('R = {}'.format(correlation_coefficients))
    plt.tight_layout()
    plt.savefig(figname)
    plt.clf()
    plt.close()
    return correlation_coefficients

def main(args):
    result_dir = args.result_dir
    review_jsons = [pathlib.Path(f) for f in glob.glob('{}/**'.format(result_dir), recursive=True)
                    if pathlib.Path(f).name == 'review.json']

    outdir = pathlib.Path(args.outdir if args.outdir else result_dir) / 'correlation' / 'date_and_vote'
    if not outdir.exists():
        outdir.mkdir(parents=True)


    # 各商品ごとに相関を見る
    # print('plot each product...')
    # each_product_result_dir = outdir / 'each_product'
    # if not each_product_result_dir.exists():
    #     each_product_result_dir.mkdir()

    # correlation_info_list = []
    # for review_json_path in tqdm(review_jsons, ascii=True):
    #     date_and_vote_list = extract_date_and_vote(review_json_path)
    #     date, vote = split_date_and_vote(date_and_vote_list)
    #     int_date = date_to_int_date(date)

    #     product_name = review_json_path.parent.name
    #     figname = each_product_result_dir / '{}.png'.format(product_name)
    #     R = plot_correlation(int_date, vote, date, figname)
    #     correlation_info_list.append(CorrelationInfo(product_name, R))

    # R_array = np.array([ci.R for ci in correlation_info_list])
    # mean_R = R_array.mean()
    # correlation_info_list.append(CorrelationInfo('mean', mean_R))
    # each_correlation_df = pandas.DataFrame(correlation_info_list)
    # each_correlation_csvname = each_product_result_dir / 'result.csv'
    # each_correlation_df.to_csv(each_correlation_csvname, encoding='utf-8', index=None)

    # 全商品を対象に相関を見る
    # print('plot all product...')
    # all_product_result_dir = outdir / 'all_product'
    # if not all_product_result_dir.exists():
    #     all_product_result_dir.mkdir()

    # all_date_and_vote_list = []
    # for review_json_path in tqdm(review_jsons, ascii=True):
    #     date_and_vote_list = extract_date_and_vote(review_json_path)
    #     all_date_and_vote_list.extend(date_and_vote_list)

    # date, vote = split_date_and_vote(all_date_and_vote_list)
    # int_date = date_to_int_date(date)
    # figname = all_product_result_dir / 'result.png'
    # plot_correlation(int_date, vote, date, figname)

    # all_date_and_vote_df = pandas.DataFrame(sorted(all_date_and_vote_list, key=lambda dav: dav.date))
    # csvname = all_product_result_dir / 'data.csv'
    # all_date_and_vote_df.to_csv(csvname, encoding='utf-8', index=False)


    # 評価クラスおよび商品カテゴリごとに分類
    evalclass_to_pathlist = {}
    category_to_pathlist  = {}
    for review_json_path in review_jsons:
        review_data = json.load(review_json_path.open(mode='r', encoding='utf-8'))
        avg_star = review_data['average_stars']
        evalclass = ''
        if avg_star > 4.0:
            evalclass = '5-4'
        
        elif avg_star > 3.0:
            evalclass = '4-3'

        elif avg_star > 2.0:
            evalclass = '3-2'

        else:
            evalclass = '2-1'

        evalclass_to_pathlist.setdefault(evalclass, []).append(review_json_path)

        category = review_data['category']
        category_to_pathlist.setdefault(category, []).append(review_json_path)


    # 評価クラスごと（商品カテゴリを横断）に相関を見る
    print('plot each evalclass...')
    each_evalclass_result_dir = outdir / 'each_evalclass'
    if not each_evalclass_result_dir.exists():
        each_evalclass_result_dir.mkdir()

    correlation_info_list = []
    for evalclass, pathlist in tqdm(evalclass_to_pathlist.items(), ascii=True):
        evalclass_date_and_vote_list = []
        for review_json_path in pathlist:
            date_and_vote_list = extract_date_and_vote(review_json_path)
            evalclass_date_and_vote_list.extend(date_and_vote_list)

        date, vote = split_date_and_vote(evalclass_date_and_vote_list)
        int_date = date_to_int_date(date)
        figname = each_evalclass_result_dir / '{}.png'.format(evalclass)
        R = plot_correlation(int_date, vote, date, figname)
        correlation_info_list.append(CorrelationInfo(evalclass, R))

    R_array = np.array([ci.R for ci in correlation_info_list])
    mean_R = R_array.mean()
    correlation_info_list.append(CorrelationInfo('mean', mean_R))
    each_correlation_df = pandas.DataFrame(correlation_info_list)
    csvname = each_evalclass_result_dir / 'result.csv'
    each_correlation_df.to_csv(csvname, encoding='utf-8', index=False)

    # 商品カテゴリごと（評価クラスを横断）に相関を見る
    print('plot each category...')
    each_category_result_dir = outdir / 'each_category'
    if not each_category_result_dir.exists():
        each_category_result_dir.mkdir()

    correlation_info_list = []
    for category, pathlist in tqdm(category_to_pathlist.items(), ascii=True):
        category_date_and_vote_list = []
        for review_json_path in pathlist:
            date_and_vote_list = extract_date_and_vote(review_json_path)
            category_date_and_vote_list.extend(date_and_vote_list)

        date, vote = split_date_and_vote(category_date_and_vote_list)
        int_date = date_to_int_date(date)
        figname = each_category_result_dir / '{}.png'.format(category)
        R = plot_correlation(int_date, vote, date, figname)
        correlation_info_list.append(CorrelationInfo(category, R))

    R_array = np.array([ci.R for ci in correlation_info_list])
    mean_R = R_array.mean()
    correlation_info_list.append(CorrelationInfo('mean', mean_R))
    each_correlation_df = pandas.DataFrame(correlation_info_list)
    csvname = each_category_result_dir / 'result.csv'
    each_correlation_df.to_csv(csvname, encoding='utf-8', index=False)

    # 評価クラスと商品カテゴリごとに相関を見る
    print('plot each evalclass and category...')
    evalclass_and_category_to_pathlist = {}
    for evalclass, category in product(evalclass_to_pathlist, category_to_pathlist):
        evalclass_and_category = '{}_{}'.format(evalclass, category)
        evalclass_pathset = set(evalclass_to_pathlist[evalclass])
        category_pathset  = set(category_to_pathlist[category])
        pathlist = list(evalclass_pathset.intersection(category_pathset))
        evalclass_and_category_to_pathlist[evalclass_and_category] = pathlist

    each_evalclass_and_category_result_dir = outdir / 'each_evalclass_and_category'
    if not each_evalclass_and_category_result_dir.exists():
        each_evalclass_and_category_result_dir.mkdir()

    correlation_info_list = []
    for evalclass_and_category, pathlist in tqdm(evalclass_and_category_to_pathlist.items(), ascii=True):
        evalclass_and_category_dav_list = []
        for review_json_path in pathlist:
            date_and_vote_list = extract_date_and_vote(review_json_path)
            evalclass_and_category_dav_list.extend(date_and_vote_list)

        date, vote = split_date_and_vote(evalclass_and_category_dav_list)
        int_date = date_to_int_date(date)
        figname = each_evalclass_and_category_result_dir / '{}.png'.format(evalclass_and_category)
        R = plot_correlation(int_date, vote, date, figname)
        correlation_info_list.append(CorrelationInfo(evalclass_and_category, R))

    R_array = np.array([ci.R for ci in correlation_info_list])
    mean_R = R_array.mean()
    correlation_info_list.append(CorrelationInfo('mean', mean_R))
    each_correlation_df = pandas.DataFrame(correlation_info_list)
    csvname = each_evalclass_and_category_result_dir / 'result.csv'
    each_correlation_df.to_csv(csvname, encoding='utf-8', index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('result_dir')
    parser.add_argument('--outdir')

    main(parser.parse_args())