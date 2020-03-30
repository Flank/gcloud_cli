# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for features of list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock

API_VERSION = 'v1'


class InstanceGroupManagersListTest(test_base.BaseTest):

  def SetUp(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def SetupMockGetZonalResources(self, autoscalers):
    def _MockGetZonalResources(service, project, requested_zones, filter_expr,
                               http, batch_url, errors):
      _ = project, requested_zones, filter_expr, http, batch_url, errors
      if 'InstanceGroupsService' in str(type(service)):
        return test_resources.MakeInstanceGroups(self.messages, API_VERSION)
      return None

    self.SelectApi(API_VERSION)
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetZonalResources',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_zonal_resources = lister_patcher.start()
    self.mock_get_zonal_resources.side_effect = _MockGetZonalResources
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.MakeInstanceGroupManagers(api=API_VERSION))
    ]
    self.make_requests.side_effect = [
        autoscalers,
    ]

  def SetupMockGetRegionalResources(self, autoscalers):
    def _MockGetRegionalResources(service, project, requested_regions,
                                  filter_expr, http, batch_url, errors):
      _ = project, requested_regions, filter_expr, http, batch_url, errors
      if 'RegionInstanceGroupsService' in str(type(service)):
        return test_resources.MakeInstanceGroups(
            msgs=self.messages, api=API_VERSION,
            scope_name='region-1', scope_type='region')
      return None

    self.SelectApi(API_VERSION)
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetRegionalResources',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_regional_resources = lister_patcher.start()
    self.mock_get_regional_resources.side_effect = _MockGetRegionalResources

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.MakeInstanceGroupManagers(
                api=API_VERSION, scope_name='region-1', scope_type='region'))
    ]
    self.make_requests.side_effect = [autoscalers]

  def testZonalTableOutput(self):
    self.SetupMockGetZonalResources(
        [test_resources.MakeAutoscalers(API_VERSION)[0]])
    self.Run('compute instance-groups managed list --zones=zone-1')
    self.mock_get_zonal_resources.assert_any_call(
        service=self.compute.instanceGroups,
        project='my-project',
        requested_zones=set(['zone-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME    LOCATION SCOPE BASE_INSTANCE_NAME   SIZE TARGET_SIZE INSTANCE_TEMPLATE AUTOSCALED
        group-1 zone-1   zone  test-instance-name-1 0    1           template-1        yes
        group-2 zone-1   zone  test-instance-name-2 3    10          template-2        no
        group-3 zone-1   zone  test-instance-name-3 10   1           template-2        no
        """), normalize_space=True)
    self.AssertErrEquals("""\
    WARNING: Flag `--zones` is deprecated. Use `--filter="zone:( ZONE ...  )"` instead.
    For example `--filter="zone:( europe-west1-b europe-west1-c )"`.
    """, normalize_space=True)

  def testRegionalTableOutput(self):
    self.SetupMockGetRegionalResources([
        test_resources.MakeAutoscalers(api=API_VERSION,
                                       scope_name='region-1',
                                       scope_type='region')[0]])
    self.Run('compute instance-groups managed list --regions=region-1,region-2')
    self.mock_get_regional_resources.assert_any_call(
        service=self.compute.regionInstanceGroups,
        project='my-project',
        requested_regions=set(['region-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME    LOCATION SCOPE  BASE_INSTANCE_NAME   SIZE TARGET_SIZE INSTANCE_TEMPLATE AUTOSCALED
        group-1 region-1 region test-instance-name-1 0    1           template-1        yes
        group-2 region-1 region test-instance-name-2 3    10          template-2        no
        group-3 region-1 region test-instance-name-3 10   1           template-2        no
        """), normalize_space=True)
    self.AssertErrEquals("""\
    WARNING: Flag `--regions` is deprecated. Use `--filter="region:( REGION ... )"` instead.
    For example `--filter="region:( europe-west1 europe-west2 )"`.
    """, normalize_space=True)

  def testMultiScopeTableOutput(self):
    self.SetupMockGetZonalResources(
        [test_resources.MakeAutoscalers(API_VERSION)[0]])
    self.Run('compute instance-groups managed list --zones zone-1,zone-2')
    self.mock_get_zonal_resources.assert_any_call(
        service=self.compute.instanceGroups,
        project='my-project',
        requested_zones=set(['zone-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.list_json.assert_called_once_with(
        requests=[(self.compute.instanceGroupManagers,
                   'List',
                   self.messages.ComputeInstanceGroupManagersListRequest(
                       project='my-project',
                       zone='zone-1')),
                  (self.compute.instanceGroupManagers,
                   'List',
                   self.messages.ComputeInstanceGroupManagersListRequest(
                       project='my-project',
                       zone='zone-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.CheckRequests(
        [(self.compute.autoscalers,
          'List',
          self.messages.ComputeAutoscalersListRequest(
              maxResults=500,
              project='my-project',
              zone='zone-1'))
        ],
    )

    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME    LOCATION SCOPE  BASE_INSTANCE_NAME   SIZE TARGET_SIZE INSTANCE_TEMPLATE AUTOSCALED
        group-1 zone-1   zone   test-instance-name-1 0    1           template-1        yes
        group-2 zone-1   zone   test-instance-name-2 3    10          template-2        no
        group-3 zone-1   zone   test-instance-name-3 10   1           template-2        no
        """), normalize_space=True)
    self.AssertErrEquals("""\
    WARNING: Flag `--zones` is deprecated. Use `--filter="zone:( ZONE ... )"` instead.
    For example `--filter="zone:( europe-west1-b europe-west1-c )"`.
    """, normalize_space=True)

  def testAggregatedTableOutput(self):
    self.SetupMockGetRegionalResources([])
    self.SetupMockGetZonalResources([])
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.MakeInstanceGroupManagers(
                api=API_VERSION, scope_name='zone-1', scope_type='zone') +
            test_resources.MakeInstanceGroupManagers(
                api=API_VERSION, scope_name='region-1', scope_type='region'))
    ]
    self.make_requests.side_effect = [
        [test_resources.MakeAutoscalers(api=API_VERSION,
                                        scope_name='region-1',
                                        scope_type='region')[0],
         test_resources.MakeAutoscalers(api=API_VERSION,
                                        scope_name='zone-1',
                                        scope_type='zone')[0]]]

    self.Run('compute instance-groups managed list')
    self.mock_get_zonal_resources.assert_any_call(
        service=self.compute.instanceGroups,
        project='my-project',
        requested_zones=set(['zone-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.mock_get_regional_resources.assert_any_call(
        service=self.compute.regionInstanceGroups,
        project='my-project',
        requested_regions=set(['region-1']),
        filter_expr=None,
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
        NAME    LOCATION SCOPE  BASE_INSTANCE_NAME   SIZE TARGET_SIZE INSTANCE_TEMPLATE AUTOSCALED
        group-1 zone-1   zone   test-instance-name-1 0    1           template-1        yes
        group-2 zone-1   zone   test-instance-name-2 3    10          template-2        no
        group-3 zone-1   zone   test-instance-name-3 10   1           template-2        no
        group-1 region-1 region test-instance-name-1 0    1           template-1        yes
        group-2 region-1 region test-instance-name-2 3    10          template-2        no
        group-3 region-1 region test-instance-name-3 10   1           template-2        no
        """), normalize_space=True)
    self.AssertErrEquals('')

  def testPageSize(self):
    self.Run('compute instance-groups managed list --page-size 2')

    self.list_json.assert_called_once_with(
        requests=[
            (self.compute.instanceGroupManagers, 'AggregatedList',
             self.messages.ComputeInstanceGroupManagersAggregatedListRequest(
                 maxResults=None, project='my-project', includeAllScopes=True))
        ],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.CheckRequests([])


if __name__ == '__main__':
  test_case.main()
