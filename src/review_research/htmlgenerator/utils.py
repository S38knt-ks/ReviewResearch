import pathlib
from typing import Tuple, Any, List, Dict, Optional, Union

def tag(name: str, *content: Tuple[Any, ...], 
        class_: Optional[str] = None, **attrs: Dict[str, str]) -> str:
  """html タグの生成

  Args:
    name (str): html タグ名
    *content (Tuple[Any, ...]): タグで囲まれる要素
    class_ (Optional[str]): class 属性の値
    **attrs (Dict[str, str]): 属性名と属性の値の辞書

  Returns:
    作成された html タグ
  """
  if class_:
    attrs['class'] = class_

  if attrs:
    attr_str = ''.join(' {}="{}"'.format(attr, value) 
                       for attr, value in sorted(attrs.items()))
  else:
    attr_str = ''

  if content:
    return '\n'.join('<{}{}>{}</{}>'.format(name, attr_str, c, name)
                     for c in content)

  else:
    return '<{}{}>'.format(name, attr_str)


def organize_contents(content_list: List[str], 
                      tag_name: str, **attrs: Dict[str, str]) -> str:
  """html タグで与えられた要素列を囲む

  Args:
    content_list (List[str]): tag_name で囲みたい要素リスト
    tag_name (str): html タグ
    **attrs (Dict[str, str]): tag_name に関する属性名と属性の値の辞書

  Returns:
    tag_name タグで囲まれた html タグ
  """
  content = '\n'.join(content_list)
  return tag(tag_name, content, **attrs)

def read_script(scriptfile: Union[str, pathlib.Path],
                old_and_new: Optional[Tuple[str, str]] = None) -> str:
  """html に埋め込む script ファイルを読み込み、その中身を返す

  Args:
    scriptfile (Union[str, pathlib.Path]): html に埋め込みたい script ファイル
    old_and_new (Optional[Tuple[str, str]]): 置換文字列のペア(old を new に置換)

  Returns:
    scriptfile の中身
  """
  scriptfile = pathlib.Path(scriptfile)
  with scriptfile.open('r', encoding='utf-8') as fp:
    script = fp.read()

  if old_and_new:
    old, new = old_and_new
    return script.replace(old, new)

  else:
    return script