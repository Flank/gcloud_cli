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
"""Tests for the target-pools set-backup subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetPoolsSetBackupTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute target-pools set-backup target-pool-1
          --backup-pool target-pool-2
          --failover-ratio 0.5
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'SetBackup',
          messages.ComputeTargetPoolsSetBackupRequest(
              targetPool='target-pool-1',
              project='my-project',
              failoverRatio=0.5,
              region='us-central2',
              targetReference=messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/v1/projects/'
                      'my-project/regions/us-central2/targetPools/'
                      'target-pool-2'),
              )))],
    )

  def testUnsetBackup(self):
    self.Run("""
        compute target-pools set-backup target-pool-1
          --no-backup-pool
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'SetBackup',
          messages.ComputeTargetPoolsSetBackupRequest(
              targetPool='target-pool-1',
              project='my-project',
              region='us-central2',
              targetReference=messages.TargetReference()
          ))],
    )

  def testFailoverRatioMissing(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--failover-ratio\] must be provided when setting a backup pool.'):
      self.Run("""
        compute target-pools set-backup target-pool-1
          --backup-pool target-pool-2
          --region us-central2
        """)

    self.CheckRequests()

  def testFailoverRatioTooSmall(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--failover-ratio\] must be a number between 0 and 1, inclusive.'):
      self.Run("""
        compute target-pools set-backup target-pool-1
          --backup-pool target-pool-2
          --failover-ratio -0.2
          --region us-central2
        """)

    self.CheckRequests()

  def testFailoverRatioTooBig(self):
    with self.AssertRaisesToolExceptionRegexp(
        '[--failover-ratio] must be a number between 0 and 1, inclusive.'):
      self.Run("""
        compute target-pools set-backup target-pool-1
          --backup-pool target-pool-2
          --failover-ratio 2
          --region us-central2
        """)

    self.CheckRequests()

  def testUriSupport(self):
    self.Run("""
        compute target-pools set-backup
          https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2/targetPools/target-pool-1
          --backup-pool https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2/targetPools/target-pool-2
          --failover-ratio 0.5
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'SetBackup',
          messages.ComputeTargetPoolsSetBackupRequest(
              targetPool='target-pool-1',
              project='my-project',
              failoverRatio=0.5,
              region='us-central2',
              targetReference=messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/v1/projects/'
                      'my-project/regions/us-central2/targetPools/'
                      'target-pool-2'),
              )))],
    )

  def testRegionPrompting(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self.make_requests.side_effect = iter([
        [
            messages.Region(name='us-central1'),
            messages.Region(name='us-central2'),
        ],

        [],
    ])
    self.WriteInput('2\n')

    self.Run("""
        compute target-pools set-backup target-pool-1
          --backup-pool target-pool-2
          --failover-ratio 0.5
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.targetPools,
          'SetBackup',
          messages.ComputeTargetPoolsSetBackupRequest(
              targetPool='target-pool-1',
              project='my-project',
              failoverRatio=0.5,
              region='us-central2',
              targetReference=messages.TargetReference(
                  target=(
                      'https://www.googleapis.com/compute/v1/projects/'
                      'my-project/regions/us-central2/targetPools/'
                      'target-pool-2'),
              )))],
    )

    self.AssertErrContains('target-pool-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')


if __name__ == '__main__':
  test_case.main()
