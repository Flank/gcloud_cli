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
"""Tests for the instance-groups managed get-named-ports subcommand."""
import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'v1'


class InstanceGroupsGetNamedPortsZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(self.messages, API_VERSION)[0]],
    ])

  def testGetPortsForGroup(self):
    self.Run("""
        compute instance-groups managed get-named-ports group-1
        --zone central2-a
        """)
    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            serv-2 2222
            serv-3 3333
            """), normalize_space=True)

  def testGetPortsForGroupByUri(self):
    self.Run("""
        compute instance-groups managed get-named-ports
          {0}/projects/my-project/zones/central2-a/instanceGroups/group-1
        """.format(self.compute_uri))
    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            serv-2 2222
            serv-3 3333
            """), normalize_space=True)

  def testGetPortsSingleRow(self):
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(self.messages, API_VERSION)[1]],
    ])
    self.Run("""
        compute instance-groups managed get-named-ports group-1
          --zone central2-a
        """)
    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            """), normalize_space=True)

  def testGetPortsSorted(self):
    self.Run("""
        compute instance-groups managed get-named-ports group-1
          --zone central2-a
          --sort-by ~NAME
        """)
    self.CheckRequests(
        [(self.compute.instanceGroups,
          'Get',
          self.messages.ComputeInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              zone='central2-a'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-3 3333
            serv-2 2222
            serv-1 1111
            """), normalize_space=True)


class InstanceGroupsGetNamedPortsRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(msgs=self.messages,
                                           api=API_VERSION,
                                           scope_type='region',
                                           scope_name='central2')[0]],
    ])

  def testGetPortsForGroup(self):
    self.Run("""
        compute instance-groups managed get-named-ports group-1
        --region central2
        """)
    self.CheckRequests(
        [(self.compute.regionInstanceGroups,
          'Get',
          self.messages.ComputeRegionInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              region='central2'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            serv-2 2222
            serv-3 3333
            """), normalize_space=True)

  def testGetPortsForGroupByUri(self):
    self.Run("""
        compute instance-groups managed get-named-ports
          https://www.googleapis.com/compute/{0}/projects/my-project/regions/central2/instanceGroups/group-1
        """.format(API_VERSION))
    self.CheckRequests(
        [(self.compute.regionInstanceGroups,
          'Get',
          self.messages.ComputeRegionInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              region='central2'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            serv-2 2222
            serv-3 3333
            """), normalize_space=True)

  def testGetPortsSingleRow(self):
    self.make_requests.side_effect = iter([
        [test_resources.MakeInstanceGroups(msgs=self.messages,
                                           api=API_VERSION,
                                           scope_type='region',
                                           scope_name='central2')[1]],
    ])
    self.Run("""
        compute instance-groups managed get-named-ports group-1
          --region central2
        """)
    self.CheckRequests(
        [(self.compute.regionInstanceGroups,
          'Get',
          self.messages.ComputeRegionInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              region='central2'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-1 1111
            """), normalize_space=True)

  def testGetPortsSorted(self):
    self.Run("""
        compute instance-groups managed get-named-ports group-1
          --region central2
          --sort-by ~NAME
        """)
    self.CheckRequests(
        [(self.compute.regionInstanceGroups,
          'Get',
          self.messages.ComputeRegionInstanceGroupsGetRequest(
              instanceGroup='group-1',
              project='my-project',
              region='central2'))],
    )
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME   PORT
            serv-3 3333
            serv-2 2222
            serv-1 1111
            """), normalize_space=True)


if __name__ == '__main__':
  test_case.main()
