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
"""Tests for the target-instances create subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetInstancesCreateTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute target-instances create my-target-instance
          --instance my-instance --zone central2-a
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Insert',
          messages.ComputeTargetInstancesInsertRequest(
              targetInstance=messages.TargetInstance(
                  name='my-target-instance',
                  instance=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute target-instances create
          https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/targetInstances/my-target-instance
          --instance https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/instances/my-instance
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Insert',
          messages.ComputeTargetInstancesInsertRequest(
              targetInstance=messages.TargetInstance(
                  name='my-target-instance',
                  instance=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testDifferentZones(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Target instance zone must match the virtual machine instance zone.'):
      self.Run("""
          compute target-instances create
            https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-a/targetInstances/my-target-instance
            --instance https://www.googleapis.com/compute/v1/projects/my-project/zones/central2-b/instances/my-instance
          """)

    self.CheckRequests()

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Zone(name='central1-a'),
            messages.Zone(name='central1-b'),
            messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('3\n')

    self.Run("""
        compute target-instances create my-target-instance
          --instance my-instance
        """)

    self.CheckRequests(
        self.zones_list_request,

        [(self.compute_v1.targetInstances,
          'Insert',
          messages.ComputeTargetInstancesInsertRequest(
              targetInstance=messages.TargetInstance(
                  name='my-target-instance',
                  instance=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

    self.AssertErrContains('my-target-instance')
    self.AssertErrContains('central1-a')
    self.AssertErrContains('central1-b')
    self.AssertErrContains('central2-a')

  def testWithDescriptionFlag(self):
    self.Run("""
        compute target-instances create my-target-instance
          --instance my-instance --zone central2-a
          --description my-description
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Insert',
          messages.ComputeTargetInstancesInsertRequest(
              targetInstance=messages.TargetInstance(
                  description='my-description',
                  name='my-target-instance',
                  instance=('https://www.googleapis.com/compute/v1/projects/'
                            'my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testLegacyProject(self):
    self.Run("""
        compute target-instances create my-target-instance
          --instance my-instance --zone central2-a
          --project google.com:my-legacy-project
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Insert',
          messages.ComputeTargetInstancesInsertRequest(
              targetInstance=messages.TargetInstance(
                  name='my-target-instance',
                  instance=('https://www.googleapis.com/compute/v1/projects/'
                            'google.com:my-legacy-project/zones/central2-a/'
                            'instances/my-instance'),
              ),
              project='google.com:my-legacy-project',
              zone='central2-a'))],
    )


if __name__ == '__main__':
  test_case.main()
