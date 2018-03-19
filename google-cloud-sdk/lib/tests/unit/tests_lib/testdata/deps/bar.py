"""Bar."""

try:
  import unknown_module  # pylint: disable=g-import-not-at-top
except ImportError:
  pass

if __name__ == '__main__':
  unknown_module.do_something()
