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

"""Tests for the global-operations describe subcommand."""

import textwrap

from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class OperationsDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testWithGlobalFlag(self):
    self.make_requests.side_effect = iter([
        [test_resources.GLOBAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe operation-1 --global
        """)

    self.CheckRequests(
        [(self.compute_v1.globalOperations,
          'Get',
          self.messages.ComputeGlobalOperationsGetRequest(
              operation='operation-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            insertTime: '2014-09-04T09:55:33.679-07:00'
            name: operation-1
            operationType: insert
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/operations/operation-1
            status: DONE
            targetLink: https://www.googleapis.com/compute/v1/projects/my-project/resource/resource-1
            """))

  def testWithRegionFlag(self):
    self.make_requests.side_effect = iter([
        [test_resources.REGIONAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe operation-2 --region region-1
        """)

    self.CheckRequests(
        [(self.compute_v1.regionOperations,
          'Get',
          self.messages.ComputeRegionOperationsGetRequest(
              operation='operation-2',
              region='region-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            insertTime: '2014-09-04T09:53:33.679-07:00'
            name: operation-2
            operationType: insert
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            status: DONE
            targetLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/resource/resource-2
            """))

  def testWithZoneFlag(self):
    self.make_requests.side_effect = iter([
        [test_resources.ZONAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe operation-3 --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.zoneOperations,
          'Get',
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-3',
              zone='zone-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            httpErrorStatusCode: 409
            insertTime: '2014-09-04T09:56:33.679-07:00'
            name: operation-3
            operationType: insert
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
            status: DONE
            targetLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/resource/resource-3
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))

  def testUriSupportForGlobalOperations(self):
    self.make_requests.side_effect = iter([
        [test_resources.GLOBAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe
          https://www.googleapis.com/compute/v1/projects/my-project/global/operations/operation-1
        """)

    self.CheckRequests(
        [(self.compute_v1.globalOperations,
          'Get',
          self.messages.ComputeGlobalOperationsGetRequest(
              operation='operation-1',
              project='my-project'))])

  def testUriSupportForRegionalOperations(self):
    self.make_requests.side_effect = iter([
        [test_resources.REGIONAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe
          https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
        """)

    self.CheckRequests(
        [(self.compute_v1.regionOperations,
          'Get',
          self.messages.ComputeRegionOperationsGetRequest(
              operation='operation-2',
              region='region-1',
              project='my-project'))])

  def testUriSupportForZonalOperation(self):
    self.make_requests.side_effect = iter([
        [test_resources.ZONAL_OPERATIONS[0]],
    ])

    self.Run("""
        compute operations describe
          https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/operations/operation-3
        """)

    self.CheckRequests(
        [(self.compute_v1.zoneOperations,
          'Get',
          self.messages.ComputeZoneOperationsGetRequest(
              operation='operation-3',
              zone='zone-1',
              project='my-project'))])

  def testUriSupportWithIllegalType(self):
    with self.assertRaises(resources.WrongResourceCollectionException):
      self.Run("""
          compute operations describe
            https://www.googleapis.com/compute/v1/projects/my-project/global/networks/network-1
          """)

  def testUriSupportWithIllegalTypeAlpha(self):
    with self.assertRaises(resources.WrongResourceCollectionException):
      self.Run("""
          alpha compute operations describe
            https://www.googleapis.com/compute/alpha/projects/my-project/global/networks/network-1
          """)

  def testDefaultScope(self):
    self.make_requests.side_effect = iter([
        [test_resources.REGIONAL_OPERATIONS[0]],
    ])
    self.Run('compute operations describe operation-1')
    self.CheckRequests(
        [(self.compute_v1.globalOperations,
          'Get',
          self.messages.ComputeGlobalOperationsGetRequest(
              operation='operation-1',
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            insertTime: '2014-09-04T09:53:33.679-07:00'
            name: operation-2
            operationType: insert
            region: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/operations/operation-2
            status: DONE
            targetLink: https://www.googleapis.com/compute/v1/projects/my-project/regions/region-1/resource/resource-2
            """))


if __name__ == '__main__':
  test_case.main()
