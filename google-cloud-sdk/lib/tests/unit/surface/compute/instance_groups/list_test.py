# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the instance-groups list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class InstanceGroupsListTestBase(test_base.BaseTest):

  def SetUp(self):
    api_version = self.ApiVersion()

    def _MockMakeRequests(requests, batch_url, *unused_args, **unused_kwargs):
      _ = batch_url, unused_args, unused_kwargs
      if len(requests) != 1:
        self.fail('expected to send single request, sent: ' + str(requests))
      service = requests[0][0]
      verb = requests[0][1]
      if verb == 'AggregatedList':
        if service == self.compute.instanceGroupManagers:
          return (test_resources.MakeInstanceGroupManagers(api_version)
                  + test_resources.MakeInstanceGroupManagers(
                      api=api_version,
                      scope_name='region-1',
                      scope_type='region'))
        elif service == self.compute.instanceGroups:
          return (test_resources.MakeInstanceGroups(self.messages, api_version)
                  + test_resources.MakeInstanceGroups(self.messages,
                                                      api=api_version,
                                                      scope_name='region-1',
                                                      scope_type='region'))
      if verb == 'List':
        if service == self.compute.instanceGroups:
          return test_resources.MakeInstanceGroups(self.messages, api_version)
        elif service == self.compute.regionInstanceGroups:
          return test_resources.MakeInstanceGroups(self.messages,
                                                   api=api_version,
                                                   scope_name='region-1',
                                                   scope_type='region')
        elif service == self.compute.instanceGroupManagers:
          return test_resources.MakeInstanceGroupManagers(api_version)
        elif service == self.compute.regionInstanceGroupManagers:
          return test_resources.MakeInstanceGroupManagers(api=api_version,
                                                          scope_name='region-1',
                                                          scope_type='region')
      else:
        self.fail('unexpected request ' + str(requests[0]))

    self.SelectApi(api_version)
    make_requests_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.MakeRequests')
    self.addCleanup(make_requests_patcher.stop)
    self.make_requests = make_requests_patcher.start()
    self.make_requests.side_effect = _MockMakeRequests

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

    def _MockListJson(*args, **kwargs):
      messages = _MockMakeRequests(*args, **kwargs)
      return resource_projector.MakeSerializable(messages)
    self.list_json.side_effect = _MockListJson


