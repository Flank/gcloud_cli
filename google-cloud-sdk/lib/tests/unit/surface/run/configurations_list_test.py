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

from googlecloudsdk.api_lib.run import configuration
from tests.lib.surface.run import base

import six
from six.moves import range


class ConfigurationsListTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.configurations = [
        configuration.Configuration.New(
            self.mock_serverless_client, 'fake-project')
        for _ in range(2)]
    for i, r in enumerate(self.configurations):
      r.name = 'conf{}'.format(i)
      r.metadata.creationTimestamp = '2018/01/01 00:{}0:00Z'.format(i)
      r.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/configurations/{}'.format(
          self.namespace.Name(), r.name)
      r.status.latestCreatedRevisionName = '{}.3'.format(r.name)
      r.status.latestReadyRevisionName = '{}.1'.format(r.name)
      r.status.conditions = [self.serverless_messages.ConfigurationCondition(
          type='Ready',
          status=six.text_type(bool(i%2)))]
    self.operations.ListConfigurations.return_value = self.configurations
    self._MockConnectionContext()

  def testNoArg(self):
    """Two configurations are listable using the Serverless API format."""
    out = self.Run('run configurations list')

    self.operations.ListConfigurations.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.configurations)
    self.AssertOutputEquals(
        """CONFIGURATION REGION LATEST REVISION READY REVISION
        X conf0 conf0.3 conf0.1
        + conf1 conf1.3 conf1.1
        """, normalize_space=True)

  def testNoArgUri(self):
    """Two routes are listable using the Serverless API format."""
    self.Run('run configurations list --uri')

    self.operations.ListConfigurations.assert_called_once_with(self.namespace)
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/configurations/conf0
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/configurations/conf1
        """,
        normalize_space=True)

