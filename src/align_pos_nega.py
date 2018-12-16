import argparse
import os
import pandas

def main(args):
    header = ('Phrase', 'Polarity', 'Subj_or_Obj')

    pn_df = pandas.read_csv(
        args.dictionary, 
        sep=args.separator, names=header, encoding='utf-8',dtype=str
    )

    print(pn_df)

    key = header[1]
    
    negative_df = pn_df.query('{} == "n"'.format(key))
    positive_df = pn_df.query('{} == "p"'.format(key))
    other_df = pn_df.query('{} == "e"'.format(key))

    print('[positive]\n', positive_df, '\n')
    print('[negative]\n', negative_df, '\n')
    print('[other]\n', other_df, '\n')

    print('[positive]\n', positive_df.count(), '\n')
    print('[negative]\n', negative_df.count(), '\n')
    print('[other]\n', other_df.count(), '\n')



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'dictionary'
    )
    parser.add_argument(
        'separator'
    )
    parser.add_argument(
        'out_dir'
    )

    main(parser.parse_args())
    