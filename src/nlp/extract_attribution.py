import os
import glob

from collections import OrderedDict, namedtuple, defaultdict
from pprint import pprint
from tqdm import tqdm

from analyze_dependency import DependencyAnalyzer

class AttributionExtractor:

    DICTIONARY_PROP_FIELD = ['name', 'path']
    DictionaryProp = namedtuple('DictionaryProp', DICTIONARY_PROP_FIELD)

    ANALYSIS_RESULT_FIELD = ['chunk_dict', 'token_dict', 'alloc_dict', 'phrase_dict', 'link_dict']
    AnalysisResult = namedtuple('AnalysisResult', ANALYSIS_RESULT_FIELD)

    EXTRACTION_RESULT_FIELD = ['attrs', 'flagment', 'candidate_terms', 'hit_terms', 'cooccurrence_words', 'phrases', 'phrase_num']
    ExtractionResult = namedtuple('ExtractionResult', EXTRACTION_RESULT_FIELD)

    EXTRACTION_DETAIL_RESULT = [*EXTRACTION_RESULT_FIELD[1:]]
    ExtractionDetail = namedtuple('ExtractionDetail', EXTRACTION_DETAIL_RESULT)

    STOPWORD_DIC_PATH = 'JapaneseStopWord.txt'

    PAEALLEL_PRESENTATION_WORDS = ['や', 'と']

    BASE_PATTERN_WORDS = ['が', 'は', 'も', 'に', 'を']

    WORD_SEPARATOR = '<WORDSEP>'
    

    def __init__(self, dic_dir: str, category: str, code='utf-8', extend=True, ristrict=True):
        self._category = category
        self._code     = code
        self._extend   = extend
        self._ristrict = ristrict

        self._dic_dict  = OrderedDict()
        self._attr_dict = OrderedDict()

        self._read_stopword_dic()

        dic_list = self._search_dictionaries(dic_dir)
        # pprint(dic_list)
        for dic_prop in dic_list:
            self._read_dictionary(dic_prop)

        self._analyzer = DependencyAnalyzer()


    @property
    def extend(self) -> bool:
        return self._extend


    @property
    def ristrict(self) -> bool:
        return self._ristrict

    @property
    def category(self) -> str:
        return self._category


    @property
    def code(self) -> str:
        return self._code


    @property
    def dic_dict(self) -> OrderedDict:
        return self._dic_dict


    @property
    def attr_dict(self) -> OrderedDict:
        return self._attr_dict

    @property
    def stopwords(self) -> list:
        return self._stopwords


    def extract_attrribution(self, sentence: str) -> OrderedDict:
        analysis_result = self._analyze(sentence)
        result_list = []
        for link_prop_list in analysis_result.link_dict.values():
            attrs = []
            candidate_term_list = []
            hit_terms = []
            link_list = [link_prop.chunk_id for link_prop in link_prop_list]
            flagment = self._link_to_flagment(link_list, analysis_result.chunk_dict)
            # print('<flagment>')
            # print(flagment)
            # print('<link prop>')
            # pprint(link_prop_list)
            # print()
            # print('<candidate prop>')
            candidate_link_prop_list = self._get_canndidate_terms(link_prop_list)
            # pprint(candidate_link_prop_list)
            # print()
            for link_prop in candidate_link_prop_list:
                main_term, words, _, _ = link_prop.phrase_content
                
                candidate_terms = [main_term]
                if self.extend and words:
                    candidate_terms.extend(words)

                candidate_term_list.extend(candidate_terms)

                for attr, words in self.attr_dict.items():
                    for term in candidate_terms:
                        if term in words :
                            hit_terms.append(term)
                            attrs.append(attr)


            

            candidate_terms = self.WORD_SEPARATOR.join(sorted(set(candidate_term_list), key=candidate_term_list.index))
            hit_terms       = self.WORD_SEPARATOR.join(sorted(set(hit_terms), key=hit_terms.index))
            cooccurrences   = self._extract_cooccurrence(link_prop_list)
            phrases         = self.WORD_SEPARATOR.join(link_prop.phrase_content.main for link_prop in link_prop_list)

            result_list.append(self.ExtractionResult(attrs, flagment, candidate_terms, hit_terms, cooccurrences, phrases, len(link_list)))

        result_dict = defaultdict(list)
        for result in result_list:
            for attr in result.attrs:
                detail = self.ExtractionDetail(result.flagment, result.candidate_terms, result.hit_terms, result.cooccurrence_words, result.phrases, result.phrase_num)
                result_dict[attr].append(detail)

        temp_dict = dict(result_dict)
        result_dict = OrderedDict()
        for attr in self.attr_dict.keys():
            if attr in temp_dict.keys():
                details = temp_dict[attr]
                detail_set = sorted(set(details), key=details.index)
                result_dict[attr] = [OrderedDict(detail._asdict()) for detail in detail_set]

        return result_dict

            
    def _read_stopword_dic(self):
        with open(self.STOPWORD_DIC_PATH, mode='r', encoding=self.code) as fp:
            self._stopwords = [line.strip() for line in fp.readlines() if line.strip() != '']


    def _get_canndidate_terms(self, link_list: list) -> list:
        if self.ristrict:
            link_list = self._update_link_prop_list(link_list)

        candidate_link_prop_list = []
        for link_prop in link_list[:-1]:
            main_term, _, pos, sub = link_prop.phrase_content
            if pos != '名詞':
                continue

            elif main_term in self.stopwords:
                continue                

            else:
                if sub in self.BASE_PATTERN_WORDS:
                    candidate_link_prop_list.append(link_prop)

        last_lp = link_list[-1]
        if last_lp.phrase_content.pos == '名詞':
            candidate_link_prop_list.append(last_lp)

        return candidate_link_prop_list


    def _update_link_prop_list(self, link_prop_list: list) -> list:
        length = len(link_prop_list) - 1
        # 更新し終わるまで
        # print('updating...')
        old_updated_list = link_prop_list[:]
        while True:
            updated_lp_list = []
            for curr_idx, curr_link_prop in enumerate(link_prop_list[:-1]):
                # print('\t{}'.format(curr_link_prop))
                c_term, c_words, c_pos, c_sub = curr_link_prop.phrase_content
                # print('\t\t[is goog pp]\t{}'.format(self._is_good_pp(c_sub)))
                if c_pos != '名詞':
                    # print('\t\t[hit in not noun]\t{}'.format(curr_link_prop))
                    updated_link_prop = curr_link_prop

                elif c_pos == '名詞' and self._is_good_pp(c_sub):
                    # print('\t\t[hit in noun @good]\t{}'.format(curr_link_prop))
                    updated_link_prop = curr_link_prop

                elif c_term in self.stopwords:
                    # print('\t\t[hit in @sp]\t{}'.format(curr_link_prop))
                    updated_link_prop = curr_link_prop

                # 属性候補語(名詞)と思われる語句が含まれる文節の処理
                else:
                    n_term, _, n_pos, n_sub = link_prop_list[curr_idx+1].phrase_content
                    if n_pos != '名詞':
                        # print('\t\t[hit next]\t{}'.format(link_prop_list[curr_idx+1].phrase_content))
                        updated_link_prop = curr_link_prop

                    else:
                        # 助詞「の」における処理
                        if c_sub == 'の':
                            if n_term in self.stopwords:
                                # print('\t\t[hit in "の" @sp]\t{}'.format(curr_link_prop))
                                updated_link_prop = DependencyAnalyzer.LinkProp(
                                    curr_link_prop.chunk_id, DependencyAnalyzer.PhraseContent(c_term, c_pos, c_words, n_sub)
                                )

                            else:
                                # print('\t\t[hit in "の"]\t{}'.format(curr_link_prop))
                                updated_link_prop = curr_link_prop

                        # 助詞「と」「や」における処理
                        elif c_sub in self.PAEALLEL_PRESENTATION_WORDS:
                            # print('\t\t[hit in parallel]\t{}'.format(curr_link_prop))
                            updated_link_prop = DependencyAnalyzer.LinkProp(
                                curr_link_prop.chunk_id, DependencyAnalyzer.PhraseContent(c_term, c_pos, c_words, n_sub)
                            )
                            
                        # 例外
                        else:
                            # print('<例外発見>：{}'.format(curr_link_prop))
                            updated_link_prop = curr_link_prop

                updated_lp_list.append(updated_link_prop)

            
            updated_lp_list.append(link_prop_list[length])
            # print('\t[finish?]')
            if updated_lp_list == old_updated_list:
                break

            old_updated_list = updated_lp_list[:]


        # print('[before]')
        # pprint(link_prop_list)
        # print()
        # print('[after]')
        # pprint(updated_lp_list)
        # print()

        return updated_lp_list


    def _is_good_pp(self, sub: str) -> bool:
        return sub != 'の' and sub not in self.PAEALLEL_PRESENTATION_WORDS
            


    def _extract_cooccurrence(self, link_prop_list: list) -> str:
        cooccurrences = []
        for link_prop in link_prop_list:
            main_term, _, pos, _ = link_prop.phrase_content
            if pos in DependencyAnalyzer.REQUIREMENT_POS_LIST and main_term not in self.stopwords:
                cooccurrences.append(main_term)

        cooccurrence = self.WORD_SEPARATOR.join(sorted(set(cooccurrences), key=cooccurrences.index))
        return cooccurrence



    def _register_dictionary_field(self, dic_dir, category='common') -> list:
        category_dic_dir  = '{}\\{}'.format(dic_dir, category)
        category_dic_list = [
            self.DictionaryProp(os.path.splitext(os.path.basename(f))[0], os.path.abspath(f)) 
            for f in glob.glob('{}\\*.txt'.format(category_dic_dir))
        ]
        return category_dic_list


    def _search_dictionaries(self, dic_dir: str) -> list:
        common_dic_list   = self._register_dictionary_field(dic_dir)
        # print('<common_dic_list>')
        # pprint(common_dic_list)

        category_dic_list = self._register_dictionary_field(dic_dir, self.category)
        # print('<category_dic_list>')
        # pprint(category_dic_list)

        dic_list = category_dic_list + common_dic_list
        return dic_list 


    def _read_dictionary(self, dic_prop):
        dic_path = dic_prop.path
        with open(dic_path, mode='r', encoding=self.code) as fp:
            dic_data = [line.strip() for line in fp.readlines()]

        attr_name  = dic_data[0].replace('name:', '')
        attr_words = dic_data[1:]

        self._dic_dict[attr_name]  = dic_prop
        self._attr_dict[attr_name] = attr_words


    def _analyze(self, sentence: str) -> AnalysisResult:
        chunk_dict, token_dict, _ = self._analyzer.analyze(sentence)
        alloc_dict  = self._analyzer.allocate_token_for_chunk(chunk_dict, token_dict)
        phrase_dict = self._analyzer.extract_representation(chunk_dict, alloc_dict)
        link_dict   = self._analyzer.make_link_dict(chunk_dict, phrase_dict)

        return self.AnalysisResult(chunk_dict, token_dict, alloc_dict, phrase_dict, link_dict)


    @staticmethod
    def _link_to_flagment(link_list: list, chunk_dict: OrderedDict) -> str:
        flagment = ''.join(chunk_dict[link].phrase for link in link_list)
        return flagment




