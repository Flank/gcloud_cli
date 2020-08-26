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
"""Tests for `gcloud service-directory namespaces update`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.service_directory import base


class NamespacesUpdateTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.namespace_name = resources.REGISTRY.Parse(
        'my-namespace',
        params={
            'projectsId': self.Project(),
            'locationsId': 'my-location',
        },
        collection='servicedirectory.projects.locations.namespaces'
    ).RelativeName()
    self.labels = self._Labels(additional_properties=[
        self._AdditionalProperty(key='a', value='b'),
        self._AdditionalProperty(key='c', value='d'),
    ])
    self.my_namespace = self._Namespace(
        name=self.namespace_name, labels=self.labels)

  def _Namespace(self, name=None, labels=None):
    return self.msgs.Namespace(name=name, labels=labels)

  def _Labels(self, additional_properties=None):
    if not additional_properties:
      additional_properties = []
    return self.msgs.Namespace.LabelsValue(
        additionalProperties=additional_properties)

  def _AdditionalProperty(self, key, value=None):
    return self.msgs.Namespace.LabelsValue.AdditionalProperty(
        key=key, value=value)

  def _ExpectUpdateNamespaceRequest(self,
                                    namespace=None,
                                    name=None,
                                    update_mask=None,
                                    response=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesPatchRequest(
        namespace=namespace, name=name, updateMask=update_mask)
    self.client.projects_locations_namespaces.Patch.Expect(
        request=req, response=response)

  def testUpdate_UpdateLabels(self):
    labels = self._Labels([self._AdditionalProperty('a', 'b')])
    namespace = self._Namespace(labels=labels)
    expected = self._Namespace(name=self.namespace_name, labels=labels)

    self._ExpectUpdateNamespaceRequest(
        namespace=namespace,
        name=self.namespace_name,
        update_mask='labels',
        response=expected)

    actual = self.Run('service-directory namespaces update my-namespace '
                      '--location my-location '
                      '--labels a=b')

    self.assertEqual(actual, expected)
    self.AssertErrContains('Updated namespace [my-namespace].')

  def testUpdate_InvliadRequest_Fails(self):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesPatchRequest(
        namespace=self._Namespace(
            labels=self._Labels([self._AdditionalProperty('a', 'b')])),
        name=self.namespace_name,
        updateMask='labels')
    exception = http_error.MakeHttpError(code=400)
    self.client.projects_locations_namespaces.Patch.Expect(
        request=req, exception=exception, response=None)
    with self.assertRaisesRegex(exceptions.HttpException,
                                'Invalid request API reason: Invalid request.'):
      self.Run('service-directory namespaces update my-namespace '
               '--location my-location '
               '--labels a=b')
    self.AssertErrNotContains('Updated namespace')


class NamespacesUpdateTestAlpha(NamespacesUpdateTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
