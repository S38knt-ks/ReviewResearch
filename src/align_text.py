import argparse
import emoji
import re

from collections import namedtuple
from tokenizer import Tokenizer


ALIGNMENT_FIELDS = ['surface', 'word', 'is_token']
Alignment = namedtuple('Alignment', ALIGNMENT_FIELDS)

class TextAlignment:

    REPLACE_MARK = '<<REPL>>'

    def __init__(self):
        self._alignment_list  = None
        self._words           = None
        self._text            = ''
        self._tokenizer       = Tokenizer()

        self._periods_pat = re.compile(r'。{2,}')

    
    @property
    def alignment(self) -> list:
        return self._alignment_list


    @property
    def words(self) -> list:
        return self._words


    @property
    def text(self) -> str:
        return self._text


    def align(self, text: str):
        self._text = self._adjust_text(text)
        self._words = self._tokenizer.get_baseforms(text)
        self._alignment_list = []
        target = self.text[:]
        for w in self.words:
            # print('[word]\t\t{}'.format(w))
            start_idx = target.find(w.surface)
            # print('[start]\t\t{}'.format(start_idx))
            if start_idx == -1:
                continue

            target = target.replace(w.surface, self.REPLACE_MARK, 1)
            # print('-'*79)
            # print(target)
            # print('-'*79)

            if start_idx > 0:
                part = target.split(self.REPLACE_MARK)[0]
                # print('[part]\t\t{}'.format(part))
                self._alignment_list.append(Alignment(part, part, False))
                target = target.replace(part, self.REPLACE_MARK, 1)
                # print('-'*79)
                # print(target)
                # print('-'*79)   

            self._alignment_list.append(Alignment(w.surface, w.word, True))
            target = target.replace(self.REPLACE_MARK, '')
            # print('-'*79)
            # print(target)
            # print('-'*79)
            # print()


        if len(target) > 0:
            self._alignment_list.append(Alignment(target, target, False))

    
    def _adjust_text(self, text: str):
        if text.find('\n') == -1:
            return text

        adjusted_text = ''.join(c for c in text if c not in emoji.UNICODE_EMOJI)

        if text.find('。') != -1:
            adjusted_text = self._periods_pat.sub('。', adjusted_text)

        adjusted_text = ''.join(sentence.strip() for sentence in text.split('\n'))
        return adjusted_text



