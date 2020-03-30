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
"""Tests for `gcloud service-directory namespaces list`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.service_directory import base


class NamespacesListTestBeta(base.ServiceDirectoryUnitTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    # By default, the command output resources are formatted and displayed on
    # log.out. Disabling the output allows the output resources to be returned
    # by the Run() method. This disables all user interactions/output.
    properties.VALUES.core.user_output_enabled.Set(False)

    self.location_name = resources.REGISTRY.Parse(
        'my-location',
        params={
            'projectsId': self.Project(),
        },
        collection='servicedirectory.projects.locations').RelativeName()
    self.my_namespace = self._Namespace(
        name=self.location_name + '/namespaces/my-namespace', labels=None)
    self.a_namespace = self._Namespace(
        name=self.location_name + '/namespaces/a-namespace', labels=None)
    self.namespaces = [
        self.my_namespace,
        self.a_namespace,
    ]

  def _Namespace(self, name=None, labels=None):
    return self.msgs.Namespace(name=name, labels=labels)

  def _ListNamespacesResponse(self, namespaces, next_page_token=None):
    return self.msgs.ListNamespacesResponse(
        namespaces=namespaces, nextPageToken=next_page_token)

  def _ExpectListNamespaceRequest(self,
                                  parent,
                                  namespace_filter=None,
                                  order_by=None,
                                  page_size=None,
                                  page_token=None,
                                  response_namespaces=None,
                                  response_page_token=None):
    req = self.msgs.ServicedirectoryProjectsLocationsNamespacesListRequest(
        parent=parent,
        filter=namespace_filter,
        orderBy=order_by,
        pageSize=page_size,
        pageToken=page_token)
    self.client.projects_locations_namespaces.List.Expect(
        request=req,
        response=self._ListNamespacesResponse(response_namespaces,
                                              response_page_token))

  def testList_NoFlags_YieldsDefaultList(self):
    expected = self.namespaces
    self._ExpectListNamespaceRequest(
        parent=self.location_name, response_namespaces=expected)

    actual = self.Run('service-directory namespaces list '
                      '--location my-location')

    self.assertEqual(actual, expected)

  def testList_FilterByName_YieldsMyNamespace(self):
    expected = [self.my_namespace]
    self._ExpectListNamespaceRequest(
        parent=self.location_name,
        namespace_filter='name:my-namespace',
        response_namespaces=expected)

    actual = self.Run('service-directory namespaces list '
                      '--location my-location '
                      '--filter name:my-namespace')

    self.assertEqual(actual, expected)

  def testList_OrderbyName_YieldsNameAsc(self):
    expected = [self.a_namespace, self.my_namespace]
    self._ExpectListNamespaceRequest(
        parent=self.location_name,
        order_by='name desc,name asc',
        response_namespaces=expected)

    actual = self.Run('service-directory namespaces list '
                      '--location my-location '
                      '--sort-by ~name,name')

    self.assertEqual(actual, expected)

  def testList_MultiplePages_YieldsMultiplePages(self):
    expected = self.namespaces
    self._ExpectListNamespaceRequest(
        parent=self.location_name,
        page_size=1,
        response_namespaces=expected[:1],
        response_page_token='nextPageToken')
    self._ExpectListNamespaceRequest(
        parent=self.location_name,
        page_size=1,
        page_token='nextPageToken',
        response_namespaces=expected[1:])

    actual = self.Run('service-directory namespaces list '
                      '--location my-location '
                      '--page-size 1')

    self.assertEqual(actual, expected)


class NamespacesListTestAlpha(NamespacesListTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
