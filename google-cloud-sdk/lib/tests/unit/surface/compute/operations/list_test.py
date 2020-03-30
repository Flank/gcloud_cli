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
"""Tests for the global-operations list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock

messages = core_apis.GetMessagesModule('compute', 'v1')


class OperationsListTest(test_base.BaseTest):

  def SetUp(self):
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testSimpleCase(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.GLOBAL_OPERATIONS +
                                            test_resources.REGIONAL_OPERATIONS +
                                            test_resources.ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalOperations,
                   'AggregatedList',
                   messages.ComputeGlobalOperationsAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/operations/operation-1
            https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testWithGlobalFlag(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.GLOBAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --global
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalOperations,
                   'List',
                   messages.ComputeGlobalOperationsListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/operations/operation-1
            """))

  def testWithNoArgumentRegionsFlag(self):
    self.make_requests.side_effect = [
        test_resources.REGIONS,
    ]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.REGIONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --regions ''
        """)

    self.CheckRequests(
        self.regions_list_request,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.regionOperations,
                   'List',
                   messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute_v1.regionOperations,
                   'List',
                   messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-2')),
                  (self.compute_v1.regionOperations,
                   'List',
                   messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-3'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            """))

  def testWithManyArgumentRegionsFlag(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.REGIONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --regions region-1,region-2
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.regionOperations,
                   'List',
                   messages.ComputeRegionOperationsListRequest(
                       region='region-1',
                       project='my-project')),
                  (self.compute_v1.regionOperations,
                   'List',
                   messages.ComputeRegionOperationsListRequest(
                       region='region-2',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            """))

  def testWithNoArgumentZonesFlag(self):
    self.make_requests.side_effect = [
        test_resources.ZONES,
    ]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --zones ''
        """)

    self.CheckRequests(
        self.zones_list_request,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b')),
                  (self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-a')),
                  (self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testWithManyArgumentZonesFlag(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --zones zone-1,zone-2
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       zone='zone-1',
                       project='my-project')),
                  (self.compute_v1.zoneOperations,
                   'List',
                   messages.ComputeZoneOperationsListRequest(
                       zone='zone-2',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testNameRegexes(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.GLOBAL_OPERATIONS +
                                            test_resources.REGIONAL_OPERATIONS +
                                            test_resources.ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list
          --uri
          --regexp "operation-1|operation-.*"
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalOperations,
                   'AggregatedList',
                   messages.ComputeGlobalOperationsAggregatedListRequest(
                       filter='name eq ".*(^operation-1|operation-.*$).*"',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/operations/operation-1
            https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            https://compute.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testTabularOutput(self):
    self.list_json.side_effect = iter([
        resource_projector.MakeSerializable(test_resources.GLOBAL_OPERATIONS +
                                            test_resources.REGIONAL_OPERATIONS +
                                            test_resources.ZONAL_OPERATIONS),
    ])

    self.Run("""
        compute operations list
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        TYPE   TARGET                       HTTP_STATUS STATUS TIMESTAMP
            operation-1 insert resource-1                   200         DONE   2014-09-04T09:55:33.679-07:00
            operation-2 insert region-1/resource/resource-2 200         DONE   2014-09-04T09:53:33.679-07:00
            operation-3 insert zone-1/resource/resource-3   409         DONE   2014-09-04T09:56:33.679-07:00
            """), normalize_space=True)

  def testWithPositionalArgs(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(test_resources.GLOBAL_OPERATIONS +
                                            test_resources.REGIONAL_OPERATIONS +
                                            test_resources.ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list
          operation-2
          --uri
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalOperations,
                   'AggregatedList',
                   messages.ComputeGlobalOperationsAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            """))

  def testRegionsAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions | --zones '
        'may be specified.'):
      self.Run("""
          compute operations list --regions '' --global
          """)

    self.CheckRequests()

  def testRegionsAndZones(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --regions: At most one of --global | --regions | --zones '
        'may be specified.'):
      self.Run("""
          compute operations list --regions '' --zones ''
          """)

    self.CheckRequests()

  def testZonesAndGlobal(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --regions | --zones '
        'may be specified.'):
      self.Run("""
          compute operations list --zones '' --global
          """)

    self.CheckRequests()

  def testLimitAndFilter(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable([
            messages.Operation(
                name='operation-2',
                status=messages.Operation.StatusValueValuesEnum.DONE,
                operationType='insert',
                insertTime='2014-09-04T09:55:33.679-07:00',
                selfLink=(
                    'https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'global/operations/operation-2'),
                targetLink=(
                    'https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'resource/resource-2')),
            messages.Operation(
                name='operation-2',
                status=messages.Operation.StatusValueValuesEnum.DONE,
                operationType='insert',
                insertTime='2014-09-04T09:55:33.679-07:00',
                selfLink=(
                    'https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'global/operations/operation-3'),
                targetLink=(
                    'https://compute.googleapis.com/compute/v1/projects/my-project/'
                    'resource/resource-3')),
        ])
    ]

    self.Run("""
        compute operations list
          --uri
          --filter "name = operation-2"
          --limit 1
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_v1.globalOperations,
                   'AggregatedList',
                   messages.ComputeGlobalOperationsAggregatedListRequest(
                       filter='name eq ".*\\boperation\\-2\\b.*"',
                       maxResults=None,
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/v1/projects/my-project/global/operations/operation-2
            """))


if __name__ == '__main__':
  test_case.main()
