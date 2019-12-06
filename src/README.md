# review_research

Python3 で実装された研究用パッケージ

## Requirement

Python3.7+ (32bit)

- MeCab (32bit)
- CaboCha
- Beautiful Soup (bs4)
- NumPy
- Pandas

## Installation

前準備として以下のコマンドを実行すること

```cmd
pip install -U pip setuptools
```

`review_research` ディレクトリにて以下を実行するとインストールできる

```cmd
pip install .
```

### For developper

`review_research` ディレクトリにて以下を実行

```cmd
pip install -e '.[dev]'
```

Windows であれば PowerShell で実行すると良い