from review_research.nlp import TextAlignment

ta1 = TextAlignment()
ta2 = TextAlignment()

def test_text_alignment1():
  text = 'ユニットテストフレームワークは元々 JUnit に触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。'
  ta1.align(text)
  assert ta1.text == text
  assert len(ta1.words) == len([a for a in ta1.alignment if a.is_word])


def test_text_alignment2():
  text = 'ユニットテストフレームワークは元々 JUnit に触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。。。。。'
  ta2(text)
  assert ta2.text != text
  assert ta2.text == ta1.text
  assert len(ta1.alignment) == len(ta2.alignment)
