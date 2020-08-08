# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for the instance-groups managed wait-until subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instance_groups import test_resources
from mock import patch


class InstanceGroupManagersWaitUntilZonalGATest(test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testWaitUntilStable(self):
    self._SetRequestsSideEffects()
    self.Run("""compute instance-groups managed wait-until --stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1
        Waiting for group to become stable
        Group is stable
        """),
        normalize_space=True)

  def testWaitUntilStableCreationWithoutRetries(self):
    self._SetRequestsSideEffects(pending_state='creatingWithoutRetries')
    self.Run("""compute instance-groups managed wait-until --stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creatingWithoutRetries: 10
        Waiting for group to become stable, current operations: creatingWithoutRetries: 10
        Waiting for group to become stable, current operations: creatingWithoutRetries: 5
        Waiting for group to become stable, current operations: creatingWithoutRetries: 1
        Waiting for group to become stable
        Group is stable
        """),
        normalize_space=True)

  def testWaitUntilVersionTargetReached(self):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(version_target_reached=False),
        self._MakeInstanceGroupManager(version_target_reached=False),
        self._MakeInstanceGroupManager(version_target_reached=True)
    ])
    self.Run("""compute instance-groups managed wait-until
      --version-target-reached group-1 --zone central2-a""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to reach version target
        Waiting for group to reach version target
        Version target is reached
        """),
        normalize_space=True)

  def testWaitUntilStableAlreadyStable(self):
    self._SetRequestsSideEffects()
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(0, is_stable=True),
    ])

    self.Run("""compute instance-groups managed wait-until --stable group-1
      --zone central2-a
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Group is stable
        """), normalize_space=True)

  def testWaitUntilVersionTargetReachedAlreadyReached(self):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(version_target_reached=True)
    ])
    self.Run("""compute instance-groups managed wait-until
      --version-target-reached group-1 --zone central2-a""")

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Version target is reached
        """),
        normalize_space=True)

  def testWaitUntilStableTimeout(self):
    self._SetRequestsSideEffects()
    self.time.side_effect = iter([0, 10])
    with self.assertRaisesRegex(
        utils.TimeoutError,
        'Timeout while waiting for group to become stable'):
      self.Run("""compute instance-groups managed wait-until --stable group-1
        --zone central2-a
        --timeout 1
        """)

  def testWaitUntilVersionTargetReachedTimeout(self):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(version_target_reached=False),
        self._MakeInstanceGroupManager(version_target_reached=True)
    ])
    self.time.side_effect = iter([0, 10])
    with self.assertRaisesRegex(
        utils.TimeoutError,
        'Timeout while waiting for group to reach version target'):
      self.Run("""compute instance-groups managed wait-until
        --version-target-reached group-1 --zone central2-a --timeout 1""")

  @patch('googlecloudsdk.command_lib.compute.instance_groups.flags.'
         'MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG',
         instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_ARG)
  def testInvalidCollectionPath(self):
    with self.assertRaisesRegex(ValueError, 'Unknown reference type.*'):
      self.Run("""compute instance-groups managed wait-until --stable group-1
        --zone central2-a""")

  def testWaitUntilWithoutArguments(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        r'Exactly one of \(--stable \| --version-target-reached\) '
        'must be specified'):
      self.Run("""compute instance-groups managed wait-until group-1
        --zone central2-a
        --timeout 1
        """)

  def _MakeInstanceGroupManager(self,
                                current_operations=0,
                                current_state='creating',
                                is_stable=False,
                                version_target_reached=True):
    return [
        test_resources.MakeInstanceGroupManagersWithActions(
            self.api_version,
            current_operations,
            actions_state=current_state,
            is_stable=is_stable,
            version_target_reached=version_target_reached)
    ]

  def _SetRequestsSideEffects(self, pending_state='creating'):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(10, pending_state),
        self._MakeInstanceGroupManager(10, pending_state),
        self._MakeInstanceGroupManager(5, pending_state),
        self._MakeInstanceGroupManager(1, pending_state),
        self._MakeInstanceGroupManager(0, pending_state),
        self._MakeInstanceGroupManager(0, pending_state, is_stable=True),
    ])


class InstanceGroupManagersWaitUntilRegionalGATest(test_base.BaseTest):

  def PreSetUp(self):
    self.api_version = 'v1'
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testWait(self):
    self._SetRequestsSideEffects()
    self.Run("""compute instance-groups managed wait-until --stable group-1
      --region central2
      """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 10
        Waiting for group to become stable, current operations: creating: 5
        Waiting for group to become stable, current operations: creating: 1
        Waiting for group to become stable
        Group is stable
        """),
        normalize_space=True)

  def testAlreadyStable(self):
    self._SetRequestsSideEffects()
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(0, is_stable=True),
    ])

    self.Run("""
        compute instance-groups managed wait-until --stable group-1
            --region central2
        """)

    self.AssertOutputEquals(
        textwrap.dedent("""\
        Group is stable
        """), normalize_space=True)

  def testTimeout(self):
    self._SetRequestsSideEffects()
    self.time.side_effect = iter([0, 10])
    with self.assertRaisesRegex(
        utils.TimeoutError,
        'Timeout while waiting for group to become stable'):
      self.Run("""
          compute instance-groups managed wait-until --stable group-1
              --region central2
              --timeout 1
          """)

  def _MakeInstanceGroupManager(self,
                                current_operations=0,
                                current_state='creating',
                                is_stable=False,
                                version_target_reached=True):
    return [
        test_resources.MakeInstanceGroupManagersWithActions(
            self.api_version,
            current_operations,
            actions_state=current_state,
            is_stable=is_stable,
            version_target_reached=version_target_reached)
    ]

  def _SetRequestsSideEffects(self, pending_state='creating'):
    self.make_requests.side_effect = iter([
        self._MakeInstanceGroupManager(10),
        self._MakeInstanceGroupManager(10),
        self._MakeInstanceGroupManager(5),
        self._MakeInstanceGroupManager(1),
        self._MakeInstanceGroupManager(0),
        self._MakeInstanceGroupManager(0, is_stable=True),
    ])


class InstanceGroupManagersWaitUntilZonalBetaTest(
    InstanceGroupManagersWaitUntilZonalGATest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersWaitUntilRegionalBetaTest(
    InstanceGroupManagersWaitUntilRegionalGATest):

  def PreSetUp(self):
    self.api_version = 'beta'
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceGroupManagersWaitUntilRegionalAlphaTest(
    InstanceGroupManagersWaitUntilRegionalBetaTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


class InstanceGroupManagersWaitUntilZonalAlphaTest(
    InstanceGroupManagersWaitUntilZonalBetaTest):

  def PreSetUp(self):
    self.api_version = 'alpha'
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
