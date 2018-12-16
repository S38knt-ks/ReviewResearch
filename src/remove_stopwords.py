
from pprint import pprint

class StopwordRemover:

    def __init__(self):
        dictionary_path = 'C:\\Users\\ms338\\Desktop\\html_for_review\\JapaneseStopWord.txt'

        with open(dictionary_path, mode='r', encoding='utf-8') as fp:
            stopword_list = [w.strip() for w in fp.readlines()]

        self.stopwords = [w for w in stopword_list if w is not '']


    def remove(self, word_list: list):
        removed_word_list = [
            word
            for word in word_list
            if word not in self.stopwords
        ]
        return removed_word_list



def main():
    sr = StopwordRemover()
    pprint(sr.stopwords)

if __name__ == "__main__":
    main()