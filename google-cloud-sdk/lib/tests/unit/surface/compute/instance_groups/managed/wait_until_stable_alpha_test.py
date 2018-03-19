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
"""Tests for the instance-groups managed wait-until-stable subcommand."""
import textwrap

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

API_VERSION = 'alpha'


class InstanceGroupManagersWaitUntilStableZonalTest(test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWait(self):
    self._SetRequestsSideEffects()
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1
        Group is stable
        """), normalize_space=True)

  def testWaitForCreationWithoutRetries(self):
    self._SetRequestsSideEffects(current_state='creatingWithoutRetries')
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creatingWithoutRetries: 10
        Waiting for group to become stable, current operations: creatingWithoutRetries: 10
        Waiting for group to become stable, current operations: creatingWithoutRetries: 5
        Waiting for group to become stable, current operations: creatingWithoutRetries: 1
        Group is stable
        """), normalize_space=True)

  def testWaitForVerification(self):
    self._SetRequestsSideEffects(current_state='verifying')
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: verifying: 10
        Waiting for group to become stable, current operations: verifying: 10
        Waiting for group to become stable, current operations: verifying: 5
        Waiting for group to become stable, current operations: verifying: 1
        Group is stable
        """), normalize_space=True)

  def testAlreadyStable(self):
    self._SetRequestsSideEffects()
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(0),
    ])

    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Group is stable
        """), normalize_space=True)

  def testTimeout(self):
    self._SetRequestsSideEffects()
    self.time.side_effect = iter([0, 10])
    with self.assertRaisesRegexp(
        utils.TimeoutError,
        'Timeout while waiting for group to become stable'):
      self.Run("""compute instance-groups managed wait-until-stable group-1
        --zone central2-a
        --timeout 1
        """)

  def testPendingActions(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManagerWithPendingActions(10),
        self._MakeInstanceGroupManagerWithPendingActions(10),
        self._MakeInstanceGroupManagerWithPendingActions(5),
        self._MakeInstanceGroupManagerWithPendingActions(1),
        self._MakeInstanceGroupManagerWithPendingActions(0),
    ])
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, pending operations: creating: 10
        Waiting for group to become stable, pending operations: creating: 10
        Waiting for group to become stable, pending operations: creating: 5
        Waiting for group to become stable, pending operations: creating: 1
        Group is stable
        """), normalize_space=True)

  def testCurrentAndPendingActions(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManagerWithPendingActions(10, 10),
        self._MakeInstanceGroupManagerWithPendingActions(10, 10),
        self._MakeInstanceGroupManagerWithPendingActions(5, 5),
        self._MakeInstanceGroupManagerWithPendingActions(1, 1),
        self._MakeInstanceGroupManagerWithPendingActions(0, 0),
    ])
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10, pending operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10, pending operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5, pending operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1, pending operations: creating: 1
        Group is stable
        """), normalize_space=True)

  @staticmethod
  def _MakeInstanceGroupManager(current_operations, current_state='creating'):
    return [test_resources.MakeInstanceGroupManagersWithCurrentActions(
        API_VERSION, current_operations, current_actions_state=current_state)]

  @staticmethod
  def _MakeInstanceGroupManagerWithPendingActions(pending_operations,
                                                  current_operations=0):
    return [test_resources.MakeInstanceGroupManagersWithPendingActions(
        API_VERSION, pending_operations, current_operations)]

  def _SetRequestsSideEffects(self, current_state='creating'):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(10, current_state),
        self._MakeInstanceGroupManager(10, current_state),
        self._MakeInstanceGroupManager(5, current_state),
        self._MakeInstanceGroupManager(1, current_state),
        self._MakeInstanceGroupManager(0, current_state),
    ])


class InstanceGroupManagersWaitUntilStableRegionalTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(10),
        self._MakeInstanceGroupManager(10),
        self._MakeInstanceGroupManager(5),
        self._MakeInstanceGroupManager(1),
        self._MakeInstanceGroupManager(0),
    ])
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testWait(self):
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --region central2
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1
        Group is stable
        """), normalize_space=True)

  def testAlreadyStable(self):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(0),
    ])

    self.Run("""
        compute instance-groups managed wait-until-stable group-1
            --region central2
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Group is stable
        """), normalize_space=True)

  def testTimeout(self):
    self.time.side_effect = iter([0, 10])
    with self.assertRaisesRegexp(
        utils.TimeoutError,
        'Timeout while waiting for group to become stable'):
      self.Run("""
          compute instance-groups managed wait-until-stable group-1
              --region central2
              --timeout 1
          """)

  def testPendingActions(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManagerWithPendingActions(10),
        self._MakeInstanceGroupManagerWithPendingActions(10),
        self._MakeInstanceGroupManagerWithPendingActions(5),
        self._MakeInstanceGroupManagerWithPendingActions(1),
        self._MakeInstanceGroupManagerWithPendingActions(0),
    ])
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --region central2
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, pending operations: creating: 10
        Waiting for group to become stable, pending operations: creating: 10
        Waiting for group to become stable, pending operations: creating: 5
        Waiting for group to become stable, pending operations: creating: 1
        Group is stable
        """), normalize_space=True)

  def testCurrentAndPendingActions(self):
    self.SelectApi(API_VERSION)
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManagerWithPendingActions(10, 10),
        self._MakeInstanceGroupManagerWithPendingActions(10, 10),
        self._MakeInstanceGroupManagerWithPendingActions(5, 5),
        self._MakeInstanceGroupManagerWithPendingActions(1, 1),
        self._MakeInstanceGroupManagerWithPendingActions(0, 0),
    ])
    self.Run("""compute instance-groups managed wait-until-stable group-1
      --region central2
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10, pending operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10, pending operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5, pending operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1, pending operations: creating: 1
        Group is stable
        """), normalize_space=True)

  @staticmethod
  def _MakeInstanceGroupManager(current_operations):
    return [test_resources.MakeInstanceGroupManagersWithCurrentActions(
        api=API_VERSION, current_actions_count=current_operations,
        scope_type='region', scope_name='central2')]

  @staticmethod
  def _MakeInstanceGroupManagerWithPendingActions(pending_operations,
                                                  current_operations=0):
    return [test_resources.MakeInstanceGroupManagersWithPendingActions(
        api=API_VERSION, pending_actions_count=pending_operations,
        current_actions_count=current_operations, scope_type='region',
        scope_name='central2')]


if __name__ == '__main__':
  test_case.main()