if __name__ == "__main__":
    
    import json

    from split_sentence import Splitter
    from normalize import normalize

    sp = Splitter()

    SENTENCE_PROP_FIELD = ['review_id', 'last_review_id', 'sentence_id', 'last_sentence_id', 'star', 'title', 'review', 'sentence', 'result']
    SentenceProp = namedtuple('SentenceProp', SENTENCE_PROP_FIELD)

    dic_dir = r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\doc\dictionary'

    file_dict = OrderedDict()
    file_dict['air_cleaner'] = [
        # for validation
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\air_cleaner\SHARP-KIREION-加湿空気清浄機-高濃度7000プラズマクラスター技術-KC-Y65-W\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\air_cleaner\カンキョー-TB-202-タービュランス空気清浄機\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\air_cleaner\シャープ-加湿空気清浄機-プラズマクラスター25000-13畳-空気清浄-KI-GS50-W\review.json',
        # for training
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\result\air_cleaner\アイリスオーヤマ-空気清浄機-人感センサー付き-スリムデザイン-KFN-700\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\result\air_cleaner\Levoit-タイマー付き-花粉・PM2-5対応-HEPAフィルター-LV-PUR131\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\result\air_cleaner\ダイキン-DAIKIN-加湿ストリーマ空気清浄機「うるおい光クリエール」-ビターブラウン-TCK70R-T\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\result\air_cleaner\ダイキン-DAIKIN-加湿空気清浄機「うるおい光クリエール」-ホワイト-ACK70M-W\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\result\air_cleaner\空気洗浄機「NAGOMI-なごみ-」-パールホワイト-RCW-04WH\review.json'
    ]
    file_dict['air_cleaner'] = [f for f in glob.glob(r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\2019_result\air_cleaner\**', recursive=True)
                                if os.path.isfile(f) and f.endswith('review.json')]

    file_dict['refrigerator'] = [
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\refrigerator\【メーカー5年保証】省エネ17リットル型小型冷蔵庫-Peltism-ペルチィズム-Dunewhite-ペルチェ冷蔵庫\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\refrigerator\シャープ-SHARP-118L-2ドア冷蔵庫（直冷式）シルバー系SHARP-SJ-H12Y-S\review.json'
    ]
    file_dict['refrigerator'] = [f for f in glob.glob(r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\2019_result\refrigerator\**', recursive=True)
                                 if os.path.isfile(f) and f.endswith('review.json')]


    file_dict['water_purifying_pot'] = [
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\water_purifying_pot\ブリタ-ナヴェリア-ホワイトメモ-カートリッジ-【日本仕様・日本正規品】\review.json',
        r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\validation\water_purifying_pot\三菱レイヨン・クリンスイ-ポット型浄水器-アルカリポット-クリンスイCP007-CP007-GR\review.json'
    ]
    file_dict['water_purifying_pot'] = [f for f in glob.glob(r'C:\Users\ms338\OneDrive\Documents\GitHub\ReviewResearch\2019_result\water_purifying_pot\**', recursive=True)
                                        if os.path.isfile(f) and f.endswith('review.json')]


    category = 'air_cleaner'
    category = 'refrigerator'
    category = 'water_purifying_pot'

    OPTION_FIELD = ['is_extended', 'is_ristrict']
    Option = namedtuple('Option', OPTION_FIELD)

    option_list = [
        Option(False, False), Option(False, True), Option(True, False), Option(True, True)
    ]
    
    # pprint(file_dict)
        
    extractor = AttributionExtractor(dic_dir, category)

    for json_file in tqdm(file_dict[category], ascii=True):
        for option in option_list:
            extention    = '_extended' if option.is_extended else ''
            restricition = '_ristrict' if option.is_ristrict else ''
            product_dir = os.path.dirname(json_file)

            extractor._extend = option.is_extended
            extractor._ristrict = option.is_ristrict


            out_file = '{}\\prediction{}{}.json'.format(product_dir, extention, restricition)
            
            review_data = json.load(open(json_file, mode='r', encoding='utf-8'), object_pairs_hook=OrderedDict)
            reviews = review_data['reviews']

            product_name = review_data['product']
            link = review_data['link']
            maker = review_data['maker']
            ave_star = review_data['average_stars']
            stars_dist = review_data['stars_distribution']


            total_review = len(reviews)
            
            last_review_id = total_review
            sentence_prop_list = []
            for idx, review_info in enumerate(reviews):
                star   = review_info['star']
                title  = review_info['title']
                review = review_info['review']
                # vote   = review_info['vote']
                review_id = idx + 1

                sentences = sp.split_sentence(normalize(review))
                last_sentence_id = len(sentences)
                for sidx, sentence in sentences.items():
                    sentence_id = sidx + 1

                    result_dict = extractor.extract_attrribution(sentence)
                    # pprint(result_dict)

                    editted_dict = OrderedDict()
                    for attr, flagment in result_dict.items():
                        editted_dict[extractor.dic_dict[attr].name] = flagment

                    sentence_prop_list.append(
                        SentenceProp(
                            review_id, last_review_id,
                            sentence_id, last_sentence_id,
                            star, title, review, sentence, editted_dict
                        )
                    )

            total_sentence = len(sentence_prop_list)

            out_data = OrderedDict()
            out_data['input_file'] = json_file
            out_data['product'] = product_name
            out_data['link'] = link
            out_data['maker'] = maker
            out_data['average_stars'] = ave_star
            out_data['star_distribuition'] = stars_dist
            out_data['total_review'] = total_review
            out_data['total_sentence'] = total_sentence
            out_data['sentences'] = [sentence_prop._asdict() for sentence_prop in sentence_prop_list]


            json.dump(out_data, open(out_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=4)


    print('categoty: {}'.format(category))
    # print('option:   {}'.format(option))
            

