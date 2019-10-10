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
"""Unit tests for the `events triggers delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.core.console import console_io
from tests.lib.surface.run import base


class TriggersDeleteTestAlpha(base.ServerlessSurfaceBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testTriggersFailNonGKE(self):
    """Triggers are not yet supported on managed Cloud Run."""
    with self.assertRaises(exceptions.UnsupportedArgumentError):
      self.Run('events triggers delete my-trigger --region=us-central1')
    self.AssertErrContains(
        'Events are only available with Cloud Run for Anthos.')

  def testTriggersDelete(self):
    """Tests successful delete with default output format."""
    self.WriteInput('Y\n')
    self.Run('events triggers delete my-trigger --platform=gke '
             '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.operations.DeleteTrigger.assert_called_once_with(
        self._TriggerRef('my-trigger', 'default'))
    self.AssertErrContains('Deleted trigger [my-trigger].')

  def testTriggersFailsIfUnattended(self):
    """Tests that delete fails if console is unattended."""
    self.is_interactive.return_value = False
    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run('events triggers delete my-trigger --platform=gke '
               '--cluster=cluster-1 --cluster-location=us-central1-a')
    self.operations.DeleteTrigger.assert_not_called()
