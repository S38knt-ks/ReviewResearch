from collections import OrderedDict
from normalize import normalize
from tokenizer import Tokenizer
from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary

class TopicModel:

    def __init__(self):
        self._tokenizer = Tokenizer()


    def allot_topics(self, topic_num: int, review_dict_list: list) -> OrderedDict:
        corpus, dictionary = self._make_property(review_dict_list)

        lda = LdaModel(corpus=corpus, num_topics=topic_num, id2word=dictionary)
        
        word_dict = OrderedDict()
        for topic_id in range(topic_num):
            word_dict[topic_id] = lda.show_topic(topic_id)

        return word_dict



    def _make_property(self, review_dict_list: list) -> tuple:
        """
        review_dict's keys are 'date', 'star', 'vote', 'name', 'title' and 'review' 
        """
        reviews = OrderedDict()
        for idx, review_dict in enumerate(review_dict_list):
            review = normalize(review_dict['review'])
            reviews[idx] = review

        text_list = [
            [term.word for term in self._tokenizer.get_baseforms(review)]
            for review in reviews.values()
        ]

        dictionary = Dictionary(text_list)
        dictionary.filter_extremes(no_below=1, no_above=0.6)
        corpus = [dictionary.doc2bow(words) for words in text_list]

        return corpus, dictionary