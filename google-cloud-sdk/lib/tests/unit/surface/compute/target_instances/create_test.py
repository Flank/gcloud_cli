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
"""Tests for the target-instances create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetInstancesCreateTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')
    self._api = ''
    self._target_instances_api = self.compute_v1.targetInstances

  def RunCreate(self, args):
    self.Run(self._api + ' compute target-instances create ' + args)

  def testSimpleCase(self):
    self.RunCreate("""
        my-target-instance --instance my-instance --zone central2-a
        """)

    self.CheckRequests(
        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/my-project/zones/central2-a/instances/'
                            'my-instance')
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/%(api)s/projects/my-project/zones/central2-a/targetInstances/my-target-instance
          --instance https://compute.googleapis.com/compute/%(api)s/projects/my-project/zones/central2-a/instances/my-instance
          --zone central2-a
        """ % {'api': self.api})

    self.CheckRequests(
        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testDifferentZones(self):
    with self.AssertRaisesToolExceptionRegexp(
        'Target instance zone must match the virtual machine instance zone.'):
      self.RunCreate("""
            https://compute.googleapis.com/compute/v1/projects/my-project/zones/central2-a/targetInstances/my-target-instance
            --instance https://compute.googleapis.com/compute/v1/projects/my-project/zones/central2-b/instances/my-instance
            --zone central2-a
          """)

    self.CheckRequests()

  def testZonePrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            self.messages.Zone(name='central1-a'),
            self.messages.Zone(name='central1-b'),
            self.messages.Zone(name='central2-a'),
        ],
        []
    ])
    self.WriteInput('3\n')

    self.RunCreate("""
        my-target-instance --instance my-instance
        """)

    self.CheckRequests(
        self.zones_list_request,

        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/my-project/zones/central2-a/instances/'
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
    self.RunCreate("""
        my-target-instance
          --instance my-instance --zone central2-a
          --description my-description
        """)

    self.CheckRequests(
        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  description='my-description',
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/my-project/zones/central2-a/instances/'
                            'my-instance'),
              ),
              project='my-project',
              zone='central2-a'))],
    )

  def testLegacyProject(self):
    self.RunCreate("""
        my-target-instance
          --instance my-instance --zone central2-a
          --project google.com:my-legacy-project
        """)

    self.CheckRequests(
        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/google.com:my-legacy-project/zones/'
                            'central2-a/instances/my-instance')
                  ),
              project='google.com:my-legacy-project',
              zone='central2-a'))],
    )


class TargetInstancesCreateBetaTest(TargetInstancesCreateTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._api = 'beta'
    self._target_instances_api = self.compute_beta.targetInstances

  def testWithNetwork(self):
    self.RunCreate("""
          my-target-instance
          --instance my-instance --zone central2-a
          --network default
        """)

    self.CheckRequests(
        [(self._target_instances_api,
          'Insert',
          self.messages.ComputeTargetInstancesInsertRequest(
              targetInstance=self.messages.TargetInstance(
                  name='my-target-instance',
                  instance=(self.compute_uri +
                            '/projects/my-project/zones/central2-a/instances/'
                            'my-instance'),
                  network=(self.compute_uri +
                           '/projects/my-project/global/networks/default')
                  ),
              project='my-project',
              zone='central2-a'))],
    )


class TargetInstancesCreateAlphaTest(TargetInstancesCreateTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._api = 'alpha'
    self._target_instances_api = self.compute_alpha.targetInstances


if __name__ == '__main__':
  test_case.main()
