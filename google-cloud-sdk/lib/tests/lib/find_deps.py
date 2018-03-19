# Copyright 2017 Google Inc. All Rights Reserved.
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

"""A script listing which tests to run given list of changed files as input."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import itertools
import json
import logging
import os
import sys


this_dir = os.path.dirname(__file__)  # .../lib/tests/lib
tests_dir = os.path.abspath(os.path.join(this_dir, '..'))  # .../lib/tests
lib_dir = os.path.abspath(os.path.join(tests_dir, '..'))  # .../lib
third_party_dir = os.path.abspath(os.path.join(lib_dir, 'third_party'))
bin_dir = os.path.abspath(os.path.join(lib_dir, '..', 'bin'))  # .../bin
# This is only applicable on Windows, but it doesn't hurt anything elsewhere
python_dir = os.path.abspath(os.path.join(
    lib_dir, '..', 'platform', 'bundledpython'))

os.environ['PATH'] = os.pathsep.join([python_dir, bin_dir, os.environ['PATH']])

# Remove the dist-packages folders and add our library folders
sys.path[:] = [pp for pp in sys.path if 'dist-packages' not in pp]
sys.path[0:0] = [python_dir, lib_dir, third_party_dir]


import googlecloudsdk  # pylint: disable=g-import-not-at-top
from googlecloudsdk.core import yaml
import tests
from tests.lib import with_deps_capture
from modulegraph import modulegraph  # pylint: disable=g-import-not-at-top


DEPOT_PREFIX = 'depot_path: '
DEPOT_PREFIX_LEN = len(DEPOT_PREFIX)
FILE_PREFIX = 'third_party.py.'
FILE_PREFIX_LEN = len(FILE_PREFIX)
GOOGLECLOUDSDK = 'googlecloudsdk'
GOOGLECLOUDSDK_LEN = len(GOOGLECLOUDSDK)
TESTS_PREFIX = 'tests.'
TESTS_PREFIX_LEN = len(TESTS_PREFIX)
THIRD_PARTY_PREFIX = 'third_party.cloudsdk.external.'
THIRD_PARTY_PREFIX_LEN = len(THIRD_PARTY_PREFIX)


class Error(Exception):
  """A class used for all exceptions raised in this script."""
  pass


class _PathHelper(object):
  """A helper class for path-to-module conversion."""

  googlecloudsdk_root = None
  googlecloudsdk_preroot = None
  googlecloudsdk_tests_root = None

  @classmethod
  def SetRoot(cls, googlecloudsdk_root, googlecloudsdk_tests_root):
    cls.googlecloudsdk_root = googlecloudsdk_root
    cls.googlecloudsdk_preroot = os.path.dirname(googlecloudsdk_root)
    cls.googlecloudsdk_tests_root = googlecloudsdk_tests_root

  @classmethod
  def ModuleByPath(cls, path):
    """Return module to import by path."""
    if 'testdata' in path or 'test_data' in path:
      raise Error(
          'Test data file {} may refer to multiple modules'.format(path))
    res = with_deps_capture.ModuleByPath(path, cls.googlecloudsdk_preroot)
    idx = res.rfind(TESTS_PREFIX)
    if idx != -1:
      return res[idx:]
    idx = res.rfind(GOOGLECLOUDSDK)
    if idx != -1:
      return res[idx:]
    raise Error('Problem getting module from path {}'.format(path))

  @staticmethod
  def ModuleBySurfacePath(surface_path):
    return with_deps_capture.GOOGLECLOUDSDK_PREFIX + surface_path


_PathHelper.SetRoot(os.path.dirname(googlecloudsdk.__file__),
                    os.path.dirname(tests.__file__))


def _ImportPath(graph, root, f):
  if f.endswith('.deps'):
    path = f[:-len('.deps')] + '.py'
  elif f.endswith('.py'):
    path = f
  else:
    return
  path = os.path.join(root, path)
  try:
    mod = _PathHelper.ModuleByPath(path)
  except Error as e:
    logging.warning('Error in path: %s', e.message)
  else:
    if not graph.findNode(mod):
      graph.import_hook(mod)
    if f.endswith('.deps'):
      deps = yaml.load_path(os.path.join(root, f))
      for dep in deps:
        dep_module = _PathHelper.ModuleBySurfacePath(dep)
        if not graph.findNode(dep_module):
          graph.import_hook(dep_module)
        if not graph.graph.edge_by_node(mod, dep_module):
          graph.graph.add_edge(mod, dep_module)


def GetGraph():
  """Build the graph object."""
  python_path = sys.path[:]

  graph = modulegraph.ModuleGraph(python_path)
  for root, unused_dirs, files in itertools.chain(
      os.walk(_PathHelper.googlecloudsdk_root),
      os.walk(_PathHelper.googlecloudsdk_tests_root)):
    for f in files:
      _ImportPath(graph, root, f)
  return graph


def RunBfs(graph, changed_modules):
  """Run BFS to determine which e2e tests to run.

  Args:
    graph: ModuleGraph, The graph of module dependencies.
    changed_modules: list, The modules to start BFS from.

  Returns:
    list, Tests affected.
  """
  e2e_tests_pattern = os.path.join('tests', 'e2e')

  used = set(changed_modules)
  tests_to_run = []

  # All imported through import_hook modules directly depend on it
  used.add(graph)

  while changed_modules:
    try:
      current_node, data, unused_outgoing, incoming = graph.graph.describe_node(
          changed_modules.pop(0))
    except KeyError:
      # TODO(b/65551481): raise Error('Can\'t find node: {}'.format(e.message))
      continue
    if isinstance(data, modulegraph.BadModule):
      logging.warning('Module %s not imported: %s', current_node, data)
      continue
    if e2e_tests_pattern in os.path.realpath(data.filename):
      tests_to_run.append(data.graphident)
    for edge_id in incoming:
      node = graph.graph.edge_by_id(edge_id)[0]
      if node not in used:
        used.add(node)
        changed_modules.append(node)

  return sorted(tests_to_run)


def GetChangedFiles():
  with open(os.environ.get('PRESUBMIT_FILE')) as f:
    lines = f.readlines()

  for line in lines:
    line = line.strip()
    if line.startswith(DEPOT_PREFIX):
      line = line[DEPOT_PREFIX_LEN:]
      yield line


def main():
  graph = GetGraph()

  changed_files = list(GetChangedFiles())
  try:
    changed_modules = [_PathHelper.ModuleByPath(p) for p in changed_files]
  except Error:
    # TODO(b/65551481): run all tests: print '[]' and return
    changed_modules = []
    for p in changed_files:
      try:
        changed_modules.append(_PathHelper.ModuleByPath(os.path.realpath(p)))
      except Error:
        sys.__stderr__.write('FAIL ON ' +  p + '\n')

  tests_to_run = RunBfs(graph, changed_modules)
  print(json.dumps(tests_to_run))


if __name__ == '__main__':
  main()
