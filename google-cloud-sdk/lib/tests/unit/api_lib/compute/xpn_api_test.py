# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for XPN API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.compute import client_adapter
from googlecloudsdk.api_lib.compute import xpn_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


def _MakeRequestsError(*_, **kwargs):
  if False:  # pylint: disable=using-constant-test
    yield
  kwargs['errors'].append((404, 'Not Found'))


_DEFAULT_API_VERSION = 'v1'


class XpnApiTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(_DEFAULT_API_VERSION)
    self.xpn_client = xpn_api.GetXpnClient(calliope_base.ReleaseTrack.GA)

  def _SetupMockXpnClient(self):
    self.mock_client = mock.Client(
        core_apis.GetClientClass('compute', _DEFAULT_API_VERSION),
        real_client=core_apis.GetClientInstance(
            'compute', _DEFAULT_API_VERSION, no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = self.mock_client.MESSAGES_MODULE
    self.xpn_client = xpn_api.XpnClient(
        compute_client=client_adapter.ClientAdapter(
            api_default_version=_DEFAULT_API_VERSION, client=self.mock_client))

  def _MakeProject(self, name=None):
    project_status_enum = self.messages.Project.XpnProjectStatusValueValuesEnum
    return self.messages.Project(
        name=(name or 'xpn-host'),
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        selfLink='https://www.googleapis.com/compute/v1/projects/xpn-host/',
        xpnProjectStatus=project_status_enum.HOST)

  def testEnableHost(self):
    self.make_requests.side_effect = iter([iter([None])])

    self.xpn_client.EnableHost('myproject')

    self.CheckRequests([
        (self.compute.projects,
         'EnableXpnHost',
         self.messages.ComputeProjectsEnableXpnHostRequest(
             project='myproject'))])

  def testEnableHost_Errors(self):
    self.make_requests.side_effect = _MakeRequestsError

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Could not enable [myproject] as XPN host')):
      self.xpn_client.EnableHost('myproject')

    self.CheckRequests([
        (self.compute.projects,
         'EnableXpnHost',
         self.messages.ComputeProjectsEnableXpnHostRequest(
             project='myproject'))])

  def testDisableHost(self):
    self.make_requests.side_effect = iter([iter([None])])

    self.xpn_client.DisableHost('myproject')

    self.CheckRequests([
        (self.compute.projects,
         'DisableXpnHost',
         self.messages.ComputeProjectsDisableXpnHostRequest(
             project='myproject'))])

  def testDisableHost_Errors(self):
    self.make_requests.side_effect = _MakeRequestsError

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Could not disable [myproject] as XPN host')):
      self.xpn_client.DisableHost('myproject')

    self.CheckRequests([
        (self.compute.projects,
         'DisableXpnHost',
         self.messages.ComputeProjectsDisableXpnHostRequest(
             project='myproject'))])

  def testGetHostProject(self):
    project = self._MakeProject()
    self.make_requests.side_effect = iter([iter([project])])

    self.assertEqual(self.xpn_client.GetHostProject('myproject'), project)

    self.CheckRequests([
        (self.compute.projects,
         'GetXpnHost',
         self.messages.ComputeProjectsGetXpnHostRequest(
             project='myproject'))])

  def testGetHostProject_Errors(self):
    self.make_requests.side_effect = _MakeRequestsError

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Could not get XPN host for project [myproject]')):
      self.xpn_client.GetHostProject('myproject')

    self.CheckRequests([
        (self.compute.projects,
         'GetXpnHost',
         self.messages.ComputeProjectsGetXpnHostRequest(
             project='myproject'))])

  def testListEnabledResources(self):
    self._SetupMockXpnClient()
    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum

    expected_request_1 = self.messages.ComputeProjectsGetXpnResourcesRequest(
        project='myproject')
    project_1 = self.messages.XpnResourceId(
        id='xpn-associated-project-1', type=xpn_types.PROJECT)
    response_1 = self.messages.ProjectsGetXpnResources(
        kind='compute#ProjectsGetXpnResources',
        resources=[project_1],
        nextPageToken='pagetoken-1')
    self.mock_client.projects.GetXpnResources.Expect(expected_request_1,
                                                     response_1)

    expected_request_2 = self.messages.ComputeProjectsGetXpnResourcesRequest(
        project='myproject', pageToken='pagetoken-1')
    project_2 = self.messages.XpnResourceId(
        id='xpn-associated-project-2', type=xpn_types.PROJECT)
    response_2 = self.messages.ProjectsGetXpnResources(
        kind='compute#ProjectsGetXpnResources', resources=[project_2])
    self.mock_client.projects.GetXpnResources.Expect(expected_request_2,
                                                     response_2)

    results = list(self.xpn_client.ListEnabledResources('myproject'))
    self.assertEqual(results, [project_1, project_2])

  def testListEnabledResources_Errors(self):
    self._SetupMockXpnClient()
    expected_request = self.messages.ComputeProjectsGetXpnResourcesRequest(
        project='myproject')
    self.mock_client.projects.GetXpnResources.Expect(
        expected_request, exception=apitools_exceptions.Error(404, 'Not Found'))

    with self.assertRaisesRegex(apitools_exceptions.Error, 'Not Found'):
      list(self.xpn_client.ListEnabledResources('myproject'))

  def testListOrganizationsHostProjects_OrganizationIdSpecified(self):
    self._SetupMockXpnClient()

    expected_request_1 = self.messages.ComputeProjectsListXpnHostsRequest(
        project='myproject',
        projectsListXpnHostsRequest=self.messages.ProjectsListXpnHostsRequest(
            organization='12345'))
    project_1 = self._MakeProject('xpn-host-1')
    response_1 = self.messages.XpnHostList(
        items=[project_1],
        kind='compute#xpnHostList',
        nextPageToken='pagetoken-1')
    self.mock_client.projects.ListXpnHosts.Expect(expected_request_1,
                                                  response_1)

    expected_request_2 = self.messages.ComputeProjectsListXpnHostsRequest(
        project='myproject',
        pageToken='pagetoken-1',
        projectsListXpnHostsRequest=self.messages.ProjectsListXpnHostsRequest(
            organization='12345'))
    project_2 = self._MakeProject('xpn-host-2')
    response_2 = self.messages.XpnHostList(
        items=[project_2], kind='compute#xpnHostList')
    self.mock_client.projects.ListXpnHosts.Expect(expected_request_2,
                                                  response_2)

    results = self.xpn_client.ListOrganizationHostProjects(
        project='myproject', organization_id='12345')
    self.assertEqual(list(results), [project_1, project_2])

  def testListOrganizationsHostProjects_OrganizationIdSpecifiedError(self):
    self._SetupMockXpnClient()
    expected_request = self.messages.ComputeProjectsListXpnHostsRequest(
        project='myproject',
        projectsListXpnHostsRequest=self.messages.ProjectsListXpnHostsRequest(
            organization='12345'))
    self.mock_client.projects.ListXpnHosts.Expect(
        expected_request, exception=apitools_exceptions.Error(404, 'Not Found'))

    with self.assertRaisesRegex(apitools_exceptions.Error, 'Not Found'):
      list(
          self.xpn_client.ListOrganizationHostProjects(
              project='myproject', organization_id='12345'))

  def testEnableXpnAssociatedProject(self):
    self.make_requests.side_effect = iter([iter([None])])

    self.xpn_client.EnableXpnAssociatedProject('xpn-host', 'myproject')

    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    projects_enable_request = self.messages.ProjectsEnableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(id='myproject',
                                                type=xpn_types.PROJECT))
    self.CheckRequests([
        (self.compute.projects,
         'EnableXpnResource',
         self.messages.ComputeProjectsEnableXpnResourceRequest(
             project='xpn-host',
             projectsEnableXpnResourceRequest=projects_enable_request))])

  def testEnableXpnAssociatedProject_Errors(self):
    self.make_requests.side_effect = _MakeRequestsError

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Could not enable resource [myproject] as an associated '
                  'resource for project [xpn-host]')):
      self.xpn_client.EnableXpnAssociatedProject('xpn-host', 'myproject')

    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    projects_enable_request = self.messages.ProjectsEnableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(id='myproject',
                                                type=xpn_types.PROJECT))
    self.CheckRequests([
        (self.compute.projects,
         'EnableXpnResource',
         self.messages.ComputeProjectsEnableXpnResourceRequest(
             project='xpn-host',
             projectsEnableXpnResourceRequest=projects_enable_request))])

  def testDisableXpnAssociatedProject(self):
    self.make_requests.side_effect = iter([iter([None])])

    self.xpn_client.DisableXpnAssociatedProject('xpn-host', 'myproject')

    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    projects_disable_request = self.messages.ProjectsDisableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(id='myproject',
                                                type=xpn_types.PROJECT))
    self.CheckRequests([
        (self.compute.projects,
         'DisableXpnResource',
         self.messages.ComputeProjectsDisableXpnResourceRequest(
             project='xpn-host',
             projectsDisableXpnResourceRequest=projects_disable_request))])

  def testDisableXpnAssociatedProject_Errors(self):
    self.make_requests.side_effect = _MakeRequestsError

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Could not disable resource [myproject] as an associated '
                  'resource for project [xpn-host]')):
      self.xpn_client.DisableXpnAssociatedProject('xpn-host', 'myproject')

    xpn_types = self.messages.XpnResourceId.TypeValueValuesEnum
    projects_disable_request = self.messages.ProjectsDisableXpnResourceRequest(
        xpnResource=self.messages.XpnResourceId(id='myproject',
                                                type=xpn_types.PROJECT))
    self.CheckRequests([
        (self.compute.projects,
         'DisableXpnResource',
         self.messages.ComputeProjectsDisableXpnResourceRequest(
             project='xpn-host',
             projectsDisableXpnResourceRequest=projects_disable_request))])


if __name__ == '__main__':
  test_case.main()
