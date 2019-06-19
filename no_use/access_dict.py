import pandas
import os
import re
import tkinter

from tkinter import filedialog

class AccessDictionary():

    def __init__(self, 
        noun_dictionary=None, decl_dictionary=None,
        noun_dict_sep='\t', decl_dict_sep='\t',
        noun_dict_cols=['noun', 'polar', 'appendix'],
        decl_dict_cols=['polar', 'decl']
    ):
        if noun_dictionary:
            noun_dict_file = noun_dictionary
        
        else:
            noun_dict_file = self._choose_file()

        nd = self._read_dictionary(noun_dict_file, noun_dict_sep)
        nd_df = pandas.DataFrame(
            nd, columns=noun_dict_cols, dtype=str
        )

        # print(nd_df.query('polar not in ["e", "p", "n"]'))

        nd_sr = nd_df['polar'].map(
            lambda p: p.translate(
                str.maketrans(
                    {
                        'e': '0',
                        'p': '1',
                        'n': '-1'
                    }
                )
            )
        )


        n_values = pandas.Series(
            nd_sr, name='value', dtype=int
        )

        self.ND = pandas.concat([nd_df, n_values], axis=1)

        if decl_dictionary:
            decl_dict_file = decl_dictionary

        else:
            decl_dict_file = self._choose_file()

        dd = self._read_dictionary(decl_dict_file, decl_dict_sep)
        dd_df = pandas.DataFrame(
            dd, columns=decl_dict_cols, dtype=str
        )

        d_values = pandas.Series(
            dd_df['polar'].map(
                lambda p: re.sub(
                    r'ポジ.*', '1', re.sub(
                        r'ネガ.*', '-1', p
                    )
                )
            ), name='value', dtype=int
        )
        self.DD = pandas.concat([dd_df, d_values], axis=1)


        
    def _choose_file(self, f_type=[('', '*')]):
        root = tkinter.Tk()
        root.withdraw()
        init_dir = os.path.abspath(os.path.dirname('__file__'))
        return filedialog.askopenfilename(filetypes=f_type, initialdir=init_dir)


    def _read_dictionary(self, dict_file: str, sep: str):
        with open(dict_file, mode='r', encoding='utf-8') as fp:
            return  [re.split(sep, line.strip()) for line in fp.readlines()]





        