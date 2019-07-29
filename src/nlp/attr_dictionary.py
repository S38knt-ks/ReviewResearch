import os
import pathlib
import glob

from functools import partial
from collections import namedtuple

AttrName = namedtuple('AttrName', ['en', 'ja'])
AttrDictInfo = namedtuple('AttrDictInfo', ['category', 'name', 'words'])

def search_attr_dict(dic_source_dir):
    glob_recursively = partial(glob.glob, recursive=True)
    all_dictionaries = [pathlib.Path(f) for f in glob_recursively('{}/**'.format(dic_source_dir))
                        if pathlib.Path(f).is_file()]
    return all_dictionaries


def read_attr_dict(dic_path):
    dic_path = pathlib.Path(dic_path)
    with dic_path.open(mode='r', encoding='utf-8') as fp:
        dic_data = [line.strip() for line in fp.readlines()]

    category = dic_path.parent.name
    attr_en_name = dic_path.stem
    attr_ja_name = dic_data[0].replace('name:', '')
    attr_words   = dic_data[1:]
    return AttrDictInfo(category, AttrName(attr_en_name, attr_ja_name), attr_words)

class AttrDictHandler:

    COMMON_DICTIONARY = 'common'

    def __init__(self, dic_source_dir):
        """
        dic_source_dir: 属性辞書の大本のディレクトリ
        """
        self.dic_source_dir = pathlib.Path(dic_source_dir)
        self.all_dictionaries = search_attr_dict(self.dic_source_dir)
        
        # 商品カテゴリごとに整理
        self._category_to_attrdicts = {}
        self._category_to_en2ja_translater = {}
        self._category_to_ja2en_translater = {}
        for dic_path in self.all_dictionaries:
            attr_dict_info = read_attr_dict(dic_path)
            category = attr_dict_info.category

            attr_en_name, attr_ja_name = attr_dict_info.name
            self._category_to_en2ja_translater.setdefault(category, {})[attr_en_name] = attr_ja_name
            self._category_to_ja2en_translater.setdefault(category, {})[attr_ja_name] = attr_en_name

            attr_words = attr_dict_info.words
            self._category_to_attrdicts.setdefault(category, {})[attr_ja_name] = attr_words



    @property
    def common_attr_dict(self):
        return self.attr_dict(self.COMMON_DICTIONARY)

    @property
    def common_en2ja(self):
        return self.en2ja(self.COMMON_DICTIONARY)

    @property
    def common_ja2en(self):
        return self.ja2en(self.COMMON_DICTIONARY)


    def attr_dict(self, category):
        """
        categoryで指定した属性辞書を返す
        """
        return self._category_to_attrdicts[category]

    def en2ja(self, category):
        """
        categoryで指定した属性名の英日変換辞書を返す
        """
        return self._category_to_en2ja_translater[category]

    def ja2en(self, category):
        """
        categoryで指定した属性名の日英変換辞書を返す
        """
        return self._category_to_ja2en_translater[category]


    def remove_intersection_word(self, category):
        """
        categoryで指定した属性辞書において、複数属性にまたがる単語を削除して更新した属性辞書を返す
        """
        attr_dict = self.attr_dict(category)
        attr_list = [*attr_dict.keys()]
        attr_num  = len(attr_list)
        intersection_word_dict = {}
        for target_idx, target_attr in enumerate(attr_list[:-1]):
            target_word_set = set(attr_dict[target_attr])
            intersection_with_target = partial(set.intersection, target_word_set)
            
            for next_idx in range(target_idx+1, attr_num):
                next_attr = attr_list[next_idx]
                next_word_set = set(attr_dict[next_attr])
                intersection_words = list(intersection_with_target(next_word_set))
                for word in intersection_words:
                    intersection_word_dict.setdefault(word, []).append((target_attr, next_attr))

        intersection_words = set(intersection_word_dict.keys())
        if len(intersection_words) == 0:
            return attr_dict

        else:
            new_attr_dict = {}
            for attr_name, words in attr_dict.items():      
                new_words = sorted(set.difference(set(words), intersection_words),
                                   key=words.index)
                new_attr_dict[attr_name] = new_words

            return new_attr_dict


        