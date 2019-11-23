import ast
import re
import os
from pathlib import Path
from setuptools import setup, find_packages

VERSION_REGEX = re.compile(r'__version__\s+=\s+(?P<version>.*)')
current_file = Path(__file__).resolve()
INIT_FILE = current_file.parent / '__init__.py'
with INIT_FILE.open(mode='r', encoding='utf-8') as fp:
  match = VERSION_REGEX.search(fp.read())

PACKAGE_NAME = 'review_research'
version = str(ast.literal_eval(match.group('version')))

setup(# metadata
      name=PACKAGE_NAME,
      version=version,
      # options
      packages=[PACKAGE_NAME],
      include_package_data=True,
      zip_safe=False,
      python_requires='>=3.7',
      install_requires=[],
      extras_require={'dev': ['pytest>=3',
                              'coverage',
                              'tox'],},)