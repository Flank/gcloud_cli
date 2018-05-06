# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A pytest plugin to implement several command line options.

Note that pytest plugin hook names, including argument names, are fixed by the
pytest specification.

Adds the options:
  --module-prefixes: Includes only tests that match one of the given prefixes
  --exclude-module-prefixes: Excludes tests that match the given prefixes
  --no-unit-tests: Excludes all unit tests (those in tests.unit)
  --no-integration-tests: Excludes e2e tests (those in tests.e2e)
  --random: Shuffle tests before running
  --no-random: Disable randomization
  --random-seed: Specify a random seed for test shuffling
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os
import random
import sys
import time


from py._path import local
import pytest
import six
from six.moves import range  # pylint: disable=redefined-builtin


def pytest_addoption(parser):
  """Adds command line options for this plugin to pytest."""
  parser.addoption(
      '--module-prefixes', '--module_prefixes',
      dest='included', nargs='*', action='append')
  parser.addoption(
      '--exclude-module-prefixes', '--exclude_module_prefixes',
      dest='excluded', nargs='*', action='append')
  # TODO(b/36057256): Reevaluate the no-...-tests flags. They might be removed
  # or reworked depending on how useful people find them.
  parser.addoption(
      '--no-integration-tests', dest='no_integration', action='store_true')
  parser.addoption('--no-unit-tests', dest='no_unit', action='store_true')
  parser.addoption('--random', dest='random', action='store_true')
  parser.addoption('--no-random', dest='random', action='store_false')
  parser.addoption('--random-seed', dest='random_seed', type=int)


def _test_module_path_matches_prefix(test_module_path, prefixes, can_match):
  """Tests whether a path is a prefix of something in the prefixes list.

  If can_match is true, this also checks whether something in prefixes is a
  prefix of the given path.

  Args:
    test_module_path: string, the path to test
    prefixes: list, strings to test the path against
    can_match: boolean, whether or not to check in both directions

  Returns:
    bool, Whether or not this path matches one of the given prefixes
  """
  # When running pyttest from $INSTALL_DIR in a private repo with
  # --module-prefixes some test_module_path values were prefixed with
  # google-cloud-sdk.lib.tests. and caused this method to not match prefixes
  # it should have.
  for skip_prefix in ('google-cloud-sdk.', 'lib.', 'tests.'):
    if test_module_path.startswith(skip_prefix):
      test_module_path = test_module_path[len(skip_prefix):]
  if test_module_path.endswith('.py'):
    test_module_path = test_module_path[:-3]
  for prefix in prefixes:
    if (test_module_path.startswith(prefix) or
        (can_match and prefix.startswith(test_module_path))):
      return True
  return False


def _test_module_path_ok(test_module_path, included, excluded):
  """Test if path matches at least one inclusion and no exclusions."""
  in_test = (not included or _test_module_path_matches_prefix(
      test_module_path, included, can_match=True))
  ex_test = (not excluded or not _test_module_path_matches_prefix(
      test_module_path, excluded, can_match=False))
  return in_test and ex_test


def _remove_overlaps(paths):
  """Remove extraneous paths from the list.

  Given a paths list like [unit, unit.core, unit.surface], we want to only run
  the tests in unit.core and unit.surface, but the inclusion-exclusion filter
  would normally run all tests in unit instead. (It's assumed that users
  generally wouldn't enter such a list manually, but might accidentally because
  of the paths added by the automated tools.) This removes any paths that are
  prefixes of other paths in the list.

  Args:
    paths: list, a list of paths to filter

  Returns:
    A list of paths with the overlapping paths removed
  """
  if not paths:
    return []
  paths = sorted(paths)
  results = []
  for i in range(len(paths) - 1):
    if not _contains(paths[i], paths[i+1]):
      results.append(paths[i])
  results.append(paths[-1])
  return results


def _contains(first_path, second_path):
  return (first_path == second_path or second_path.startswith(first_path)
          and second_path[len(first_path)] == '.')


