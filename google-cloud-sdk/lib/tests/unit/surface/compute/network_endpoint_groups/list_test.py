# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Tests for the network-endpoint-groups list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.network_endpoint_groups import test_resources
import mock


class NetworkEndpointGroupsListTest(test_base.BaseTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS

  def SetUp(self):
    self.SelectApi(self.api_version)
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    command = 'compute network-endpoint-groups list'
    return_value = (
        self.zonal_neg_test_resource + self.global_neg_test_resource +
        self.region_neg_test_resource)
    output = ("""\
        NAME   LOCATION ENDPOINT_TYPE SIZE
        my-neg1 zone-1 GCE_VM_IP_PORT 5
        my-neg2 zone-2 GCE_VM_IP_PORT 2
        my-neg3 zone-1 GCE_VM_IP_PORT 3
        my-global-neg global INTERNET_IP_PORT 1
        my-global-neg-fqdn global INTERNET_FQDN_PORT 2
        my-cloud-run-neg region-1 SERVERLESS 0
        my-app-engine-neg region-2 SERVERLESS 0
        my-cloud-function-neg region-3 SERVERLESS 0
        """)
    self.RequestAggregate(command, return_value, output)

  def testCommandOuput(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.list_json.side_effect = iter(
        [self.zonal_neg_test_resource + self.global_neg_test_resource])
    result = list(self.Run('compute network-endpoint-groups list'))
    self.list_json.assert_called_once_with(
        requests=[(self.compute.networkEndpointGroups, 'AggregatedList',
                   self._getListRequestMessage('my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.assertEqual(
        self.zonal_neg_test_resource + self.global_neg_test_resource, result)

  def testGlobalOption(self):
    command = 'compute network-endpoint-groups list --uri --global'
    return_value = self.global_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg-fqdn
        """.format(api=self.api))

    self.RequestOnlyGlobal(command, return_value, output)

  def testZonesWithNoArgs(self):
    command = 'compute network-endpoint-groups list --uri --zones ""'
    return_value = self.zonal_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-2/networkEndpointGroups/my-neg2
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg3
        """.format(api=self.api))

    self.RequestAggregate(command, return_value, output)

  def testOneZone(self):
    command = 'compute network-endpoint-groups list --uri --zones zone-1'
    return_value = self.zonal_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg3
        """.format(api=self.api))

    self.RequestOneZone(command, return_value, output)

  def testMultipleZones(self):
    command = 'compute network-endpoint-groups list --uri --zones zone-1,zone-2'
    return_value = self.zonal_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-2/networkEndpointGroups/my-neg2
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg3
        """.format(api=self.api))

    self.RequestTwoZones(command, return_value, output)

  def testZonesAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions | --zones '
        'may be specified'):
      self.Run("""\
          compute network-endpoint-groups list --zones '' --global
          """)
    self.CheckRequests()

  def testPositionalArgsWithSimpleNames(self):
    command = """
        compute network-endpoint-groups list
          my-neg1 my-global-neg my-cloud-run-neg
          --uri
        """
    return_value = self.zonal_neg_test_resource + self.global_neg_test_resource + self.region_neg_test_resource
    output = """\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
        """.format(api=self.api)

    self.RequestAggregate(command, return_value, output)

  def testPositionalArgsWithUris(self):
    command = """
        compute network-endpoint-groups list
          https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
          https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
          https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
          --uri
        """.format(api=self.api)
    return_value = self.zonal_neg_test_resource \
                   + self.global_neg_test_resource \
                   + self.region_neg_test_resource
    output = """\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
        """.format(api=self.api)

    self.RequestAggregate(command, return_value, output)

  def testPositionalArgsWithSimpleNamesAndZonesFlag(self):
    command = """
        compute network-endpoint-groups list
          my-neg1 my-neg2 my-global-neg my-cloud-run-neg
          --zones zone-1,zone-2
          --uri
        """
    return_value = self.zonal_neg_test_resource
    output = """\
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-1/networkEndpointGroups/my-neg1
        https://compute.googleapis.com/compute/{api}/projects/my-project/zones/zone-2/networkEndpointGroups/my-neg2
        """.format(api=self.api)

    self.RequestTwoZones(command, return_value, output)

  def testPositionalArgsWithSimpleNamesAndGlobalFlag(self):
    command = """
        compute network-endpoint-groups list
          my-neg1 my-neg2 my-global-neg my-global-neg-fqdn my-cloud-run-neg
          --global
          --uri
        """
    return_value = self.global_neg_test_resource
    output = """\
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/global/networkEndpointGroups/my-global-neg-fqdn
        """.format(api=self.api)

    self.RequestOnlyGlobal(command, return_value, output)

  def RequestOnlyGlobal(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.globalNetworkEndpointGroups, 'List',
                   self.messages.ComputeGlobalNetworkEndpointGroupsListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestAggregate(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)

    self.list_json.assert_called_once_with(
        requests=[
            (self.compute.networkEndpointGroups, 'AggregatedList',
             self._getListRequestMessage('my-project'))
        ],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestOneZone(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.networkEndpointGroups, 'List',
                   self.messages.ComputeNetworkEndpointGroupsListRequest(
                       project='my-project', zone='zone-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoZones(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.networkEndpointGroups, 'List',
                   self.messages.ComputeNetworkEndpointGroupsListRequest(
                       project='my-project', zone='zone-1')),
                  (self.compute.networkEndpointGroups, 'List',
                   self.messages.ComputeNetworkEndpointGroupsListRequest(
                       project='my-project', zone='zone-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def testOneRegion(self):
    command = 'compute network-endpoint-groups list --uri --regions region-1'
    return_value = self.region_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
    """.format(api=self.api))

    self.RequestOneRegion(command, return_value, output)

  def testMultipleRegions(self):
    command = ('compute network-endpoint-groups list --uri '
               '--regions region-1,region-2')
    return_value = self.region_neg_test_resource
    output = ("""\
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-2/networkEndpointGroups/my-app-engine-neg
    """.format(api=self.api))

    self.RequestTwoRegions(command, return_value, output)

  def testRegionsAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions | --zones '
        'may be specified'):
      self.Run("""\
          compute network-endpoint-groups list --regions '' --global
          """)
    self.CheckRequests()

  def testPositionalArgsWithSimpleNamesAndRegionsFlag(self):
    command = """
        compute network-endpoint-groups list
          my-neg1 my-neg2 my-global-neg my-global-neg-fqdn
          my-cloud-run-neg my-app-engine-neg my-cloud-function-neg
          --regions region-1,region-2
          --uri
        """
    return_value = self.region_neg_test_resource
    output = """\
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-1/networkEndpointGroups/my-cloud-run-neg
        https://compute.googleapis.com/compute/{api}/projects/my-project/regions/region-2/networkEndpointGroups/my-app-engine-neg
    """.format(api=self.api)

    self.RequestTwoRegions(command, return_value, output)

  def RequestOneRegion(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionNetworkEndpointGroups, 'List',
                   self.messages.ComputeRegionNetworkEndpointGroupsListRequest(
                       project='my-project', region='region-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def RequestTwoRegions(self, command, return_value, output):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(return_value)
    ]
    self.Run(command)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionNetworkEndpointGroups, 'List',
                   self.messages.ComputeRegionNetworkEndpointGroupsListRequest(
                       project='my-project', region='region-1')),
                  (self.compute.regionNetworkEndpointGroups, 'List',
                   self.messages.ComputeRegionNetworkEndpointGroupsListRequest(
                       project='my-project', region='region-2'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(textwrap.dedent(output), normalize_space=True)

  def _getListRequestMessage(self, project):
    return self.messages.ComputeNetworkEndpointGroupsAggregatedListRequest(
        project=project, includeAllScopes=True)


class BetaNetworkEndpointGroupsListTest(NetworkEndpointGroupsListTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS_BETA
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS_BETA
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS_BETA


class AlphaNetworkEndpointGroupsListTest(BetaNetworkEndpointGroupsListTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'
    self.zonal_neg_test_resource = test_resources.NETWORK_ENDPOINT_GROUPS_ALPHA
    self.global_neg_test_resource = test_resources.GLOBAL_NETWORK_ENDPOINT_GROUPS_ALPHA
    self.region_neg_test_resource = test_resources.REGION_NETWORK_ENDPOINT_GROUPS_ALPHA

  def _getListRequestMessage(self, project):
    request_params = {'includeAllScopes': True}
    if hasattr(self.messages.ComputeNetworkEndpointGroupsAggregatedListRequest,
               'returnPartialSuccess'):
      request_params['returnPartialSuccess'] = True

    return self.messages.ComputeNetworkEndpointGroupsAggregatedListRequest(
        project=project, **request_params)


if __name__ == '__main__':
  test_case.main()
