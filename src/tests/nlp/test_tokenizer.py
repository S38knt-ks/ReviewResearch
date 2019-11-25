from pprint import pprint

from review_research.nlp import Splitter, Tokenizer


tokenizer = Tokenizer()
text = 'ユニットテストフレームワークは元々 JUnit に触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。'

def test_tokenizer1():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=False,
                                   remove_a_hiragana=False,
                                   pos_list=None)
  assert len(result) == 28

def test_tokenizer2():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=True, 
                                   remove_a_hiragana=False, 
                                   pos_list=None)
  assert len(result) == 23

def test_tokenizer3():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=False, 
                                   remove_a_hiragana=True, 
                                   pos_list=None)
  assert len(result) == 19

def test_tokenizer4():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=False, 
                                   remove_a_hiragana=False)
  assert len(result) == 14

def test_tokenizer5():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=True, 
                                   remove_a_hiragana=True, 
                                   pos_list=None)
  assert len(result) == 14

def test_tokenizer6():
  result = tokenizer.get_baseforms(text, 
                                   remove_stopwords=True, 
                                   remove_a_hiragana=True)
  assert len(result) == 10





if __name__ == "__main__":
  test_tokenizer1()