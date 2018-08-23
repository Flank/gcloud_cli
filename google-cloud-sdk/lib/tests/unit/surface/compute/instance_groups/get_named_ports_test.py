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
"""Tests for the instance-groups get-named-ports subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class InstanceGroupsGetNamedPortsGaTest(test_base.BaseTest):

  def SetUp(self):
    api_version = 'v1'
    self.SelectApi(api_version)

    def _MockMakeRequests(requests, batch_url, *unused_args, **unused_kwargs):
      _ = batch_url, unused_args, unused_kwargs
      if len(requests) != 1:
        self.fail('expected to send single request, sent: ' + str(requests))
      service = requests[0][0]
      verb = requests[0][1]
      if verb != 'Get':
        self.fail('expected GET verb, sent: ' + str(verb))
      if service == self.compute.instanceGroups:
        return [test_resources.MakeInstanceGroups(self.messages,
                                                  api_version)[0]]
      elif service == self.compute.regionInstanceGroups:
        return [test_resources.MakeInstanceGroups(self.messages,
                                                  api_version,
                                                  scope_name='region-1',
                                                  scope_type='region')[0]]
      else:
        self.fail('expected IG request, sent: ' + str(service))
    self.make_requests.side_effect = _MockMakeRequests

  def testGetPortsForGroupZonal(self):
    self.Run("""
        compute instance-groups get-named-ports group-1
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

  def testGetPortsForGroupByUriZonal(self):
    self.Run("""
        compute instance-groups get-named-ports
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
        [test_resources.MakeInstanceGroups(
            self.messages, self.resource_api)[1]],
    ])
    self.Run("""
        compute instance-groups get-named-ports group-1
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
        compute instance-groups get-named-ports group-1
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

  def testGetPortsLimit(self):
    self.Run("""
        compute instance-groups get-named-ports group-1
          --zone central2-a
          --limit 1
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

  def testGetPortsForGroupRegional(self):
    self.Run("""
        compute instance-groups get-named-ports group-1
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

  def testGetPortsForGroupByUriRegional(self):
    self.Run("""
        compute instance-groups get-named-ports
          {0}/projects/my-project/regions/central2/instanceGroups/group-1
        """.format(self.compute_uri))
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

  def testGetPortsScopePromptingZonalRegional(self):
     # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [self.messages.Region(name='central2')],
        [self.messages.Zone(name='central2-a'),
         self.messages.Zone(name='central2-b')],
        [test_resources.MakeInstanceGroups(self.messages,
                                           self.api,
                                           scope_name='region-1',
                                           scope_type='region')[0]],
    ])
    self.WriteInput('1\n')
    self.Run("""
        compute instance-groups get-named-ports group-1
        """)
    self.CheckRequests(
        self.regions_list_request,
        self.zones_list_request,
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


if __name__ == '__main__':
  test_case.main()
