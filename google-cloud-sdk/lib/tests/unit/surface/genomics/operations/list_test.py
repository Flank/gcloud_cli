# -*- coding: utf-8 -*- #
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

"""Tests for genomics operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.genomics import base
from six.moves import range


class ListTest(base.GenomicsUnitTest):
  """Unit tests for genomics operations list command."""

  def createOperationResponseMessage(self, identifier=None):
    """Helper function to simulate a simple operation response.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Operation with name and id set.
    """
    if identifier is not None:
      name = 'operation-name' + str(identifier)
    else:
      name = 'operation-name'
    return self.messages.Operation(name=name, done=False,)

  def createV2OperationResponseMessage(self, identifier=None):
    """Helper function to simulate a simple v2 operation response.

    Args:
      identifier: Optional integer to act as id and append to name.

    Returns:
      Operation with name and id set.
    """
    if identifier is not None:
      name = 'operation-name' + str(identifier)
    else:
      name = 'operation-name'
    return self.messages_v2.Operation(name=name, done=False,)

  def testOperationsList(self):
    num_operations = 3
    self.mocked_client.operations.List.Expect(
        request=self.messages.GenomicsOperationsListRequest(
            name='operations',
            filter='createTime <= 100 AND projectId=fake-project',),
        response=self.messages.ListOperationsResponse(
            operations=[self.createOperationResponseMessage(i)
                        for i in range(num_operations)]))
    self.RunGenomics(['operations', 'list', '--where', 'createTime <= 100'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ---
      done: false
      name: operation-name0
      ---
      done: false
      name: operation-name1
      ---
      done: false
      name: operation-name2
      """),
                            normalize_space=True)

  def testOperationsList_WithoutWhere(self):
    self.mocked_client_v2.projects_operations.List.Expect(
        request=self.messages_v2.GenomicsProjectsOperationsListRequest(
            name='projects/fake-project/operations',
            filter=None,),
        response=self.messages_v2.ListOperationsResponse(
            operations=[self.createV2OperationResponseMessage(i)
                        for i in range(1)]))
    self.mocked_client.operations.List.Expect(
        request=self.messages.GenomicsOperationsListRequest(
            name='operations',
            filter='projectId=fake-project',),
        response=self.messages.ListOperationsResponse(
            operations=[self.createOperationResponseMessage(i)
                        for i in range(2)]))
    self.RunGenomics(['operations', 'list'])
    self.AssertOutputEquals(textwrap.dedent("""\
      ---
      done: false
      name: operation-name0
      ---
      done: false
      name: operation-name0
      ---
      done: false
      name: operation-name1
      """),
                            normalize_space=True)

  def testOperationsList_EmptyList(self):
    self.mocked_client.operations.List.Expect(
        request=self.messages.GenomicsOperationsListRequest(
            name='operations',
            filter='createTime <= 100 AND projectId=fake-project',),
        response=self.messages.ListOperationsResponse())
    self.RunGenomics(['operations', 'list', '--where', 'createTime <= 100'])
    self.AssertOutputEquals('')

  def testOperationsList_Limit_InvalidLow(self):
    with self.AssertRaisesArgumentErrorRegexp(
        '--limit: Value must be greater than or equal to 1; received: -1'):
      self.RunGenomics(['operations', 'list', '--where', 'blah', '--limit=-1'])

  def testOperationsList_Limit(self):
    num_operations = 10
    limit = 3
    self.mocked_client.operations.List.Expect(
        request=self.messages.GenomicsOperationsListRequest(
            name='operations',
            filter='createTime <= 100 AND projectId=fake-project',
            pageSize=limit),
        response=self.messages.ListOperationsResponse(
            operations=[self.createOperationResponseMessage(i)
                        for i in range(num_operations)]))
    self.RunGenomics([
        'operations', 'list', '--limit', str(limit), '--where',
        'createTime <= 100'
    ])
    self.AssertOutputEquals(textwrap.dedent("""\
      ---
      done: false
      name: operation-name0
      ---
      done: false
      name: operation-name1
      ---
      done: false
      name: operation-name2
      """), normalize_space=True)

  def testInaccessibleProject(self):
    self.mocked_client_v2.projects_operations.List.Expect(
        request=self.messages_v2.GenomicsProjectsOperationsListRequest(
            name='projects/secret-project/operations',
            filter=None,),
        exception=self.MakeHttpError(403,
                                     'Permission denied; need GET permission'))

    with self.assertRaisesRegex(exceptions.HttpException,
                                'Permission denied; need GET permission'):
      self.RunGenomics(['operations', 'list', '--project', 'secret-project'])

if __name__ == '__main__':
  test_case.main()
