import re
from pprint import pprint

class StopwordRemover:

    def __init__(self):
        dictionary_path = r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\JapaneseStopWord.txt'

        with open(dictionary_path, mode='r', encoding='utf-8') as fp:
            stopword_list = [w.strip() for w in fp.readlines()]


        self.stopwords = [w for w in stopword_list if w is not '']

        # ひらがなとカタカナ1文字も除外対象
        self._hirakata_pat = re.compile(r'[ぁ-んァ-ヶ]')


    def remove(self, word_list: list):
        removed_word_list = [
            w for w in word_list
            if w.word not in self.stopwords and not self._hirakata_pat.match(w.word)
        ]

        return removed_word_list



def main():
    sr = StopwordRemover()
    pprint(sr.stopwords)

if __name__ == "__main__":
    main()