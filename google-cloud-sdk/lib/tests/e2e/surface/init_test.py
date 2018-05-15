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
"""Tests for gcloud init command."""

from __future__ import absolute_import
from __future__ import unicode_literals

import os

from googlecloudsdk.core import resources
from googlecloudsdk.core.util import platforms

from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
import six


class InitTest(sdk_test_base.BundledBase,
               e2e_base.WithServiceAuth):

  def PreSetUp(self):
    self.requires_refresh_token = True

  def SetUp(self):
    self.boto_path = platforms.ExpandHomePath(os.path.join('~', '.boto'))
    self._CleanupBotoConfig()

  def TearDown(self):
    self._CleanupBotoConfig()

  def _CleanupBotoConfig(self):
    # Remove the .boto file if it exists, otherwise the test runs won't create
    # it. We do this in SetUp as well as Teardown because a previous run might
    # have left the file here.
    if os.path.exists(self.boto_path):
      os.remove(self.boto_path)

  def AssertProperties(self, props):
    config_setting = self.Run(['config', 'list'])
    for prop, value in six.iteritems(props):
      path = prop.split('/')
      cfg = config_setting
      for part in path:
        self.assertIn(part, cfg)
        cfg = cfg[part]
      self.assertEqual(value, cfg)

  def AssertActiveConfig(self, name):
    configurations = self.Run(
        ['config', 'configurations', 'list', '--no-user-output-enabled'])
    self.assertIn((name, True),
                  [(c['name'], c['is_active']) for c in configurations],
                  '[{0}] is not active'.format(name))

  def GetProjects(self):
    projects = self.Run(['beta', 'projects', 'list',
                         '--no-user-output-enabled'])
    return sorted([prj.projectId for prj in projects])

  def GetZoneRegions(self):
    resource_registry = resources.REGISTRY.Clone()
    resource_registry.RegisterApiByName('compute', 'v1')
    zones = self.Run(['compute', 'zones', 'list', '--no-user-output-enabled'])
    return [(zone['name'], resource_registry.ParseURL(zone['region']).Name())
            for zone in zones]

  def GetAccounts(self):
    results = self.Run(['auth', 'list', '--no-user-output-enabled'])
    return [resource.account for resource in results]

  def testProjects_EnterProject(self):
    projects = self.GetProjects()
    project_idx = projects.index(self.Project())
    zone, region = self.GetZoneRegions()[0]
    accounts = self.GetAccounts()
    account_idx = accounts.index('no_accountability')
    # Expecting two entries
    self.WriteInput('2')  # Create new config.
    self.WriteInput('new-test-configuration')
    self.WriteInput(str(account_idx + 1))
    # Select our test project.
    self.WriteInput(str(project_idx + 1))

    self.WriteInput('Y')  # Lets configure compute.

    # Assuming main project does not have compute zone metadata set.
    self.WriteInput('1')  # Select first zone in the list,
                          # region will be auto-selected based on zone.

    # Make sure no .boto file exists at the start.
    self.assertFalse(os.path.exists(self.boto_path))

    self.Run(['init'])
    self.AssertErrContains(
        'Your Google Cloud SDK is configured and ready to use!')

    self.AssertProperties({
        'compute/zone': zone,
        'compute/region': region,
        'core/account': 'no_accountability',
        'core/project': self.Project(),
    })
    self.AssertActiveConfig('new-test-configuration')

    # The command should have created a .boto file.
    self.AssertErrContains('Created a default .boto configuration file')
    self.assertTrue(os.path.exists(self.boto_path))

if __name__ == '__main__':
  test_case.main()
