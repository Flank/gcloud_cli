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
"""Tests for the instance-groups unmanaged describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


class UnmanagedInstanceGroupsDescribeTest(test_base.BaseTest,
                                          test_case.WithOutputCapture):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(self.messages, API_VERSION)[0]],
        [test_resources.MakeInstanceGroupManagers(API_VERSION)[0]],
    ])

  def testShowManaged(self):
    self.Run('compute instance-groups unmanaged describe group-1 --zone zone-1')

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test instance group
            fingerprint: MTIz
            instanceGroupManagerUri: https://compute.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroupManagers/group-1
            isManaged: Yes
            name: group-1
            namedPorts:
            - name: serv-1
              port: 1111
            - name: serv-2
              port: 2222
            - name: serv-3
              port: 3333
            selfLink: https://compute.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            size: 0
            zone: https://compute.googleapis.com/compute/{0}/projects/my-project/zones/zone-1
            """.format(API_VERSION)))

  def testShowNotManaged(self):
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(self.messages, API_VERSION)[0]],
        [],
    ])
    self.Run("""
        compute instance-groups unmanaged describe group-1
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instanceGroupManagers,
          'List',
          self.messages.ComputeInstanceGroupManagersListRequest(
              maxResults=500,
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            description: Test instance group
            fingerprint: MTIz
            isManaged: No
            name: group-1
            namedPorts:
            - name: serv-1
              port: 1111
            - name: serv-2
              port: 2222
            - name: serv-3
              port: 3333
            selfLink: https://compute.googleapis.com/compute/{0}/projects/my-project/zones/zone-1/instanceGroups/group-1
            size: 0
            zone: https://compute.googleapis.com/compute/{0}/projects/my-project/zones/zone-1
            """.format(API_VERSION)))


if __name__ == '__main__':
  test_case.main()
