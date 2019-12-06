from review_research.nlp import Splitter

def test_split1():
  splitter = Splitter()
  text1 = '''ユニットテストフレームワークは元々 JUnit に触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。
  テストの自動化、テスト用のセットアップやシャットダウンのコードの共有、テストのコレクション化、そして報告フレームワークからのテストの独立性をサポートしています。'''
  result = splitter.split_sentence(text1)
  assert len(result) == 2

def test_split2():
  splitter = Splitter()
  text2 = '''ユニットテストフレームワークは元々 JUnit に触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。。。。。
  テストの自動化、テスト用のセットアップやシャットダウンのコードの共有、テストのコレクション化、そして報告フレームワークからのテストの独立性をサポートしています。。。。。。'''
  result = splitter.split_sentence(text2)
  assert len(result) == 2

def test_split3():
  splitter = Splitter()
  text3 = '''テストケースは、 unittest.TestCase のサブクラスとして作成します。メソッド名が test で始まる三つのメソッドがテストです。テストランナーはこの命名規約によってテストを行うメソッドを検索します。
  これらのテスト内では、予定の結果が得られていることを確かめるために assertEqual() を、条件のチェックに assertTrue() や assertFalse() を、例外が発生する事を確認するために assertRaises() をそれぞれ呼び出しています。 assert 文の代わりにこれらのメソッドを使用すると、テストランナーでテスト結果を集計してレポートを作成する事ができます。
  setUp() および tearDown() メソッドによって各テストメソッドの前後に実行する命令を実装することが出来ます。 詳細は テストコードの構成 を参照してください。
  最後のブロックは簡単なテストの実行方法を示しています。 unittest.main() は、テストスクリプトのコマンドライン用インターフェースを提供します。'''
  result = splitter.split_sentence(text3)
  assert len(result) == 9


