"""
GUIで相関を見たいレビュー文書内の変数を選択できるようなプログラム

以下を実装
- 入力・出力ディレクトリの指定
- 選択できる変数の作成・抽出
    - 投票数（固定？）
    - 日付
    - レビューの長さ
    - 評価
    - などなど
- 次の分類で相関を見れるように設定
    - 商品ごと
    - 評価クラスごと
    - 製品カテゴリごと
    - 評価クラスと製品カテゴリごと
        - 組み合わせの数は評価クラス数と製品カテゴリ数の積
"""

import os
import glob
import pathlib

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from set_japanese_font import set_font

set_font()

class DirectorySelectDialog(FloatLayout):
    select = ObjectProperty()
    cancel = ObjectProperty()

class Root(FloatLayout):

    data_dir = StringProperty()
    outdir   = StringProperty() 

    def __init__(self, **kwargs):
        super(Root, self).__init__(**kwargs)

    def collect_review_jsons(self):
        review_jsons = [f for f in glob.glob('{}/**'.format(self.data_dir), recursive=True)
                        if pathlib.Path(f).name == 'review.json']
        return review_jsons

    def dismiss_popup(self):
        self._popup.dismiss()

    def set_dir(self, dirname):
        # print(dirname)
        self.data_dir = dirname[0]
        review_jsons = self.collect_review_jsons()
        self.ids['review_json_list'].text = '\n'.join(review_jsons)
        self.dismiss_popup()


    def select_dir(self):
        content = DirectorySelectDialog(select=self.set_dir, 
                                        cancel=self.dismiss_popup)
        self._popup = Popup(title='フォルダ選択',
                            content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()


class CorrVariableChooserApp(App):

    def __init__(self, **kwargs):
        super(CorrVariableChooserApp, self).__init__(**kwargs)
        self.title = '変数選択'

    def build(self):
        return Root()


if __name__ == "__main__":
    CorrVariableChooserApp().run()