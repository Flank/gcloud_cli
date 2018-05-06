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
"""Tests for the target-pools create subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetPoolsCreateTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.make_requests.side_effect = [[
        self.messages.TargetPool(
            name='target-pool-1',
            region='us-central2',
            sessionAffinity=(
                messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
            backupPool='backup-pool',
            healthChecks=['health-check'])
    ]]

    self.Run("""
        compute target-pools create target-pool-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  name='target-pool-1',
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
    )

    self.AssertOutputEquals("""\
      NAME           REGION       SESSION_AFFINITY  BACKUP       HEALTH_CHECKS
      target-pool-1  us-central2  NONE              backup-pool  health-check
      """, normalize_space=True)

  def testDescription(self):
    self.Run("""
        compute target-pools create target-pool-1
          --description fancy
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  description='fancy',
                  name='target-pool-1',
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testBackupPoolAndNotFailoverRatio(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Either both or neither of \[--failover-ratio\] and \[--backup-pool\] '
        'must be provided.'):
      self.Run("""
          compute target-pools create target-pool-1
            --backup-pool backup
            --region us-central2
          """)

    self.CheckRequests()

  def testFailoverRatioAndNotBackupPool(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'Either both or neither of \[--failover-ratio\] and \[--backup-pool\] '
        'must be provided.'):
      self.Run("""
          compute target-pools create target-pool-1
            --failover-ratio 0.5
            --region us-central2
          """)

    self.CheckRequests()

  def testFailoverRatioTooSmall(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--failover-ratio\] must be a number between 0 and 1, inclusive.'):
      self.Run("""
          compute target-pools create target-pool-1
            --failover-ratio -0.2
            --region us-central2
            --backup-pool backup
          """)

    self.CheckRequests()

  def testFailoverRatioTooBig(self):
    with self.AssertRaisesToolExceptionRegexp(
        r'\[--failover-ratio\] must be a number between 0 and 1, inclusive.'):
      self.Run("""
          compute target-pools create target-pool-1
            --failover-ratio 1.1
            --region us-central2
            --backup-pool backup
          """)

    self.CheckRequests()

  def testBackupPool(self):
    self.Run("""
        compute target-pools create target-pool-1
          --backup-pool backup
          --failover-ratio 0.5
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  backupPool=('https://www.googleapis.com/compute/v1/projects/'
                              'my-project/regions/us-central2/targetPools/'
                              'backup'),
                  failoverRatio=0.5,
                  name='target-pool-1',
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testSingleHealthCheck(self):
    self.Run("""
        compute target-pools create target-pool-1
          --health-check check-it-1
          --region us-central2
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  healthChecks=['https://www.googleapis.com/compute/v1/'
                                'projects/my-project/global/httpHealthChecks/'
                                'check-it-1'],
                  name='target-pool-1',
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testMultipleHealthChecks(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments:\n  check-it-2\n  check-it-3'):
      self.Run("""
          compute target-pools create target-pool-1
            --health-check check-it-1
                           check-it-2
                           check-it-3
            --region us-central2
          """)

    self.AssertErrContains(
        'unrecognized arguments:\n  check-it-2\n  check-it-3')
    self.CheckRequests()

  def testSessionAffinity(self):
    self.templateTestSessionAffinity("""
        compute target-pools create target-pool-1
          --region us-central2
          --session-affinity CLIENT_IP
        """)

  def testSessionAffinityLowerCase(self):
    self.templateTestSessionAffinity("""
        compute target-pools create target-pool-1
          --region us-central2
          --session-affinity client_ip
        """)

  def templateTestSessionAffinity(self, cmd):
    self.Run(cmd)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  name='target-pool-1',
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum
                      .CLIENT_IP),
              ),
              project='my-project',
              region='us-central2'))],
    )

  def testUriSupport(self):
    self.Run("""
        compute target-pools create
          https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2/targetPools/target-pool-1
          --backup-pool https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central2/targetPools/backup-pool
          --failover-ratio 0.5
        """)

    self.CheckRequests(
        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  name='target-pool-1',
                  backupPool=('https://www.googleapis.com/compute/v1/projects/'
                              'my-project/regions/us-central2/targetPools/'
                              'backup-pool'),
                  failoverRatio=0.5,
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
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
        compute target-pools create target-pool-1
          --backup-pool backup-pool
          --failover-ratio 0.5
        """)

    self.CheckRequests(
        self.regions_list_request,

        [(self.compute_v1.targetPools,
          'Insert',
          messages.ComputeTargetPoolsInsertRequest(
              targetPool=messages.TargetPool(
                  name='target-pool-1',
                  backupPool=('https://www.googleapis.com/compute/v1/projects/'
                              'my-project/regions/us-central2/targetPools/'
                              'backup-pool'),
                  failoverRatio=0.5,
                  sessionAffinity=(
                      messages.TargetPool.SessionAffinityValueValuesEnum.NONE),
              ),
              project='my-project',
              region='us-central2'))],
    )

    self.AssertErrContains('target-pool-1')
    self.AssertErrContains('us-central1')
    self.AssertErrContains('us-central2')


if __name__ == '__main__':
  test_case.main()
