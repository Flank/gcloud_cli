# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the instances set-iam-policy subcommand."""

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SetScopesTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testKeepScopes(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='central2-a',
                serviceAccounts=[
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'a', 'b', 'c',
                        ]
                    ),
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'd', 'e',
                        ]
                    ),
                ],
            ),
        ],
        []
    ])

    self.Run("""
        compute instances set-scopes instance
        --service-account john@doe.com
        --zone zone-1
        """)

    expected_scopes = ['a', 'b', 'c', 'd', 'e']
    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='john@doe.com',
                      scopes=expected_scopes,
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testKeepAccount(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='central2-a',
                serviceAccounts=[
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'a', 'b', 'c',
                        ]
                    ),
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'd', 'e',
                        ]
                    ),
                ],
            ),
        ],
        []
    ])

    self.Run("""
        compute instances set-scopes instance
        --scopes b
        --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='account@example.com',
                      scopes=['b'],
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testSetDefaultScopes(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='central2-a',
                serviceAccounts=[
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'a', 'b', 'c',
                        ]
                    ),
                    self.messages.ServiceAccount(
                        email='account@example.com',
                        scopes=[
                            'd', 'e',
                        ]
                    ),
                ],
            ),
        ],
        []
    ])

    self.Run("""
        compute instances set-scopes instance
        --scopes default
        --zone zone-1
        """)

    default_scopes = [
        'https://www.googleapis.com/auth/devstorage.read_only',
        'https://www.googleapis.com/auth/logging.write',
        'https://www.googleapis.com/auth/monitoring.write',
        'https://www.googleapis.com/auth/pubsub',
        'https://www.googleapis.com/auth/service.management.readonly',
        'https://www.googleapis.com/auth/servicecontrol',
        'https://www.googleapis.com/auth/trace.append',
    ]
    self.CheckRequests(
        [(self.compute.instances,
          'Get',
          self.messages.ComputeInstancesGetRequest(
              instance='instance',
              project='my-project',
              zone='zone-1'))],
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='account@example.com',
                      scopes=default_scopes,
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testSetScopesOnInstanceNoAccount(self):
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(
                name='central2-a',
                serviceAccounts=[],
            ),
        ],
        []
    ])

    with self.assertRaisesRegex(
        exceptions.ToolException,
        r'Can not set scopes when there is no service acoount\.'):
      self.Run("""
          compute instances set-scopes instance
          --scopes b
          --zone zone-1
          """)

    self.CheckRequests(
        [
            (self.compute.instances,
             'Get',
             self.messages.ComputeInstancesGetRequest(
                 instance='instance',
                 project='my-project',
                 zone='zone-1'))],
    )

  def testPurge(self):
    self.Run("""
        compute instances set-scopes instance
        --zone zone-1
        --no-scopes
        --no-service-account
        """)
    self.CheckRequests(
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest()),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testOneScope(self):
    self.Run("""
        compute instances set-scopes instance
        --zone zone-1
        --service-account john@doe.com
        --scopes scope-a
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='john@doe.com',
                      scopes=['scope-a'],
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testZonePrompting(self):
    # ResourceArgument checks if this is true before attempting to prompt.
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.WriteInput('2\n')
    self.make_requests.side_effect = iter([
        [
            self.messages.Instance(name='instance', zone='us-central1-a'),
            self.messages.Instance(name='instance', zone='us-central1-b'),
            self.messages.Instance(name='instance', zone='us-central2-a'),
        ],
        [],
    ])
    self.Run("""
        compute instances set-scopes instance
        --service-account john@doe.com
        --scopes scope-a
        """)

    self.CheckRequests(
        self.FilteredInstanceAggregateListRequest('instance'),
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='john@doe.com',
                      scopes=['scope-a'],
                  )),
              project='my-project',
              zone='us-central1-b',
              instance='instance'))],
    )

  def testTwoScopes(self):
    self.Run("""
        compute instances set-scopes instance
        --zone zone-1
        --service-account john@doe.com
        --scopes scope-a,scope-b
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='john@doe.com',
                      scopes=['scope-a', 'scope-b'],
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

  def testScopeAliases(self):
    self.Run("""
        compute instances set-scopes instance
        --zone zone-1
        --service-account john@doe.com
        --scopes bigquery,cloud-platform
        """)

    self.CheckRequests(
        [(self.compute.instances,
          'SetServiceAccount',
          self.messages.ComputeInstancesSetServiceAccountRequest(
              instancesSetServiceAccountRequest=(
                  self.messages.InstancesSetServiceAccountRequest(
                      email='john@doe.com',
                      scopes=['https://www.googleapis.com/auth/bigquery',
                              'https://www.googleapis.com/auth/cloud-platform'],
                  )),
              project='my-project',
              zone='zone-1',
              instance='instance'))],
    )

if __name__ == '__main__':
  test_case.main()
