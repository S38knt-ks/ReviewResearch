import CaboCha
import argparse
import re

from collections import OrderedDict, namedtuple
from pprint import pprint

from tokenizer import TOKEN_LIST
from normalize import normalize

CHUNK_PROP_FIELD = ['phrase',
                    'score',
                    'link',
                    'size',
                    'pos',
                    'head',
                    'func',
                    'features']

ChunkProp = namedtuple('ChunkProp', CHUNK_PROP_FIELD)

TOKEN_FEATURE_FIELD = TOKEN_LIST[1:]
TokenFeature = namedtuple('TokenFeature', TOKEN_FEATURE_FIELD)

TOKEN_PROP_FIELD = ['surface',
                    'normalized',
                    'features',
                    'ne',
                    'info',
                    'chunk']

TokenProp = namedtuple('TokenProp', TOKEN_PROP_FIELD)

CONTENT_WORD_FIELD = ['id', 'phrase', 'word']
ContentWord = namedtuple('ContentWord', CONTENT_WORD_FIELD)

PHRASE_CONTENT_FIELD = ['main', 'words', 'pos', 'sub']
PhraseContent = namedtuple('PhraseContent', PHRASE_CONTENT_FIELD)

ANALYSIS_RESULT_FIELD = ['chunk_dict', 'token_dict', 'tree']
AnalysisResult = namedtuple('AnalysisResult', ANALYSIS_RESULT_FIELD)

LINK_PROP_FIELD = ['chunk_id', 'phrase_content']
LinkProp = namedtuple('LinkProp', LINK_PROP_FIELD)

REQUIREMENT_POS_LIST = ['名詞', '形容詞', '動詞', '副詞']

