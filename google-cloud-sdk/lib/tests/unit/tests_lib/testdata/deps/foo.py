# -*- coding: utf-8 -*- #
"""Foo."""

import bar
from submodule import b

if __name__ == '__main__':
  bar.do_something()  # imports baz
  bar.imported_baz().do_something()
  b.do_someting()
