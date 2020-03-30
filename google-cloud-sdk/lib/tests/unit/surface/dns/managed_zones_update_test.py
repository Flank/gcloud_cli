# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Tests that exercise the 'gcloud dns managed-zones create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.surface.dns import base


class ManagedZonesUpdateTest(base.DnsMockMultiTrackTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def SetUp(self):
    self.SetUpForTrack(self.track, self.api_version)

  def testUpdateWithDnsPeering_IncompleteTargetProject(self):
    # set target-project, no target-network.
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --target-network: Must be specified.'):
      self.Run('dns managed-zones update --target-project tp zone')

  def testUpdateWithDnsPeering_IncompleteTargetNetwork(self):
    # set target-network, no target-project.
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --target-project: Must be specified.'):
      self.Run('dns managed-zones update --target-network tn zone')


class BetaManagedZonesUpdateTest(ManagedZonesUpdateTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'v1beta2'


if __name__ == '__main__':
  test_case.main()
