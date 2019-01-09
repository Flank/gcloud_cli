# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for the `run revisions list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import revision
from tests.lib.surface.run import base
from six.moves import range


class RevisionsListTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.revisions = [
        revision.Revision.New(
            self.mock_serverless_client, 'us-central1.fake-project')
        for _ in range(2)]
    for i, r in enumerate(self.revisions):
      r.name = 'revision{}'.format(i)
      r.metadata.creationTimestamp = '2018/01/01 00:{}0:00Z'.format(i)
      r.labels['serving.knative.dev/service'] = 'foo'
      r.labels['serving.knative.dev/configuration'] = 'foo'
      r.annotations[revision.AUTHOR_ANNOTATION] = 'some{}@google.com'.format(i)
      r.status.conditions = [self.serverless_messages.RevisionCondition(
          type='Ready',
          status='Unknown' if i%2 else 'True')]

    self.operations.ListRevisions.return_value = self.revisions

  def testNoArg(self):
    """Two revisions are listable using the Serverless API format."""
    out = self.Run('run revisions list')

    self.operations.ListRevisions.assert_called_once_with(self.namespace,
                                                          None)
    self.assertEqual(out, self.revisions)
    self.AssertOutputEquals(
        """REVISION SERVICE AUTHOR CREATED
        + revision0 foo some0@google.com 2018-01-01 00:00:00 UTC
        . revision1 foo some1@google.com 2018-01-01 00:10:00 UTC
        """, normalize_space=True)

  def testServiceArg(self):
    """Two revisions are listable using the Serverless API format."""
    out = self.Run('run revisions list --service foo')

    self.operations.ListRevisions.assert_called_once_with(self.namespace,
                                                          'foo')
    self.assertEqual(out, self.revisions)
    self.AssertOutputEquals(
        """REVISION SERVICE AUTHOR CREATED
        + revision0 foo some0@google.com 2018-01-01 00:00:00 UTC
        . revision1 foo some1@google.com 2018-01-01 00:10:00 UTC
        """, normalize_space=True)
