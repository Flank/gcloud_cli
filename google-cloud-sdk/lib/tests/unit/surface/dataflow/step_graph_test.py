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
"""Tests for step_graph."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.dataflow import exceptions
from googlecloudsdk.api_lib.dataflow import step_graph
from tests.lib import cli_test_base
from tests.lib import test_case


class StepGraphTest(cli_test_base.CliTestBase):

  def testSplitStep(self):
    self.assertEqual([''], step_graph._SplitStep(''))
    self.assertEqual(['Transform'], step_graph._SplitStep('Transform'))
    self.assertEqual(['Transform', 'Step'],
                     step_graph._SplitStep('Transform/Step'))
    self.assertEqual(['A', 'B', 'C'], step_graph._SplitStep('A/B/C'))

    self.assertEqual(['A', 'B(some/path)', 'C'],
                     step_graph._SplitStep('A/B(some/path)/C'))

  def testUnflattenStepsToClustersTwoLeaves(self):
    root = step_graph._UnflattenStepsToClusters(self._Steps(['Foo', 'Bar']))
    self.assertEqual(2, len(root.Children()))
    self.assertTrue(root.IsRoot())
    self.assertFalse(root.IsLeaf())
    self.assertFalse(root.IsSingleton())

    key1, cluster1 = root.Children()[0]
    key2, cluster2 = root.Children()[1]
    self.assertEqual('Bar', key1)
    self.assertTrue(cluster1.IsLeaf())
    self.assertFalse(cluster1.IsRoot())
    self.assertFalse(cluster1.IsSingleton())
    self.assertEqual('Foo', key2)
    self.assertTrue(cluster2.IsLeaf())
    self.assertFalse(cluster2.IsRoot())
    self.assertFalse(cluster2.IsSingleton())

  def testSplitStepAcuumulatesMismatched(self):
    user_name = 'bad/step)'
    self.assertEqual(['bad', ['step)', '/']], step_graph._SplitStep(user_name))

  def testUnsupportedGraphvizName(self):
    name = 'bad-name\\\\'
    with self.AssertRaisesExceptionMatches(
        exceptions.UnsupportedNameException,
        'Unsupported name for Graphviz ID escaping'):
      step_graph._EscapeGraphvizId(name)

  def testUnflattenStepsToClustersWithNesting(self):
    root = step_graph._UnflattenStepsToClusters(
        self._Steps(['A/B', 'A/C', 'D/E']))

    self.assertEqual(2, len(root.Children()))
    self.assertTrue(root.IsRoot())
    self.assertFalse(root.IsLeaf())
    self.assertFalse(root.IsSingleton())

    key_a, cluster_a = root.Children()[0]
    key_d, cluster_d = root.Children()[1]
    self.assertEqual('A', key_a)
    self.assertFalse(cluster_a.IsLeaf())
    self.assertFalse(cluster_a.IsRoot())

    self.assertFalse(cluster_a.IsSingleton())

    self.assertEqual(2, len(cluster_a.Children()))
    key_ab, cluster_ab = cluster_a.Children()[0]
    key_ac, cluster_ac = cluster_a.Children()[1]
    self.assertEqual('B', key_ab)
    self.assertEqual('A/B', cluster_ab.Name())
    self.assertEqual('B', cluster_ab.Name(relative_to=cluster_a))
    self.assertTrue(cluster_ab.IsLeaf())
    self.assertFalse(cluster_ab.IsRoot())
    self.assertFalse(cluster_ab.IsSingleton())

    self.assertEqual('C', key_ac)
    self.assertTrue(cluster_ac.IsLeaf())
    self.assertFalse(cluster_ac.IsRoot())
    self.assertFalse(cluster_ac.IsSingleton())

    self.assertEqual('D', key_d)
    self.assertFalse(cluster_d.IsLeaf())
    self.assertFalse(cluster_d.IsRoot())
    self.assertTrue(cluster_d.IsSingleton())
    self.assertEqual(1, len(cluster_d.Children()))

    key_de, cluster_de = cluster_d.Children()[0]

    self.assertEqual('E', key_de)
    self.assertTrue(cluster_de.IsLeaf())
    self.assertFalse(cluster_de.IsRoot())
    self.assertFalse(cluster_de.IsSingleton())

  def testGraphvizEdgesParallelInput(self):
    step = {
        'name': 'myStep',
        'properties': {
            'parallel_input': {
                'step_name': 's1',
                'output_name': 'out1',
            }
        }
    }

    result = self._GetEdges(step)
    self.assertIn(self._Edge('"s1"', '"myStep"', '"out1"', 'solid'), result)

  def testGraphvizEdgesSideInputs(self):
    step = {
        'name': 'myStep',
        'properties': {
            'non_parallel_inputs': {
                'side1': {
                    'step_name': 's"2"',
                    'output_name': 'out2',
                },
                'side2': {
                    'step_name': 's3',
                    'output_name': 'out3',
                }
            },
        }
    }

    result = self._GetEdges(step)
    self.assertIn(
        self._Edge('"s\\"2\\""', '"myStep"', '"out2"', 'dashed'), result)
    self.assertIn(self._Edge('"s3"', '"myStep"', '"out3"', 'dashed'), result)

  def testGraphvizEdgesInputs(self):
    step = {
        'name': 'myStep',
        'properties': {
            'inputs': [
                {
                    'step_name': 's2',
                    'output_name': 'out2',
                },
                {
                    'step_name': 's3',
                    'output_name': 'out3',
                }
            ],
        }
    }

    result = self._GetEdges(step)
    self.assertIn(self._Edge('"s2"', '"myStep"', '"out2"', 'solid'), result)
    self.assertIn(self._Edge('"s3"', '"myStep"', '"out3"', 'solid'), result)

  def testOutputGraphvizClustersSimple(self):
    self.assertEqual("""\
"s0" [label="A", tooltip="A", style=filled, fillcolor=white];
"s1" [label="B", tooltip="B", style=filled, fillcolor=white];
"s2" [label="C", tooltip="C", style=filled, fillcolor=white];
""", self._GetNodes(['A', 'B', 'C']))

  def testOutputGraphvizClustersNesting(self):
    self.assertEqual("""\
subgraph "cluster A" {
style=filled;
bgcolor=white;
labeljust=left;
tooltip="A";
label="A";
"s0" [label="B", tooltip="A/B", style=filled, fillcolor=white];
"s1" [label="C", tooltip="A/C", style=filled, fillcolor=white];
}
"s2" [label="D/E", tooltip="D/E", style=filled, fillcolor=white];
""", self._GetNodes(['A/B', 'A/C', 'D/E']))

  def _GetEdges(self, step):
    return list(step_graph._YieldGraphvizEdges(step))

  def _GetNodes(self, user_names):
    root = step_graph._UnflattenStepsToClusters(self._Steps(user_names))
    return '\n'.join(step_graph._YieldGraphvizClusters(root)) + '\n'

  def _Edge(self, edge_source, edge_dest, edge_output, style):
    return step_graph._EDGE_FORMAT.format(
        edge_source=edge_source,
        edge_dest=edge_dest,
        edge_output=edge_output,
        style=style)

  def _Steps(self, user_names):
    return [{'name': 's{0}'.format(idx), 'properties': {'user_name': user_name}}
            for idx, user_name in enumerate(user_names)]


if __name__ == '__main__':
  test_case.main()
