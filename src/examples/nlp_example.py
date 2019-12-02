from pprint import pprint

from review_research.nlp import Splitter
from review_research.nlp import normalize
from review_research.nlp import Tokenizer
from review_research.nlp import DependencyAnalyzer

def main():
  sentence = ("テストケースは、 unittest.TestCase のサブクラスとして作成します。"
              "メソッド名が test で始まる三つのメソッドがテストです。"
              "テストランナーはこの命名規約によってテストを行うメソッドを検索します。"
              "これらのテスト内では、予定の結果が得られていることを確かめるために assertEqual() を、条件のチェックに assertTrue() や assertFalse() を、例外が発生する事を確認するために assertRaises() をそれぞれ呼び出しています。"
              "assert 文の代わりにこれらのメソッドを使用すると、テストランナーでテスト結果を集計してレポートを作成する事ができます。"
              "setUp() および tearDown() メソッドによって各テストメソッドの前後に実行する命令を実装することが出来ます。 "
              "詳細は テストコードの構成 を参照してください。\n"
              "最後のブロックは簡単なテストの実行方法を示しています。"
              "unittest.main() は、テストスクリプトのコマンドライン用インターフェースを提供します。")

  print('print sentence')
  print(sentence)
  print()

  print('normalize sentence')
  sentence = normalize(sentence)
  print(sentence)
  print()

  print('split sentence to texts')
  splitter = Splitter()
  texts = splitter.split_sentence(sentence)
  pprint(texts)
  print()

  text0 = texts[0]
  print('tokenize text#0')
  print(text0)
  tokenizer = Tokenizer()
  words = tokenizer.get_baseforms(text0)
  pprint(words)
  print()

  text1 = texts[1]
  print('analyze dependency of text#1')
  print(text1)
  analyzer = DependencyAnalyzer()
  result = analyzer.analyze(text1)
  print('print tree')
  print(result.tree)
  print('print chunk_dict')
  pprint(result.chunk_dict)
  print()
  print('print token_dict')
  pprint(result.token_dict)
  print()
  alloc_dict = analyzer.allocate_token_for_chunk(result.chunk_dict, 
                                                 result.token_dict)
  print('print alloc_dict')
  pprint(alloc_dict)
  print()
  repr_dict = analyzer.extract_representation(result.chunk_dict, alloc_dict)
  print('print repr_dict')
  pprint(repr_dict)
  print()
  link_dict = analyzer.make_link_dict(result.chunk_dict, repr_dict)
  print('print link_dict')
  pprint(link_dict)
  print()

if __name__ == "__main__":
  main()