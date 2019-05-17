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

from googlecloudsdk.api_lib.run import route
from tests.lib.surface.run import base
import six


class RoutesListTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.routes = [
        route.Route.New(
            self.mock_serverless_client, 'us-central1.fake-project')
        for _ in range(2)]
    for i, r in enumerate(self.routes):
      r.name = 'route{}'.format(i)
      r.metadata.creationTimestamp = '2018/01/01 00:{}0:00Z'.format(i)
      r.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/routes/{}'.format(
          self.namespace.Name(), r.name)
      r.status.conditions = [self.serverless_messages.RouteCondition(
          type='Ready',
          status=six.text_type(bool(i%2)))]
    self.operations.ListRoutes.return_value = self.routes
    self._MockConnectionContext()

  def testNoArg(self):
    """Two routes are listable using the Serverless API format."""
    out = self.Run('run routes list')

    self.operations.ListRoutes.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.routes)
    self.AssertOutputEquals(
        """ROUTE
        X route0
        + route1
        """, normalize_space=True)

  def testNoArgUri(self):
    """Two routes are listable using the Serverless API format."""
    self.Run('run routes list --uri')

    self.operations.ListRoutes.assert_called_once_with(self.namespace)
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/routes/route0
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/routes/route1
        """,
        normalize_space=True)
