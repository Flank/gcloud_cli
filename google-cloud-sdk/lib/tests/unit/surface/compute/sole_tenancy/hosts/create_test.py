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
"""Tests for the sole-tenancy hosts create subcommand."""
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class HostsCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testDefaultOptionsWithSingleHost(self):
    self.make_requests.side_effect = [[
        self.messages.Host(
            name='host-1',
            zone='central2-a',
            instances=[],
            status=self.messages.Host.StatusValueValuesEnum.READY)
    ]]

    self.Run("""
        compute sole-tenancy hosts create host-1 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-1'),
              project='my-project',
              zone='central2-a'))],
    )

    # Check default output formatting
    self.AssertOutputEquals("""\
    NAME    ZONE        INSTANCES  STATUS
    host-1  central2-a  0          READY
    """, normalize_space=True)

  def testDefaultOptionsWithMultipleHosts(self):
    self.Run("""
        compute sole-tenancy hosts create host-1 host-2 host-3 --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-1'),
              project='my-project',
              zone='central2-a')),
         (self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-2'),
              project='my-project',
              zone='central2-a')),
         (self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-3'),
              project='my-project',
              zone='central2-a'))],
    )

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central2-a'),
            self.messages.Zone(name='central2-b'),
        ],
        [
            self.messages.Zone(name='central2-a'),
        ],

        [],
    ])
    self.Run("""
        compute sole-tenancy hosts create host-1
        """)

    self.CheckRequests(
        [(self.compute.zones,
          'List',
          self.messages.ComputeZonesListRequest(
              project='my-project',
              maxResults=500))],

        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-1'),
              project='my-project',
              zone='central2-b'))],
    )
    self.AssertErrContains('host-1')
    self.AssertErrContains('central2-a')
    self.AssertErrContains('central2-b')

  def testUriSupport(self):
    self.Run("""
        compute sole-tenancy hosts create {compute_uri}/projects/my-project/zones/central2-a/hosts/host-1
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(name='host-1'),
              project='my-project',
              zone='central2-a'))],
    )

  def testDescription(self):
    self.Run("""
        compute sole-tenancy hosts create host-1
        --zone europe-west1-a
        --description 'Tom B.'
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(name='host-1', description='Tom B.'),
              project='my-project',
              zone='europe-west1-a'))],
    )

  def testHostType(self):
    self.Run("""
        compute sole-tenancy hosts create host-1
        --zone europe-west1-a
        --host-type n1-host-64-208
        """.format(compute_uri=self.compute_uri))

    self.CheckRequests(
        [(self.compute.hosts,
          'Insert',
          self.messages.ComputeHostsInsertRequest(
              host=self.messages.Host(
                  name='host-1',
                  hostType='{0}/projects/{1}/zones/{2}/hostTypes/{3}'.format(
                      self.compute_uri, 'my-project', 'europe-west1-a',
                      'n1-host-64-208')),
              project='my-project',
              zone='europe-west1-a'))],
    )


if __name__ == '__main__':
  test_case.main()
