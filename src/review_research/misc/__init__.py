import pathlib
import glob
import re
from typing import Iterable, Any, Sequence, Union, Optional, Tuple

def unique_sort_by_index(sequence: Sequence[Any]) -> Iterable[Any]:
  """重複をなくして出現順にソートする

  Args:
    sequence (Sequence[Any]): 複数の要素をもつオブジェクト

  Returns:
    与えられたiterableから重複をなくして出現順にソートしたもののリスト
  """
  yield from sorted(set(sequence), key=sequence.index)


def get_all_jsonfiles(
    dirpath: Union[str, pathlib.Path],
    name_pattern: Optional[str] = None) -> Tuple[pathlib.Path, ...]:
  """与えられたディレクトリ下の JSON ファイルを全て取り出す

  Args:
    dirpath (Union[str, pathlib.Path]): 指定するディレクトリ
    name_pattern (Optional[str]): ファイル名のパターン(指定しない場合は、全ての JSON ファイルを取り出す)

  Returns:
    dirpath 下の全ての JSON ファイル(name_pattern が指定されれば、当てはまるもの全ての JSON ファイル)
  """
  all_paths = tuple(
      pathlib.Path(f) 
      for f in glob.glob('{}/**'.format(dirpath), recursive=True)
  )
  all_jsonfiles = tuple(p for p in all_paths if p.suffix == '.json')
  if name_pattern:
    name_regex = re.compile(name_pattern)
    all_jsonfiles = tuple(p for p in all_jsonfiles if name_regex.match(p.name))

  return all_jsonfiles

  