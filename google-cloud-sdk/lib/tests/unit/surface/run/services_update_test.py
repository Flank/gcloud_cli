# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Unit tests for the `run services update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib.surface.run import base

import mock


class UpdateTest(base.ServerlessSurfaceBase, parameterized.TestCase):
  """Tests `services update update` command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.operations.ReleaseService.return_value = None
    self.service = mock.NonCallableMock()
    self.service.domain = 'info.cern.ch'
    self.operations.GetService.return_value = self.service
    self.env_mock = self.StartObjectPatch(
        config_changes, 'EnvVarLiteralChanges')

  def testUpdateEnvVars(self):
    """Tests update of env vars."""
    self.Run(
        'run services update --update-env-vars NAME=tim'
        ' s1')
    self.env_mock.assert_called_once_with(env_vars_to_update={'NAME': 'tim'})
    self.AssertErrContains('Service [s1] revision [rev.1] is active and '
                           'serving traffic at info.cern.ch')

  def testSetEnvVars(self):
    """Tests set of env vars."""
    self.Run(
        'run services update --set-env-vars NAME=tim'
        ' s1')
    self.env_mock.assert_called_once_with(
        env_vars_to_update={'NAME': 'tim'}, clear_others=True)
    self.AssertErrContains('Service [s1] revision [rev.1] is active and '
                           'serving traffic at info.cern.ch')

  def testRemoveEnvVars(self):
    """Tests removal of env vars."""
    self.Run(
        'run services update --remove-env-vars NAME'
        ' s1')
    self.env_mock.assert_called_once_with(env_vars_to_remove=['NAME'])
    self.AssertErrContains('Service [s1] revision [rev.1] is active and '
                           'serving traffic at info.cern.ch')

  def testClearEnvVars(self):
    """Tests clearing of env vars."""
    self.Run(
        'run services update --clear-env-vars'
        ' s1')
    self.env_mock.assert_called_once_with(clear_others=True)
    self.AssertErrContains('Service [s1] revision [rev.1] is active and '
                           'serving traffic at info.cern.ch')

  @parameterized.parameters(base.INVALID_ENV_FLAG_PAIRS)
  def testUpdateAllEnvVars(self, flag1, flag2):
    """Tests that invalid flag pairs raise an error."""
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.Run('run services update {} {}'.format(flag1, flag2))

  def testNoFlags(self):
    """Tests that no action flags at all raises an error."""
    with self.assertRaises(exceptions.NoConfigurationChangeError):
      self.Run('run services update foo')

  def testUpdateConcurrency(self):
    """Tests --concurrency param."""
    self.Run(
        'run services update --concurrency default s1')
    self.AssertErrContains('Service [s1] revision [rev.1] is active and '
                           'serving traffic at info.cern.ch')


class UpdateTestBeta(UpdateTest):
  """Tests `services update update` command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class UpdateTestAlpha(UpdateTestBeta):
  """Tests `services update update` command."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
