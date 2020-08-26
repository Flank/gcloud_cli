# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for `gcloud service-directory namespaces create`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.service_directory import base


class NamespacesCreateTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.labels = self._Labels(
        additional_properties=[self._AdditionalProperty(key='a', value='b')])
    self.location_name = resources.REGISTRY.Parse(
        'my-location',
        params={
            'projectsId': self.Project(),
        },
        collection='servicedirectory.projects.locations').RelativeName()

  def _Namespace(self, name=None, labels=None):
    return self.msgs.Namespace(name=name, labels=labels)

  def _Labels(self, additional_properties=None):
    return self.msgs.Namespace.LabelsValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Namespace.LabelsValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectCreateNamespaceRequest(self, namespace_id, namespace):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesCreateRequest(
        parent=self.location_name,
        namespaceId=namespace_id,
        namespace=namespace)
    self.client.projects_locations_namespaces.Create.Expect(
        request=req,
        response=self._Namespace(
            name=self.location_name + '/namespaces/' + namespace_id,
            labels=namespace.labels))

  def testCreate(self):
    expected = self._Namespace(self.location_name + '/namespaces/my-namespace')
    self._ExpectCreateNamespaceRequest('my-namespace', self._Namespace())

    actual = self.Run('service-directory namespaces create my-namespace '
                      '--location my-location ')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created namespace [my-namespace].')

  def testCreate_WithLabels(self):
    expected = self._Namespace(
        self.location_name + '/namespaces/my-namespace', labels=self.labels)
    self._ExpectCreateNamespaceRequest('my-namespace',
                                       self._Namespace(labels=self.labels))

    actual = self.Run('service-directory namespaces create my-namespace '
                      '--location my-location '
                      '--labels a=b')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created namespace [my-namespace].')

  def testCreate_RelativeName(self):
    expected = self._Namespace(self.location_name + '/namespaces/my-namespace')
    self._ExpectCreateNamespaceRequest('my-namespace', self._Namespace())

    actual = self.Run(
        'service-directory namespaces create {}/namespaces/my-namespace'.format(
            self.location_name))

    self.assertEqual(actual, expected)
    self.AssertErrContains('Created namespace [my-namespace].')

  def testCreate_WithoutNamespaceId_Fails(self):
    with self.AssertRaisesArgumentErrorMatches('NAMESPACE must be specified.'):
      self.Run('service-directory namespaces create ' '--location my-location')

  def testCreate_InvalidRequest_Fails(self):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesCreateRequest(
        parent=self.location_name,
        namespaceId='my-namespace',
        namespace=self._Namespace())
    exception = http_error.MakeHttpError(code=400)
    self.client.projects_locations_namespaces.Create.Expect(
        request=req, exception=exception, response=None)
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Invalid request API reason: Invalid request.'):
      self.Run('service-directory namespaces create my-namespace '
               '--location my-location ')
    self.AssertErrNotContains('Created namespace')


class NamespacesCreateTestAlpha(NamespacesCreateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