class DependencyAnalyzer:
    """
    係り受け解析器
    """

    def __init__(self):
        self._result_tree = None
        self._parser      = CaboCha.Parser()

        self._a_hiragana_pat = re.compile(r'[ぁ-ん]')


    @property
    def parser(self) -> CaboCha.Parser:
        return self._parser


    def analyze(self, sentence: str) -> AnalysisResult:
        chunk_dict, token_dict = self._parse(sentence)
        return AnalysisResult(chunk_dict, token_dict, self._result_tree)



    def allocate_token_for_chunk(self, chunk_dict: OrderedDict, token_dict: OrderedDict) -> OrderedDict:
        allocation_dict = OrderedDict()
        for chunk_id, chunk_prop in chunk_dict.items():
            token_pos  = chunk_prop.pos
            chunk_size = chunk_prop.size

            tokens = OrderedDict()
            for token_id in range(token_pos, token_pos + chunk_size):
                tokens[token_id] = token_dict[token_id]

            allocation_dict[chunk_id] = tokens

        return allocation_dict


    def extract_representation(self, chunk_dict: OrderedDict, allocation_dict: OrderedDict) -> OrderedDict:
        representation_dict = OrderedDict()
        for chunk_id, chunk_prop in chunk_dict.items():
            chunk_features = chunk_prop.features
            rl = ''
            rh = ''
            lf = ''
            shp0 = ''
            dhp0 = ''
            fhp0 = ''
            for feat in chunk_features:
                if feat.startswith('RL:'):
                    rl = feat.replace('RL:', '', 1)

                elif feat.startswith('RH:'):
                    rh = feat.replace('RH:', '', 1)

                elif feat.startswith('LF:'):
                    lf = feat.replace('LF:', '', 1)

                elif feat.startswith('SHP0:'):
                    shp0 = feat.replace('SHP0:', '', 1)

                elif feat.startswith('DHP0:'):
                    dhp0 = feat.replace('DHP0:', '', 1)

                elif feat.startswith('FHP0:'):
                    fhp0 = feat.replace('FHP0:', '', 1)

            pos = ''
            if shp0 != '':
                pos = shp0

            elif dhp0 != '':
                pos = dhp0

            else:
                pos = fhp0
        
            tokens = allocation_dict[chunk_id]

            ri = 0
            for token_id, token in tokens.items():
                if token.normalized == rl:
                    ri = token_id
                    break

            li = 0
            for token_id, token in tokens.items():
                if token.normalized == rh:
                    li = token_id
                    break

            # print('[{:2} - {:2}]\trl:{} - rh:{}'.format(ri, li, rl, rh))

            words = [
                token.normalized for token in tokens.values()
                if token.features.pos in REQUIREMENT_POS_LIST and not self._a_hiragana_pat.match(token.surface) 
            ]

            if lf == rl and lf == rh:
                lf = ''

            if rl == rh:
                representation_dict[chunk_id] = PhraseContent(tokens[ri].surface, words, pos, lf)
                continue

            
            terms = [t for i, t in tokens.items() if i in range(ri, li+1)]
            if terms[0].features.pos == '記号':
                terms.remove(terms[0])

            if terms[-1].features.pos == '記号':
                terms.remove(terms[-1])


            term = ''.join(t.surface for t in terms)    
            representation_dict[chunk_id] = PhraseContent(term, words, pos, lf)

        return representation_dict

            
    def make_link_dict(self, chunk_dict: OrderedDict, representation_dict: OrderedDict) -> OrderedDict:
        visited = []
        link_dict = OrderedDict()
        for chunk_id in chunk_dict.keys():
            if chunk_id in visited:
                continue
        
            link = chunk_id
            link_list = [link]
            while True:
                chunk_prop = chunk_dict[link]
                next_link = chunk_prop.link
                if next_link == -1:
                    break

                link = next_link
                link_list.append(link)

            # print('link')
            # pprint(link_list, indent=4)

            link_prop_list = []
            for link in link_list:
                if link not in visited:
                    visited.append(link)

                # print('\t{}\t{}'.format(link, representation_dict[link]))
                link_prop_list.append(LinkProp(link, representation_dict[link]))

            link_dict[chunk_id] = link_prop_list

        return link_dict


    def _parse(self, sentence: str):
        self._result_tree = None
        tree = self.parser.parse(sentence)
        self._result_tree = tree.toString(CaboCha.FORMAT_TREE)

        chunk_list = [
            self._allocate_chunk_fields(tree.chunk(i), self._make_phrase(tree, tree.chunk(i)))
            for i in range(tree.chunk_size())
        ]

        chunk_dict = OrderedDict()
        for idx, chunk_prop in enumerate(chunk_list):
            chunk_dict[idx] = chunk_prop

        token_list = [
            self._allocate_token_fields(tree.token(i)) for i in range(tree.token_size())
        ]

        token_dict = OrderedDict()
        for idx, token_prop in enumerate(token_list):
            token_dict[idx] = token_prop

        return chunk_dict, token_dict

    
    def _make_phrase(self, tree, chunk: CaboCha.Chunk) -> str:
        phrase = ''.join(str(tree.token(i).surface) 
                         for i in range(chunk.token_pos, chunk.token_pos + chunk.token_size))
        return phrase
    

    def _allocate_chunk_fields(self, chunk: CaboCha.Chunk, phrase: str) -> ChunkProp:
        return ChunkProp(phrase,
                         chunk.score,
                         chunk.link,
                         chunk.token_size,
                         chunk.token_pos,
                         chunk.head_pos,
                         chunk.func_pos,
                         [str(chunk.feature_list(i)) for i in range(chunk.feature_list_size)])


    def _allocate_token_fields(self, token: CaboCha.Token) -> TokenProp:
        feature = token.feature
        features = feature.split(',')
        total_feature = len(features)
        total_token_feature = len(TOKEN_FEATURE_FIELD)
        if total_feature != total_token_feature:
            if total_feature > total_token_feature:
                features = features[0:total_token_feature]

            if total_feature < total_token_feature:
                diff = total_token_feature - total_feature
                additional_feature = ['*' for i in range(diff)]
                features.extend(additional_feature)

        token_feature = TokenFeature(*features)
        if token_feature.base_form == '*':
            token_feature = TokenFeature(token_feature.pos,
                                         token_feature.pos_detail1,
                                         token_feature.pos_detail2,
                                         token_feature.pos_detail3,
                                         token_feature.infl_type,
                                         token_feature.infl_form,
                                         token.surface,
                                         token_feature.reading,
                                         token_feature.phonetic)


        return TokenProp(token.surface,
                         token.normalized_surface,
                         token_feature,
                         token.ne,
                         token.additional_info,
                         token.chunk)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'json_file'
    )

    parser.add_argument(
        '--out-file',
        default='output.txt'
    )

    parser.add_argument(
        '--code',
        default='utf-8'
    )

    args = parser.parse_args()

    import json
    import os
    import re
    
    from split_sentence import Splitter


    jf = args.json_file
    code = args.code

    review_data = json.load(
        open(jf, mode='r', encoding=code), object_pairs_hook=OrderedDict
    )

    product = review_data['product']
    reviews = review_data['reviews']

    total_reviews = len(reviews)

    da = DependencyAnalyzer()
    sp = Splitter()

    SENTENCE_PROP_FIELD = ['review_id', 'sentence_id', 'sentence', 'chunk_dict', 'result_tree', 'token_dict']
    SentenceProp = namedtuple('SentenceProp', SENTENCE_PROP_FIELD)

    sentence_list = []
    for review_id, review_info in enumerate(reviews):
        review_text = normalize(review_info['review'])
        sentences = sp.split_sentence(review_text)
        for sentence_id, sentence in sentences.items():
            chunk_dict, token_dict, result_tree = da.analyze(sentence)
            sentence_list.append(
                SentenceProp(
                    review_id,
                    sentence_id,
                    sentence,
                    chunk_dict,
                    result_tree,
                    token_dict
                )
            )

    total_sentence = len(sentence_list)

    with open(args.out_file, mode='w', encoding=code) as fp:
        fp.write('<PRODUCT>\t{}\n'.format(product))
        fp.write('<REVIEWS>\t{}\n'.format(total_reviews))
        fp.write('<SENTENCES>\t{}\n\n'.format(total_sentence))

    sep = '{}\n'.format('=' * 79)

    with open(args.out_file, mode='a', encoding=code) as fp:
        for idx, sentence_prop in enumerate(sentence_list):
            fp.write(sep)
            fp.write('<review_id>\t{} / {}\n'.format(sentence_prop.review_id+1, total_reviews))
            fp.write('<sentence_id>\t{} ({} / {})\n'.format(sentence_prop.sentence_id, idx+1, total_sentence))

            sentence = '\n'.join(s.strip() for s in sentence_prop.sentence.split('\n'))
            fp.write('"{}"\n\n'.format(sentence))

            pprint(sentence_prop.chunk_dict, fp)

            fp.write('\n{}\n'.format(sentence_prop.result_tree))

            

            # pprint(sentence_prop.token_dict, fp)

            # fp.write('\n')

            allocation_dict = da.allocate_token_for_chunk(sentence_prop.chunk_dict, sentence_prop.token_dict)
            pprint(allocation_dict, fp)

            fp.write('\n')

            fp.write('<representation>\n')
            representation_dict = da.extract_representation(sentence_prop.chunk_dict, allocation_dict)
            pprint(representation_dict, fp)

            fp.write('\n')

            fp.write('<tree link>\n')
            tree_link = da.make_link_dict(sentence_prop.chunk_dict, representation_dict)
            pprint(tree_link, fp)




