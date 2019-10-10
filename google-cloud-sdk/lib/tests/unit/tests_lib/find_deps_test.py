# -*- coding: utf-8 -*-
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Tests for script finding dependencies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from tests.lib import find_deps
from tests.lib import sdk_test_base
from tests.lib import with_deps_capture
from modulegraph import modulegraph


class FindDepsTest(sdk_test_base.SdkBase):
  """Tests for script finding dependencies."""

  def SetUp(self):
    root = self.Resource('tests', 'unit', 'tests_lib', 'testdata', 'deps')

    class _PathHelperMock(object):

      googlecloudsdk_root = root
      googlecloudsdk_tests_root = root

      @classmethod
      def ModuleByPath(cls, path):
        return with_deps_capture.ModuleByPath(path, cls.googlecloudsdk_root)

      @staticmethod
      def ModuleBySurfacePath(surface_path):
        return surface_path

    self.StartObjectPatch(find_deps, '_PathHelper', new=_PathHelperMock)
    self.StartObjectPatch(sys, 'path', new=[root])

    self._graph = find_deps.GetGraph()

  def testGraph(self):
    outgoing = self._graph.graph.describe_node('foo')[2]
    self.assertEqual(
        ['bar', 'baz', 'submodule', 'submodule.b'],
        sorted(
            [self._graph.graph.edge_by_id(e)[1] for e in outgoing]))

    _, data, _, incoming = self._graph.graph.describe_node('unknown_module')
    self.assertIsInstance(data, modulegraph.BadModule)
    self.assertEqual(
        ['bar'],
        sorted(
            [self._graph.graph.edge_by_id(e)[0] for e in incoming]))

    outgoing, incoming = self._graph.graph.describe_node('submodule')[2:]
    self.assertEqual(
        ['submodule.c'],
        sorted(
            [self._graph.graph.edge_by_id(e)[1] for e in outgoing]))
    self.assertEqual(
        ['foo', 'submodule.a', 'submodule.b', 'submodule.c'],
        sorted(
            [self._graph.graph.edge_by_id(e)[0] for e in incoming]))

  def testBfs(self):
    self.StartObjectPatch(os.path, 'join', return_value='')

    modules_to_run = find_deps.RunBfs(self._graph, ['bar'])
    self.assertEqual(modules_to_run, ['bar', 'foo'])

    modules_to_run = find_deps.RunBfs(self._graph, ['baz'])
    self.assertEqual(modules_to_run, ['baz', 'foo'])

    modules_to_run = find_deps.RunBfs(self._graph, ['foo'])
    self.assertEqual(modules_to_run, ['foo'])


if __name__ == '__main__':
  sdk_test_base.main()
