import os
import glob
import argparse
import re
import subprocess

import tkinter as tk
from tkinter import ttk

from collections import OrderedDict, namedtuple
from pprint import pprint
from tqdm import tqdm


TARGETS = ['edge', 'distribution', 'origin']
Targets = namedtuple('Targets', TARGETS)
TARGET_LABELS = Targets(*TARGETS)


TARGET_CONTAIER = {
    TARGET_LABELS.edge:         re.compile(r'.*review_edge.+html'),
    TARGET_LABELS.distribution: re.compile(r'.*review_distribution.+html'),
    TARGET_LABELS.origin:       re.compile(r'^(?!.*(edge|distribution)).*$')
}

CHROME_PATH = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'

# PROP_LIST = ['categoty', 'product', 'path']
# HtmlProp = namedtuple('html_prop', PROP_LIST)


class HtmlShower(tk.Frame):

    def __init__(self, indir, master=None):
        super().__init__(master)
        self.selected = None
        self.indir  = indir
        self.target = TARGET_LABELS.distribution
        self.no_normalize = True
        self.mark = True

        review_html_pattern = re.compile(r'(.*\\)+review.*\.html')
        self.all_html_list = [
            os.path.abspath(f).replace('\\', '/')
            for f in glob.glob('{}/**'.format(self.indir), recursive=True)
            if review_html_pattern.match(f)
        ]

        self.normalize_pattern = re.compile(r'(.*\\)+review.*_normalized.+html')
        self.mark_parttern = '_mark.html'

        self.target_button = None
        self.normalize_button = None
        self.mark_button = None

        self._make_html_list()
        self._create_widgets()
        self.pack()

    def _create_widgets(self):
        print('create widgets')
        # pprint(self.html_dict)
        # 大枠
        pw_main = tk.PanedWindow(self.master, orient='horizontal')
        pw_main.pack(expand=True, fill=tk.BOTH)

        # 左枠(カテゴリやフィルタの選択、選択したカテゴリのブラウザ表示操作用)
        pw_left = tk.PanedWindow(self.master, orient='vertical')
        pw_main.add(pw_left)

        # 右枠(選択されたカテゴリのhtmlリストの表示用)
        pw_right = tk.PanedWindow(self.master, orient='vertical')
        pw_main.add(pw_right)

        # htmlリストを表示させるフレーム
        fm_result = tk.Frame(pw_right, bd=2, relief='ridge')
        pw_right.add(fm_result)

        # htmlリストを表示させるテキスト
        self.selected_html = tk.Text(fm_result, height=40, width=200, wrap=tk.NONE)
        self.selected_html.grid(row=0, column=0, padx=2, pady=2)

        # カテゴリを選択するためのフレーム
        fm_select = tk.Frame(pw_left, bd=2, relief='ridge')
        pw_left.add(fm_select)

        label_category = tk.Label(fm_select, text='カテゴリ一覧')
        label_category.grid(row=0, column=0, padx=2, pady=2)

        # カテゴリリスト
        categoty_tuple = tuple([*self.html_dict.keys()])
        category_listvariable = tk.StringVar(value=categoty_tuple)
        self.lb_category = tk.Listbox(fm_select, selectmode=tk.SINGLE, listvariable=category_listvariable)
        self.lb_category.bind('<<ListboxSelect>>', self._print_html_list)
        self.lb_category.grid(row=0, column=1, padx=2, pady=2)

        # 選択されたカテゴリのhtmlファイルをブラウザで開くためのボタン
        btn_show = tk.Button(fm_select, text='表示', command=self._show_html_list)
        btn_show.grid(row=1, column=1, padx=2, pady=2, sticky=tk.W + tk.E)


        # htmlファイルのフィルタのためのフレーム
        fm_change_buttons = tk.Frame(pw_left, bd=2, relief='ridge')
        fm_change_buttons.pack(side='top')
        pw_left.add(fm_change_buttons)

        target_label = tk.Label(fm_change_buttons, text='htmlターゲット')
        target_label.grid(row=0, column=0, padx=2, pady=5)

        self.btn_target_dict = OrderedDict()


        # 両端(edge)を表示するhtmlのフィルタ
        btn_edge = ttk.Button(
            fm_change_buttons, text=str(TARGET_LABELS.edge).capitalize(),
            command=lambda:self._change_target(TARGET_LABELS.edge)
        )
        btn_edge.grid(row=0, column=1, padx=2, pady=5)
        self.btn_target_dict[TARGET_LABELS.edge] = btn_edge

        # 分布(distribution)に基づいて表示するhtmlのフィルタ
        btn_dist = ttk.Button(
            fm_change_buttons, text=str(TARGET_LABELS.distribution).capitalize(),
            command=lambda:self._change_target(TARGET_LABELS.distribution)
        )
        btn_dist.grid(row=0, column=2, padx=2, pady=5)
        self.btn_target_dict[TARGET_LABELS.distribution] = btn_dist

        # もともと(origin)を表示するhtmlのフィルタ
        btn_origin = ttk.Button(
            fm_change_buttons, text=str(TARGET_LABELS.origin).capitalize(),
            command=lambda:self._change_target(TARGET_LABELS.origin)
        )
        btn_origin.grid(row=0, column=3, padx=2, pady=5)
        self.btn_target_dict[TARGET_LABELS.origin] = btn_origin

        # 最初に適用するフィルタを選択しておく
        self.target_button = self.btn_target_dict[self.target]
        self.target_button.state(['pressed'])


        normalize_label = tk.Label(fm_change_buttons, text='normalizeスイッチ')
        normalize_label.grid(row=1, column=0, padx=2, pady=5)
        
        self.normalize_button_dict = OrderedDict()

        # 正規化を行ったhtmlのフィルタ
        normalize_button = ttk.Button(
            fm_change_buttons, text='Normalize',
            command=lambda:self._change_normalization(False)
        )
        normalize_button.grid(row=1, column=1, padx=2, pady=5)
        self.normalize_button_dict[False] = normalize_button

        # 正規化を行わなかったhtmlのフィルタ
        no_normalize_button = ttk.Button(
            fm_change_buttons, text='No Normalize',
            command=lambda:self._change_normalization(True)
        )
        no_normalize_button.grid(row=1, column=2, padx=2, pady=5)
        self.normalize_button_dict[True] = no_normalize_button

        # 最初に適用するフィルタを選択しておく
        self.normalize_button = self.normalize_button_dict[self.no_normalize]
        self.normalize_button.state(['pressed'])


        mark_label = tk.Label(fm_change_buttons, text='marker')
        mark_label.grid(row=2, column=0, padx=2, pady=5)
        
        self.mark_button_dict = OrderedDict()

        # マーカー付きのhtmlのフィルタ
        mark_button = ttk.Button(
            fm_change_buttons, text='Mark',
            command=lambda:self._change_mark(True)
        )
        mark_button.grid(row=2, column=1, padx=2, pady=5)
        self.mark_button_dict[True] = mark_button

        # マーカーのないhtmlのフィルタ
        no_mark_button = ttk.Button(
            fm_change_buttons, text='No Mark',
            command=lambda:self._change_mark(False)
        )
        no_mark_button.grid(row=2, column=2, padx=2, pady=5)
        self.mark_button_dict[False] = no_mark_button

        # 最初に適用するフィルタを選択しておく
        self.mark_button = self.mark_button_dict[self.mark]
        self.mark_button.state(['pressed'])


        
        
        
    def _print_html_list(self, event=None):
        """
            選択されたカテゴリでフィルタリングされたhtmlリストを右枠に表示
        """
        # print(event)
        idx = self.lb_category.curselection()[0]
        self.selected = [*self.html_dict.keys()][idx]
        # print('[selected] {} (index:{})'.format(self.selected, idx))
        print('[target]\t{}'.format(self.target))
        print('[no-normalize]\t{}'.format(self.no_normalize))
        
        self.selected_html.delete('1.0', tk.END)
        self.selected_html.insert(tk.END, '{}\n'.format('-'*200))
        for h in self.html_dict[self.selected]:
            self.selected_html.insert(tk.END, '|{}\n{}\n'.format('\n|\t'.join(h.split('/')[-2:]), '-'*200))

        self.selected_html.insert(tk.END, '\n\n\t{} html files...'.format(len(self.html_dict[self.selected])))


    def _show_html_list(self):
        """
            右枠に表示されているhtmlを新規ウィンドウでchromeで表示
        """
        if self.selected:
            h_list = self.html_dict[self.selected]
            new_h, others = h_list[0], h_list[1:]
            subprocess.call('"{}" --new-window "{}"'.format(CHROME_PATH, new_h), shell=True)

            for command in ('"{}" "{}"'.format(CHROME_PATH, h) for h in others):
                subprocess.call(command, shell=True)


    def _change_target(self, target: str):
        """
            htmlのターゲット変更
            @param
                target: str
                    TARGET_LABELSの中から選択されたフィルタリング
        """
        self.target_button.state(['!pressed'])
        self.target = target

        self.target_button = self.btn_target_dict[target]
        self.target_button.state(['pressed'])

        self._make_html_list()
        self._print_html_list()


    def _change_normalization(self, no_normalize: bool):
        """
            正規化されたhtmlを選択するか
            @param
                no_normalize: bool
                    True  -> 正規化していないものを表示
                    False -> 正規化したものを表示
        """
        self.normalize_button.state(['!pressed'])
        self.no_normalize = no_normalize

        self.normalize_button = self.normalize_button_dict[no_normalize]
        self.normalize_button.state(['pressed'])

        self._make_html_list()
        self._print_html_list()

    def _change_mark(self, mark):
        self.mark_button.state(['!pressed'])
        self.mark = mark

        self.mark_button = self.mark_button_dict[mark]
        self.mark_button.state(['pressed'])

        self._make_html_list()
        self._print_html_list()


    def _make_html_list(self):
        """
            右側に表示、及びブラウザで表示するhtmlリストの作成
        """

        if self.no_normalize:
            html_list = [h for h in self.all_html_list if h.find('_normalized') == -1]

        else:
            html_list = [h for h in self.all_html_list if h.find('_normalized') != -1]

        # html_list = self.all_html_list
        print('normalize filter', not(self.no_normalize))
        # pprint(html_list)
        # print()

        if self.mark:
            html_list = [h for h in html_list if h.endswith(self.mark_parttern)]

        else:
            html_list = [h for h in html_list if not h.endswith(self.mark_parttern)]

        print('mark filter', self.mark)
        # pprint(html_list)

        product_dict = OrderedDict()
        for h in html_list:
            product = h.split('/')[-2]
            if product in product_dict.keys():
                product_dict[product].append(h)
            
            else:
                product_dict[product] = [h]

        # pprint(product_dict)
        target_pattern = TARGET_CONTAIER[self.target]
        self.html_dict = OrderedDict()
        for h_list in tqdm(product_dict.values(), ascii=True):
            # pprint(h_list)
            if len(h_list) == 1:
                h = h_list[0]

            else:
                temp = [h for h in h_list if target_pattern.search(h)]
                # pprint(temp)
                h = temp[0]

            category = h.split('/')[-3]
            if category in self.html_dict.keys():
                self.html_dict[category].append(h)
            
            else:
                self.html_dict[category] = [h]





def main(args):
    target_dir = args.target_dir

    root = tk.Tk()
    hs = HtmlShower(target_dir, master=root)
    hs.master.title('Html Shower Application')
    hs.master.geometry('1000x500')
    hs.mainloop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'target_dir'
    )

    main(parser.parse_args())