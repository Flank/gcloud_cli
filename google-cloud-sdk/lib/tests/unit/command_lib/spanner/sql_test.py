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
"""Tests for Spanner sql command lib."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py import extra_types
from googlecloudsdk.command_lib.spanner.sql import DisplayQueryAggregateStats
from googlecloudsdk.command_lib.spanner.sql import DisplayQueryPlan
from googlecloudsdk.command_lib.spanner.sql import DisplayQueryResults
from googlecloudsdk.command_lib.spanner.sql import Node
from googlecloudsdk.command_lib.spanner.sql import QueryHasAggregateStats
from googlecloudsdk.core import log
from tests.lib.surface.spanner import base
import six


class SqlTest(base.SpannerTestBase):
  """Cloud Spanner sql command lib tests."""

  def SetUp(self):
    self.out = log.out

  def _GivenNodeWithChildren(self, children, display_name='Serialize result'):
    """Creates a Node with the specified children.

    Args:
      children: A list of Nodes to make the children of the new Node.
      display_name: The name of the Node to be displayed.

    Returns:
      A Node with the provided children.
    """
    child_links = [
        self.msgs.ChildLink(childIndex=c + 1) for c, _ in enumerate(children)
    ]
    properties = self.msgs.PlanNode(
        kind=self.msgs.PlanNode.KindValueValuesEnum('RELATIONAL'),
        displayName=display_name,
        childLinks=child_links)
    return Node(properties, children)

  def _GivenMetadata(self, metadata):
    """Creates a metadata object from given data.

    Args:
      metadata: A dict of key, value pairs for additional properties on a Node.
        Can be None.

    Returns:
      A spanner_v1_messages.PlanNode.MetadataValue object.
    """
    if not metadata:
      return None

    additional_properties = []
    for key, val in metadata.items():
      additional_property = self.msgs.PlanNode.MetadataValue.AdditionalProperty(
          key=key, value=extra_types.JsonValue(string_value=val))
      additional_properties.append(additional_property)

    return self.msgs.PlanNode.MetadataValue(
        additionalProperties=additional_properties)

  def _GivenNestedStatProperties(self, outer_key, prop_dict):
    """Creates an additional property for each value in a given dict.

    Args:
      outer_key: The string name of the outermost key.
      prop_dict: A dictionary where the keys and values are strings.

    Returns:
      A spanner_v1_messages.PlanNode.ExecutionStatsValue.AdditionalProperty
      object, where the outermost values have type extra_types.JsonObject.
      Returns None if prop_dict doesn't exist.
    """
    if not prop_dict:
      return None

    props = []
    for k, v in six.iteritems(prop_dict):
      prop = extra_types.JsonObject.Property(
          key=k, value=extra_types.JsonValue(string_value=v))
      props.append(prop)

    return self.msgs.PlanNode.ExecutionStatsValue.AdditionalProperty(
        key=outer_key,
        value=extra_types.JsonValue(object_value=extra_types.JsonObject(
            properties=props)))

  def _GivenExecutionStats(self, execution_stats=None):
    """Creates an execution stats object from the given data.

    Args:
      execution_stats: A dict of key, value pairs where the values can be
        dictionaries themselves. The top-level keys can be 'execution_summary'
        or 'latency'. The whole object can be None.

    Returns:
      A spanner_v1_messages.PlanNode.ExecutionStatsValue object, or None if
      execution_stats doesn't exist..
    """
    if not execution_stats:
      return None

    summary = self._GivenNestedStatProperties(
        'execution_summary', execution_stats.get('execution_summary'))
    latency = self._GivenNestedStatProperties('latency',
                                              execution_stats.get('latency'))
    additional_properties = []
    if summary is not None:
      additional_properties.append(summary)
    if latency is not None:
      additional_properties.append(latency)
    return self.msgs.PlanNode.ExecutionStatsValue(
        additionalProperties=additional_properties)

  def _GivenLeafNode(self,
                     display_name='Constant',
                     description='NULL',
                     metadata=None,
                     execution_stats=None):
    """Creates a Node with no children.

    Args:
      display_name: The name of the Node to be displayed.
      description: A short summary of what the node does. Usually only exists
        on scalar nodes.
      metadata: A dict of key, value pairs for additional properties on a Node.
        Can be None.
      execution_stats: A dict of key, value pairs where the values can be
        dictionaries themselves. The top-level keys can be 'execution_summary'
        or 'latency'. The whole object can be None.

    Returns:
      A Node with no children.
    """
    leaf_props = self.msgs.PlanNode(
        kind=self.msgs.PlanNode.KindValueValuesEnum('SCALAR'),
        displayName=display_name,
        shortRepresentation=self.msgs.ShortRepresentation(
            description=description),
        metadata=self._GivenMetadata(metadata),
        executionStats=self._GivenExecutionStats(execution_stats),
        index=1)
    # A leaf has no children.
    leaf_children = []
    return Node(leaf_props, leaf_children)

  def _GivenResultsWithQueryStats(self, first_key_name='elapsed_time'):
    """Creates a result set with query statistics.

    Args:
      first_key_name: The name of the first additional property to display.

    Returns:
      A spanner_v1_messages.ResultSet object.
    """
    query_stats = self.msgs.ResultSetStats.QueryStatsValue(
        additionalProperties=[
            self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                key=first_key_name,
                value=extra_types.JsonValue(string_value='1.7 msecs')),
            self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                key='cpu_time',
                value=extra_types.JsonValue(string_value='.3 msecs')),
            self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                key='rows_returned',
                value=extra_types.JsonValue(string_value='9')),
            self.msgs.ResultSetStats.QueryStatsValue.AdditionalProperty(
                key='rows_scanned',
                value=extra_types.JsonValue(string_value='2000'))
        ])
    result_stats = self.msgs.ResultSetStats(
        queryPlan=self.msgs.QueryPlan(planNodes=[]), queryStats=query_stats)
    return self.msgs.ResultSet(stats=result_stats)

  def _GivenResultSetStats(self):
    """Creates query statistics of type spanner_v1_messages.ResultSetStats."""
    result_set_stats = self.msgs.ResultSetStats(queryPlan=self.msgs.QueryPlan(
        planNodes=[
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('RELATIONAL'),
                displayName='Serialize Result',
                childLinks=[
                    self.msgs.ChildLink(childIndex=1),
                    self.msgs.ChildLink(childIndex=3)
                ]),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('RELATIONAL'),
                displayName='Enumerate Rows',
                childLinks=[
                    self.msgs.ChildLink(childIndex=2),
                    self.msgs.ChildLink(childIndex=3)
                ],
                index=1),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('SCALAR'),
                displayName='Constant',
                shortRepresentation=self.msgs.ShortRepresentation(
                    description='<null>'),
                index=2),
            self.msgs.PlanNode(
                kind=self.msgs.PlanNode.KindValueValuesEnum('SCALAR'),
                displayName='Constant',
                shortRepresentation=self.msgs.ShortRepresentation(
                    description='1'),
                index=3)
        ]))
    return self.msgs.ResultSet(stats=result_set_stats)

  def _AssertOutputEqualsStripNewlines(self, output):
    self.AssertOutputEquals(output, normalize_space='\n')

  def testKindAndName(self):
    root = self._GivenLeafNode('Leaf')
    root.PrettyPrint(self.out)
    self.AssertOutputContains(' SCALAR Leaf\n NULL')

  def testChildIndentation(self):
    # Given a root node with a child.
    child = self._GivenLeafNode('Child')
    root = self._GivenNodeWithChildren([child])

    root.PrettyPrint(self.out)
    output = r""" RELATIONAL Serialize result
    |
    \- SCALAR Child
       NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testStubType(self):
    # Given a root node with 2 children.
    child_a = self._GivenLeafNode('ChildA')
    child_b = self._GivenLeafNode('ChildB')
    root = self._GivenNodeWithChildren([child_a, child_b])

    root.PrettyPrint(self.out)
    output = r""" RELATIONAL Serialize result
    |
    +- SCALAR ChildA
    |  NULL
    |
    \- SCALAR ChildB
       NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testConnectionBetweenChildren(self):
    # Given a root with two children that don't sit directly on top of each
    # other because one of the children has a child of its own.
    child_a_scalar = self._GivenLeafNode('ChildAScalar')
    child_a = self._GivenNodeWithChildren([child_a_scalar], 'ChildA')
    child_b = self._GivenLeafNode('ChildB')
    root = self._GivenNodeWithChildren([child_a, child_b])

    root.PrettyPrint(self.out)
    # Then the two children of the root are visually connected via a vertical
    # line.
    output = r""" RELATIONAL Serialize result
    |
    +- RELATIONAL ChildA
    |   |
    |   \- SCALAR ChildAScalar
    |      NULL
    |
    \- SCALAR ChildB
       NULL"""

    self._AssertOutputEqualsStripNewlines(output)

  def testMetadata(self):
    root = self._GivenLeafNode(
        'Root', metadata={'call_type': 'Local',
                          'scan_target': 'name'})

    root.PrettyPrint(self.out)
    output = """ SCALAR Root\n call_type: Local, scan_target: name"""
    self.AssertOutputContains(output)

  def testExecutionStatsMeanLatency(self):
    execution_stats = {
        'execution_summary': {
            'num_executions': '3'
        },
        'latency': {
            'mean': '5.3',
            'unit': 'secs'
        }
    }
    root = self._GivenLeafNode('Root', execution_stats=execution_stats)

    root.PrettyPrint(self.out)
    output = """ SCALAR Root\n (3 executions, 5.3 secs average latency)  NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testExecutionStatsTotalLatency(self):
    execution_stats = {
        'execution_summary': {
            'num_executions': '1'
        },
        'latency': {
            'total': '9',
            'unit': 'msecs'
        }
    }
    root = self._GivenLeafNode('Root', execution_stats=execution_stats)

    root.PrettyPrint(self.out)
    output = """ SCALAR Root\n (1 execution, 9 msecs total latency)  NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testExecutionStatsNoLatency(self):
    execution_stats = {'execution_summary': {'num_executions': '9'}}
    root = self._GivenLeafNode('Root', execution_stats=execution_stats)

    root.PrettyPrint(self.out)
    output = """ SCALAR Root\n (9 executions)  NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testExecutionStatsNoSummary(self):
    execution_stats = {
        'latency': {
            'mean': '3.87',
            'total': '10',
            'unit': 'secs'
        }
    }
    root = self._GivenLeafNode('Root', execution_stats=execution_stats)

    root.PrettyPrint(self.out)
    output = """ SCALAR Root\n (3.87 secs average latency)  NULL"""
    self._AssertOutputEqualsStripNewlines(output)

  def testShortRepresentation(self):
    child_a = self._GivenLeafNode('ChildA', description='Some short rep')
    child_b = self._GivenLeafNode('ChildB', description='A different desc')
    root = self._GivenNodeWithChildren([child_a, child_b])

    root.PrettyPrint(self.out)
    output = r""" RELATIONAL Serialize result
    |
    +- SCALAR ChildA
    |  Some short rep
    |
    \- SCALAR ChildB
       A different desc"""
    self._AssertOutputEqualsStripNewlines(output)

  def testQueryHasAggregateStats(self):
    results = self._GivenResultsWithQueryStats()
    has_aggregate_stats = QueryHasAggregateStats(results)
    self.assertEqual(has_aggregate_stats, True)

  def testQueryHasNoAggregateStats(self):
    # Given a result set without query stats.
    results = self.msgs.ResultSet()

    has_aggregate_stats = QueryHasAggregateStats(results)
    self.assertEqual(has_aggregate_stats, False)

  def testDisplayQueryAggregateStats(self):
    results = self._GivenResultsWithQueryStats()
    DisplayQueryAggregateStats(results.stats.queryStats, self.out)
    self.AssertOutputContains(
        'TOTAL_ELAPSED_TIME | CPU_TIME | ROWS_RETURNED | ROWS_SCANNED',
        normalize_space=True)
    # 1.7 msecs         |  .3 msecs    | 9    | 2000
    self.AssertOutputMatches(r'1\.7 msecs[\s|]+\.3 msecs[\s|]+9[\s|]+2000',
                             normalize_space=True)

  def testQueryAggregateStatsKeyNotFound(self):
    # Given stats with an unknown key name.
    results = self._GivenResultsWithQueryStats('gibberish')

    DisplayQueryAggregateStats(results.stats.queryStats, self.out)
    # Then the unknown column name should be included.
    self.AssertOutputContains(
        'TOTAL_ELAPSED_TIME | CPU_TIME | ROWS_RETURNED | ROWS_SCANNED',
        normalize_space=True)
    # Unknown         |  .3 msecs    | 9    | 2000
    self.AssertOutputMatches(r'Unknown[\s|]+\.3 msecs[\s|]+9[\s|]+2000',
                             normalize_space=True)

  def testDisplayQueryPlan(self):
    query_plan = self._GivenResultSetStats()
    DisplayQueryPlan(query_plan, self.out)

    output = r""" RELATIONAL Serialize Result
    |
    +- RELATIONAL Enumerate Rows
    |   |
    |   +- SCALAR Constant
    |   |  <null>
    |   |
    |   \- SCALAR Constant
    |      1
    |
    \- SCALAR Constant
       1"""
    self._AssertOutputEqualsStripNewlines(output)

  def testDisplayQueryResults(self):
    metadata = self.msgs.ResultSetMetadata(rowType=self.msgs.StructType(
        fields=[
            self.msgs.Field(name='colA'),
            self.msgs.Field(name='colB'),
            self.msgs.Field(name=None)
        ]))
    result_rows = [
        self.msgs.ResultSet.RowsValueListEntry(entry=[
            extra_types.JsonValue(string_value='A1'),
            extra_types.JsonValue(string_value='B1'),
            extra_types.JsonValue(string_value='C1')
        ]),
        self.msgs.ResultSet.RowsValueListEntry(entry=[
            extra_types.JsonValue(string_value='A2'),
            extra_types.JsonValue(string_value='B2'),
            extra_types.JsonValue(string_value='C2')
        ])
    ]
    results = self.msgs.ResultSet(metadata=metadata, rows=result_rows)
    DisplayQueryResults(results, self.out)

    self.AssertOutputEquals('colA  colB  (Unspecified)\n'
                            'A1    B1    C1\n'
                            'A2    B2    C2\n')
