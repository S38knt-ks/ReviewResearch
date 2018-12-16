import argparse
import pandas
import random
import glob

from tqdm import tqdm
from pprint import pprint
from collections import OrderedDict

def main(args):
    inout_dir = args.inout_dir
    holder_dir = glob.glob('{}/*'.format(inout_dir))
    extract = args.how_many

    for hd in holder_dir:
        class_file_list = glob.glob('{}/class*'.format(hd))
        sample_list = []
        memo_dict = OrderedDict()
        out_name = '{}/sample.csv'.format(hd)
        print('[out_name]', out_name)
        for cf in tqdm(class_file_list, ascii=True):
            df = pandas.read_csv(cf)
            header = df.columns.values.tolist()
            key = header[0]

            result_list = df.query('{} >= {}'.format(key, args.threshold)).values.tolist()
            count = len(result_list)
            if count == 0:
                memo_dict[cf] = '1'
                sample_list.append(df.values.tolist()[-1])

            elif count <= extract:
                sample_list.extend(result_list)
                memo_dict[cf] = str(count)

            else:
                sample_list.extend(random.sample(result_list, extract))
                memo_dict[cf] = '{} -> {}'.format(count, extract)

                
        pprint(memo_dict)
            
        with open(out_name, mode='w', encoding='utf-8') as fp:
            fp.write('{}\n'.format(','.join(header)))
            for sample in sample_list:
                fp.write('{}\n'.format(','.join(str(s) for s in sample)))

    
    
            




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'inout_dir'
    )
    parser.add_argument(
        '--how-many',
        type=int,
        default=5
    )
    parser.add_argument(
        '--threshold',
        type=int,
        default=10
    )

    main(parser.parse_args())