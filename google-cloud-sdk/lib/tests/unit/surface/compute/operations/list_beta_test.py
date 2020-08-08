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
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources as compute_resources
from tests.lib.surface.compute.operations import test_resources
import mock

beta_messages = core_apis.GetMessagesModule('compute', 'beta')


class OperationsListBetaTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi('beta')
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testSimpleCaseBeta(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            (test_resources.BETA_GLOBAL_OPERATIONS +
             test_resources.BETA_REGIONAL_OPERATIONS +
             test_resources.BETA_ZONAL_OPERATIONS)),
    ]

    self.Run("""
        compute operations list --uri
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'AggregatedList',
                   beta_messages.ComputeGlobalOperationsAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/beta/projects/my-project/global/operations/operation-1
            https://compute.googleapis.com/compute/beta/projects/my-project/regions/region-1/operations/operation-2
            https://compute.googleapis.com/compute/beta/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testWithGlobalFlag(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_GLOBAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --global
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'List',
                   beta_messages.ComputeGlobalOperationsListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/beta/projects/my-project/global/operations/operation-1
            """))

  def testWithManyArgumentRegionsFlag(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_REGIONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --regions region-1,region-2
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       region='region-1',
                       project='my-project')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       region='region-2',
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/beta/projects/my-project/regions/region-1/operations/operation-2
            """))

  def testWithNoArgumentZonesFlag(self):
    self.make_requests.side_effect = [compute_resources.BETA_ZONES]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --uri --zones ''
        """)

    self.CheckRequests(
        self.zones_list_request_beta,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/beta/projects/my-project/zones/zone-1/operations/operation-3
            """))

  def testTabularOutputBeta(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            (test_resources.BETA_GLOBAL_OPERATIONS +
             test_resources.BETA_REGIONAL_OPERATIONS +
             test_resources.BETA_ZONAL_OPERATIONS)),
    ]

    self.Run("""
        compute operations list
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        TYPE   TARGET                       HTTP_STATUS STATUS  TIMESTAMP
            operation-1 insert resource-1                   200         DONE    2014-09-04T09:55:33.679-07:00
            operation-2 insert region-1/resource/resource-2 200         DONE    2014-09-04T09:53:33.679-07:00
            operation-3 insert zone-1/resource/resource-3   409         DONE    2014-09-04T09:56:33.679-07:00
            """), normalize_space=True)

  def testRegionsAndGlobal(self):
    self.make_requests.side_effect = [compute_resources.BETA_REGIONS]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            (test_resources.BETA_GLOBAL_OPERATIONS +
             test_resources.BETA_REGIONAL_OPERATIONS))
    ]
    self.Run("""
      compute operations list --regions '' --global
      """)

    self.CheckRequests(
        self.regions_list_request_beta,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'List',
                   beta_messages.ComputeGlobalOperationsListRequest(
                       project='my-project')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-2')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-3'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testRegionsAndZones(self):
    self.make_requests.side_effect = [
        compute_resources.REGIONS,
        compute_resources.BETA_ZONES,
    ]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_REGIONAL_OPERATIONS +
            test_resources.BETA_ZONAL_OPERATIONS)
    ]
    self.Run("""
      compute operations list --regions '' --zones ''
      """)

    self.CheckRequests(
        self.regions_list_request_beta,
        self.zones_list_request_beta,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-2')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-3')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testRegionsAndSpecificZones(self):
    self.make_requests.side_effect = [compute_resources.BETA_REGIONS]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_REGIONAL_OPERATIONS +
            test_resources.BETA_ZONAL_OPERATIONS)
    ]
    self.Run("""
      compute operations list --regions '' --zones us-central1-a,us-central1-b
      """)

    self.CheckRequests(
        self.regions_list_request_beta,
    )

    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-1')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-2')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='region-3')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testZonesAndGlobal(self):
    self.make_requests.side_effect = [compute_resources.BETA_ZONES]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_GLOBAL_OPERATIONS +
            test_resources.BETA_ZONAL_OPERATIONS),
    ]
    self.Run("""
      compute operations list --zones '' --global
      """)
    self.CheckRequests(
        self.zones_list_request_beta,
    )
    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'List',
                   beta_messages.ComputeGlobalOperationsListRequest(
                       project='my-project')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='europe-west1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testOneZonesAndGlobal(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_GLOBAL_OPERATIONS +
            test_resources.BETA_ZONAL_OPERATIONS),
    ]
    self.Run("""
      compute operations list --zones us-central1-a --global
      """)
    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'List',
                   beta_messages.ComputeGlobalOperationsListRequest(
                       project='my-project')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testComplexTabularOutputBeta(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.BETA_GLOBAL_OPERATIONS +
            test_resources.BETA_REGIONAL_OPERATIONS +
            test_resources.BETA_ZONAL_OPERATIONS),
    ]

    self.Run("""
        compute operations list --zones us-central1-a,us-central1-b --regions us-central1 --global
        """)
    self.list_json.assert_called_once_with(
        requests=[(self.compute_beta.globalOperations,
                   'List',
                   beta_messages.ComputeGlobalOperationsListRequest(
                       project='my-project')),
                  (self.compute_beta.regionOperations,
                   'List',
                   beta_messages.ComputeRegionOperationsListRequest(
                       project='my-project',
                       region='us-central1')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-a')),
                  (self.compute_beta.zoneOperations,
                   'List',
                   beta_messages.ComputeZoneOperationsListRequest(
                       project='my-project',
                       zone='us-central1-b'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME        TYPE   TARGET                       HTTP_STATUS STATUS TIMESTAMP
            operation-1 insert resource-1                   200         DONE   2014-09-04T09:55:33.679-07:00
            operation-2 insert region-1/resource/resource-2 200         DONE   2014-09-04T09:53:33.679-07:00
            operation-3 insert zone-1/resource/resource-3   409         DONE   2014-09-04T09:56:33.679-07:00
            """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
