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

import datetime

from googlecloudsdk.api_lib.run import global_methods
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
      s.status.conditions = [
          self.serverless_messages.ServiceCondition(
              type='Ready',
              status=six.text_type(bool(i % 2)),
              lastTransitionTime=datetime.datetime.utcfromtimestamp(
                  i).isoformat() + 'Z')
      ]
      s.labels[k8s_object.REGION_LABEL] = 'us-central1'
      s.status.latestCreatedRevisionName = '{}.{}'.format(s.name, i)
      s.metadata.selfLink = '/apis/serving.knative.dev/v1alpha1/namespaces/{}/services/{}'.format(
          self.namespace.Name(), s.name)
      if i:
        s.status.latestReadyRevisionName = '{}.{}'.format(s.name, i%2)
        s.status.traffic = [
            self.serverless_messages.TrafficTarget(
                revisionName='{}.{}'.format(s.name, i%2),
                percent=100)]
        s.annotations[
            'serving.knative.dev/lastModifier'] = 'bozo{}@clown.com'.format(i)
    self.operations.ListServices.return_value = self.services
    self._MockConnectionContext()

  def testServicesList(self):
    """Two services are listable using the Serverless API format."""

    out = self.Run('run services list --region=us-central1')

    self.operations.ListServices.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.services)
    self.AssertOutputEquals(
        """  SERVICE REGION LATEST REVISION SERVING REVISION LAST DEPLOYED BY LAST DEPLOYED AT
           X s0 us-central1 s0.0 1970-01-01T00:00:00Z
           + s1 us-central1 s1.1 s1.1 bozo1@clown.com 1970-01-01T00:00:01Z
           ! s2 us-central1 s2.2 s2.0 bozo2@clown.com 1970-01-01T00:00:02Z
        """,
        normalize_space=True)

  def testServicesListGlobal(self):
    get_client_instance = self.StartObjectPatch(
        global_methods,
        'GetServerlessClientInstance',
        return_value=self.mock_serverless_client)
    list_services = self.StartObjectPatch(
        global_methods, 'ListServices', return_value=self.services)
    out = self.Run('run services list')
    get_client_instance.assert_called_once()
    list_services.assert_called_once()
    self.assertEqual(out, self.services)
    self.AssertOutputEquals(
        """  SERVICE REGION LATEST REVISION SERVING REVISION LAST DEPLOYED BY LAST DEPLOYED AT
           X s0 us-central1 s0.0 1970-01-01T00:00:00Z
           + s1 us-central1 s1.1 s1.1 bozo1@clown.com 1970-01-01T00:00:01Z
           ! s2 us-central1 s2.2 s2.0 bozo2@clown.com 1970-01-01T00:00:02Z
        """, normalize_space=True)

  def testServicesListYamlFormat(self):
    """Two services are listable using the Serverless API format."""

    out = self.Run('run services list --format yaml --region=us-central1')

    self.operations.ListServices.assert_called_once_with(self.namespace)
    self.assertEqual(out, self.services)
    self.AssertOutputContains('name: s0', normalize_space=True)
    self.AssertOutputContains('metadata:', normalize_space=True)
    self.AssertOutputContains('name: s1', normalize_space=True)
    self.AssertOutputContains(
        'serving.knative.dev/lastModifier: bozo1@clown.com',
        normalize_space=True)
    self.AssertOutputContains(
        'serving.knative.dev/lastModifier: bozo2@clown.com',
        normalize_space=True)
    self.AssertOutputContains(
        'lastTransitionTime: \'1970-01-01T00:00:00Z\'', normalize_space=True)
    self.AssertOutputContains(
        'lastTransitionTime: \'1970-01-01T00:00:01Z\'', normalize_space=True)
    self.AssertOutputContains(
        'lastTransitionTime: \'1970-01-01T00:00:02Z\'', normalize_space=True)

  def testServicesListUri(self):
    """Two services are listable using the Serverless API format."""

    self.Run('run services list --uri --region=us-central1')

    self.operations.ListServices.assert_called_once_with(self.namespace)
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s0
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s1
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s2
        """,
        normalize_space=True)

  def testServicesListGlobalUri(self):
    """Two services are listable using the Serverless API format."""
    get_client_instance = self.StartObjectPatch(
        global_methods,
        'GetServerlessClientInstance',
        return_value=self.mock_serverless_client)
    self.mock_serverless_client.url = 'https://run.googleapis.com/'
    list_services = self.StartObjectPatch(
        global_methods, 'ListServices', return_value=self.services)
    self.Run('run services list --uri')

    get_client_instance.assert_called_once()
    list_services.assert_called_once()
    self.AssertOutputEquals(
        """https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s0
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s1
        https://us-central1-run.googleapis.com/apis/serving.knative.dev/v1alpha1/namespaces/fake-project/services/s2
        """,
        normalize_space=True)