def _flatten_once(lists):
  result = []
  for lst in lists:
    result.extend(lst)
  return result


def _get_root_dir():
  # This file lives in the tests/lib/ folder. The rootdir for all tests should
  # be tests/ regardless of where pytest was run from.
  if six.PY2:
    return local.LocalPath(
        os.path.dirname(
            __file__.decode(sys.getfilesystemencoding() or
                            sys.getdefaultencoding()))).join('..')
  return local.LocalPath(os.path.dirname(__file__)).join('..')


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
  """One time global configuration. Set root dir and prepare prefix lists."""
  # Set the root directory for reporting purposes
  config.rootdir = _get_root_dir()

  # The command line lists are nested, so flatten them out first
  included_prefixes = _flatten_once(config.getoption('included') or [[]])
  excluded_prefixes = _flatten_once(config.getoption('excluded') or [[]])

  # Add unit and e2e exclusions if needed
  if config.getoption('no_unit'):
    excluded_prefixes.append('unit')
  if config.getoption('no_integration'):
    excluded_prefixes.append('e2e')

  # Filter out overlapping inclusions (e.g. unit from [unit, unit.surface])
  included_prefixes = _remove_overlaps(included_prefixes)

  # Store the lists back in config so they'll be accessible
  config.option.included_prefixes = included_prefixes
  config.option.excluded_prefixes = excluded_prefixes


def pytest_ignore_collect(path, config):
  """Return True if path should be skipped.

  pytest passes in each directory one at a time. If True is returned for that
  directory, none of the subdirectories under it are checked at all.

  Args:
    path: The full, absolute path under consideration
    config: A pytest Config with the command line arguments and other info

  Returns:
    A boolean indicating whether or not to ignore this path and all subpaths
  """
  # Trim the path at the tests directory
  sep = '.tests.'
  test_module_path = path.strpath.replace(os.path.sep, '.')
  pos = test_module_path.find(sep)
  test_module_path = test_module_path[pos + len(sep):]

  # Get the inclusions and exclusions from the config
  included_prefixes = config.getoption('included_prefixes')
  excluded_prefixes = config.getoption('excluded_prefixes')

  # Return True to ignore this path and all subpaths
  return not _test_module_path_ok(
      test_module_path, included_prefixes, excluded_prefixes)


def _nodeid_to_module_path(nodeid):
  module_path = nodeid.replace('.py::', '.')
  module_path = module_path.replace('::', '.')
  # nodeid's already replace all path separators by '/'
  module_path = module_path.replace('/', '.')
  return module_path


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
  """Hook to modify collected items list."""
  # Filter tests with module prefixes. pytest_ignore_collect filters test paths
  # and just uses a keep-this-or-not return value. There's no function like that
  # for individual tests, but here we can take the full list of tests and cut it
  # down to only what we're interested in. (We could do all the filtering here,
  # but it's a lot faster to prune by directories first.)
  included_prefixes = config.getoption('included_prefixes')
  excluded_prefixes = config.getoption('excluded_prefixes')

  remaining = []
  for item in items:
    module_path = _nodeid_to_module_path(item.nodeid)
    if _test_module_path_ok(
        module_path, included_prefixes, excluded_prefixes):
      remaining.append(item)
  items[:] = remaining

  # Randomize test order
  if config.getoption('random'):
    rnd = random.Random()
    seed = config.getoption('random_seed')
    if not seed:
      seed = int(time.time() * 1000)
    if _is_master_slave(config):
      sys.stderr.write('Using random seed: {0}\n'.format(seed))
    rnd.seed(seed)

    # Standard Fisher-Yates shuffle
    for i in range(len(items) - 1, -1, -1):
      n = rnd.randint(0, i)
      item = items.pop(n)
      items.append(item)


def _is_master_slave(config):
  if hasattr(config, 'slaveinput'):
    return config.slaveinput.get('slaveid') == 'gw0'
  return True
