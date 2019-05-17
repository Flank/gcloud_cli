# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Unit tests for the `run domain-mappings list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import domain_mapping
from googlecloudsdk.api_lib.run import k8s_object
from tests.lib.surface.run import base


class DomainMappingListTest(base.ServerlessSurfaceBase):

  def SetUp(self):
    self.domain_mappings = [
        domain_mapping.DomainMapping.New(
            self.mock_serverless_client, 'fake-project')
        for _ in range(2)]
    for i, d in enumerate(self.domain_mappings):
      d.name = 'www.example{}.com'.format(i)
      d.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/domainmappings/{}'.format(
          self.namespace.Name(), d.name)
      d.labels[k8s_object.REGION_LABEL] = 'us-central1'
      d.spec.routeName = 'd{}'.format(i)  # Name of service
    self.operations.ListDomainMappings.return_value = self.domain_mappings
    self._MockConnectionContext()

  def testDomainMappingsList(self):
    """Two domain mappings are listable using the Serverless API format."""

    out = self.Run('run domain-mappings list')

    self.operations.ListDomainMappings.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.domain_mappings)
    self.AssertOutputEquals(
        """DOMAIN SERVICE REGION
           www.example0.com d0 us-central1
           www.example1.com d1 us-central1
        """, normalize_space=True)

  def testDomainMappingsListUri(self):
    """Two routes are listable using the Serverless API format."""
    self.Run('run domain-mappings list --uri')

    self.operations.ListDomainMappings.assert_called_once_with(self.namespace)
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/domainmappings/www.example0.com
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/domainmappings/www.example1.com
        """,
        normalize_space=True)
