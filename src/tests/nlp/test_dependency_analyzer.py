from review_research.nlp import normalize
from review_research.nlp import DependencyAnalyzer

def test_dependency_analyzer():
  text = 'ユニットテストフレームワークは元々JUnitに触発されたもので、他の言語の主要なユニットテストフレームワークと同じような感じです。'
  text = normalize(text)
  da = DependencyAnalyzer()
  analysis_result = da.analyze(text)
  assert len(analysis_result.chunk_dict) == 11
  num_tokens = sum(chunkdetail.number_tokens 
                   for chunkdetail in analysis_result.chunk_dict.values())
  assert len(analysis_result.token_dict) == num_tokens