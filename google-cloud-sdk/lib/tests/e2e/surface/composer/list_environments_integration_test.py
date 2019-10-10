# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Integration test for the 'composer environments list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.composer import base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters(calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class ListEnvironmentsIntegrationTest(base.ComposerE2ETestBase,
                                      parameterized.TestCase):
  """Integration test for the 'composer environments list' command.

  Composer gcloud e2e tests are run against a project with existing environments
  for reasons described in base.ComposerE2ETestBase. Therefore, no
  environments are created before testing list.
  """

  def testListEnvironments(self, track):
    self.SetTrack(track)
    environs = list(
        self.Run(
            'composer environments list --locations=us-central1 --limit=2 '
            '--format=disable')
    )
    self.assertGreater(len(environs), 0)
    for environ in environs:
      # environment name follows correct pattern
      match = re.match(
          'projects/' + self.Project() + '/locations/us-central1/environments/'
          '([a-z][-0-9a-z]*[0-9a-z])', environ.name)
      self.assertTrue(bool(match))

if __name__ == '__main__':
  test_case.main()
