# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration test for the 'composer environments list-upgrades' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import test_case
from tests.lib.surface.composer import base


class _EnvironmentListUpgradesIntegrationBase(base.ComposerE2ETestBase):
  """Integration test for the 'composer environments list-upgrades' command.

  Composer gcloud e2e tests are run against a project with existing environments
  for reasons described in base.ComposerE2ETestBase. Therefore, no
  environments are created before testing list-upgrades.
  """


class EnvironmentListUpgradesIntegrationBetaTest(
    _EnvironmentListUpgradesIntegrationBase):

  def PreSetUp(self):
    self.SetTrack(calliope_base.ReleaseTrack.BETA)

  def testListEnvironments(self):
    environs = list(
        self.Run('composer environments list --locations=us-central1 --limit=2 '
                 '--format=disable', self.track))
    self.assertGreater(len(environs), 0)

    upgrade_target = environs[0]
    upgrade_results = list(self.Run(
        'composer environments list-upgrades {} --location=us-central1 '
        '--limit=2 --format=disable'.format(upgrade_target.name), self.track))

    self.assertIsNotNone(
        upgrade_results, 'Expect output from \'list-upgrades\' execution '
        '(even if 0 upgrades options are returned)')
    self.assertGreater(len(upgrade_results), 0)


if __name__ == '__main__':
  test_case.main()
