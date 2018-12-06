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
"""Unit tests for the `run services list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import service
from tests.lib.surface.run import base

import six


class ServicesListTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.services = [
        service.Service.New(
            self.mock_serverless_client, 'fake-project')
        for _ in range(3)]
    for i, s in enumerate(self.services):
      s.name = 's{}'.format(i)
      s.status.conditions = [self.serverless_messages.ServiceCondition(
          type='Ready',
          status=six.text_type(bool(i%2)))]
      s.annotations[k8s_object.REGION_ANNOTATION] = 'us-central1'
      s.status.latestCreatedRevisionName = '{}.{}'.format(s.name, i)
      if i:
        s.status.latestReadyRevisionName = '{}.{}'.format(s.name, i%2)
        s.status.traffic = [
            self.serverless_messages.TrafficTarget(
                revisionName='{}.{}'.format(s.name, i%2),
                percent=100)]
    self.operations.ListServices.return_value = self.services

  def testServicesList(self):
    """Two services are listable using the Serverless API format."""

    out = self.Run('run services list')

    self.operations.ListServices.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.services)
    self.AssertOutputEquals(
        """  SERVICE REGION LATEST REVISION SERVING REVISION
           X s0 us-central1 s0.0
           + s1 us-central1 s1.1 s1.1
           ! s2 us-central1 s2.2 s2.0
        """, normalize_space=True)

  def testServicesListYamlFormat(self):
    """Two services are listable using the Serverless API format."""

    out = self.Run('run services list --format yaml')

    self.operations.ListServices.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.services)
    self.AssertOutputContains('name: s0', normalize_space=True)
    self.AssertOutputContains('metadata:', normalize_space=True)
    self.AssertOutputContains('name: s1', normalize_space=True)