class InstanceGroupsListTest(InstanceGroupsListTestBase,
                             completer_test_base.CompleterBase):
  """Tests for GA version of 'instance-group list' command."""

  def ApiVersion(self):
    return 'v1'

  def testAggregatedTableOutput(self):
    self.Run('compute instance-groups list')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'AggregatedList',
                   self.messages.ComputeInstanceGroupsAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
        [(self.compute.regionInstanceGroupManagers,
          'List',
          self.messages.ComputeRegionInstanceGroupManagersListRequest(
              maxResults=500,
              region='region-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE  NETWORK   MANAGED INSTANCES
            group-1 zone-1   zone             Yes     0
            group-2 zone-1   zone   default   Yes     3
            group-3 zone-1   zone   network-1 Yes     10
            group-4 zone-1   zone   network-1 No      1
            group-1 region-1 region           Yes     0
            group-2 region-1 region default   Yes     3
            group-3 region-1 region network-1 Yes     10
            group-4 region-1 region network-1 No      1
            """), normalize_space=True)

  def testAggregatedTableOutputWithFilter(self):
    self.Run("""compute instance-groups list --filter=MANAGED:yes""")
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'AggregatedList',
                   self.messages.ComputeInstanceGroupsAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
        [(self.compute.regionInstanceGroupManagers,
          'List',
          self.messages.ComputeRegionInstanceGroupManagersListRequest(
              maxResults=500,
              region='region-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE  NETWORK   MANAGED INSTANCES
            group-1 zone-1   zone             Yes     0
            group-2 zone-1   zone   default   Yes     3
            group-3 zone-1   zone   network-1 Yes     10
            group-1 region-1 region           Yes     0
            group-2 region-1 region default   Yes     3
            group-3 region-1 region network-1 Yes     10
            """), normalize_space=True)

  def testZonalTableOutput(self):
    self.Run('compute instance-groups list --zones=zone-1')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE NETWORK   MANAGED INSTANCES
            group-1 zone-1   zone            Yes     0
            group-2 zone-1   zone  default   Yes     3
            group-3 zone-1   zone  network-1 Yes     10
            group-4 zone-1   zone  network-1 No      1
            """), normalize_space=True)

  def testRegionalTableOutput(self):
    self.Run('compute instance-groups list --regions=region-1')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionInstanceGroups,
                   'List',
                   self.messages.ComputeRegionInstanceGroupsListRequest(
                       region='region-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'List',
          self.messages.ComputeRegionInstanceGroupManagersListRequest(
              maxResults=500,
              region='region-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE  NETWORK   MANAGED INSTANCES
            group-1 region-1 region           Yes     0
            group-2 region-1 region default   Yes     3
            group-3 region-1 region network-1 Yes     10
            group-4 region-1 region network-1 No      1
            """), normalize_space=True)

  def testRegionalUriOutput(self):
    self.Run('compute instance-groups list --regions=region-1 --uri')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionInstanceGroups,
                   'List',
                   self.messages.ComputeRegionInstanceGroupsListRequest(
                       region='region-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'List',
          self.messages.ComputeRegionInstanceGroupManagersListRequest(
              maxResults=500,
              region='region-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroups/group-1
            https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroups/group-2
            https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroups/group-3
            https://www.googleapis.com/compute/{0}/projects/my-project/regions/region-1/instanceGroups/group-4
            """.format(self.api)), normalize_space=True)

  def testZonalUriOutput(self):
    self.Run('compute instance-groups list --zones=zone-1 --uri')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-3
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-4
            """.format(self.api)), normalize_space=True)

  def testZonalTableOutputOnlyManaged(self):
    self.Run('compute instance-groups list --zones=zone-1 --only-managed')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE NETWORK   MANAGED INSTANCES
            group-1 zone-1   zone            Yes     0
            group-2 zone-1   zone  default   Yes     3
            group-3 zone-1   zone  network-1 Yes     10
            """), normalize_space=True)

  def testZonalTableOutputOnlyUnmanaged(self):
    self.Run('compute instance-groups list --zones=zone-1 --only-unmanaged')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE NETWORK   MANAGED INSTANCES
            group-4 zone-1   zone  network-1 No      1
            """), normalize_space=True)

  def testZonalUriOutputOnlyManaged(self):
    self.Run('compute instance-groups list --zones=zone-1 --only-managed --uri')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-2
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-3
            """.format(self.api)), normalize_space=True)

  def testZonalUriOutputOnlyUnmanaged(self):
    self.Run("""
        compute instance-groups list --zones=zone-1 --only-unmanaged --uri""")
    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroups,
                   'List',
                   self.messages.ComputeInstanceGroupsListRequest(
                       zone='zone-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              zone='zone-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-4
            """.format(self.api)), normalize_space=True)

  def testInvalidUsage(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --only-managed: At most one of --only-managed | '
        '--only-unmanaged may be specified.'):
      self.Run('compute instance-groups list --only-managed --only-unmanaged')

  def testInstanceGroupsCompleter(self):
    self.RunCompleter(
        completers.InstanceGroupsCompleter,
        expected_command=[
            'compute',
            'instance-groups',
            'unmanaged',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'group-4',
        ],
        cli=self.cli,
    )


class InstanceGroupsListAlphaTest(InstanceGroupsListTestBase):
  """Tests for alpha version of 'instance-group list' command."""

  def ApiVersion(self):
    return 'alpha'

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testRegionalTableOutput(self):
    self.Run('compute instance-groups list --regions=region-1')
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionInstanceGroups,
                   'List',
                   self.messages.ComputeRegionInstanceGroupsListRequest(
                       region='region-1',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests(
        [(self.compute.regionInstanceGroupManagers,
          'List',
          self.messages.ComputeRegionInstanceGroupManagersListRequest(
              maxResults=500,
              region='region-1',
              project='my-project'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME    LOCATION SCOPE  NETWORK   MANAGED INSTANCES
            group-1 region-1 region           Yes     0
            group-2 region-1 region default   Yes     3
            group-3 region-1 region network-1 Yes     10
            group-4 region-1 region network-1 No      1
            """), normalize_space=True)

if __name__ == '__main__':
  test_case.main()
