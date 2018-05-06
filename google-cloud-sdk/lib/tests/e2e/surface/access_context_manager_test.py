
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
"""E2E tests for `gcloud access-context-manager` commands."""
import contextlib

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


def _GetResourceName(prefix):
  return next(e2e_utils.GetResourceNameGenerator(prefix, delimiter='_')).upper()


class AccessContextManagerE2eTests(e2e_base.WithServiceAuth,
                                   cli_test_base.CliTestBase):

  ORG_ID = '1054311078602'
  LEVEL_SPEC = ('[{"ipSubnetworks": ["8.8.8.8/32"]}, '
                '{"members": ["user:example@example.com"]}]')
  PROJECT_NUMBER = '175742511250'
  # Requires an already-set-up regular zone, in case it runs multiple times
  # simultaneously (a single project can only belong to one regular zone, but
  # many bridge zones; however, to belong to a bridge zone, it needs to belong
  # to one regular zone).

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def _SetPolicyProperty(self, policy):
    properties.VALUES.access_context_manager.policy.Set(policy)
    try:
      yield
    finally:
      properties.VALUES.access_context_manager.policy.Set(None)

  @contextlib.contextmanager
  def _CreateLevel(self):
    level_spec_file = self.Touch(self.temp_path, 'level.yaml',
                                 contents=self.LEVEL_SPEC)
    level_id = _GetResourceName('LEVEL')
    try:
      self.Run(
          'access-context-manager levels create'
          '    --title "My Level {level}" '
          '    --basic-level-spec {spec} '
          '   {level}'.format(spec=level_spec_file, level=level_id))
      yield level_id
    finally:
      self.Run(
          'access-context-manager levels delete '
          '    --quiet '
          '   {}'.format(level_id))

  def _UpdateLevel(self, level_id, new_title):
    return self.Run(
        'access-context-manager levels update '
        '    --title "{}" '
        '    {}'.format(new_title, level_id))

  def _DescribeLevel(self, level_id):
    return self.Run(
        'access-context-manager levels describe '
        '    --format disable '  # Disable format to get a return value
        '    {}'.format(level_id))

  @contextlib.contextmanager
  def _CreateZone(self):
    zone_id = _GetResourceName('ZONE')
    try:
      self.Run(
          'access-context-manager zones create'
          '    --zone-type bridge '
          '    --title "My Zone {zone}" '
          '    --resources projects/{project} '
          '   {zone}'.format(project=self.PROJECT_NUMBER, zone=zone_id))
      yield zone_id
    finally:
      self.Run(
          'access-context-manager zones delete '
          '    --quiet '
          '   {}'.format(zone_id))

  def _UpdateZone(self, zone_id, new_title):
    return self.Run(
        'access-context-manager zones update '
        '    --title "{}" '
        '    {}'.format(new_title, zone_id))

  def _DescribeZone(self, zone_id):
    return self.Run(
        'access-context-manager zones describe '
        '    --format disable '  # Disable format to get a return value
        '    {}'.format(zone_id))

  def testAccessContextManager(self):
    policies = list(self.Run(
        'access-context-manager policies list '
        '    --format disable '
        '    --organization ' + self.ORG_ID))
    self.assertEqual(len(policies), 1)
    policy_ref = resources.REGISTRY.Parse(
        policies[0].name, collection='accesscontextmanager.accessPolicies')

    with self._SetPolicyProperty(policy_ref.Name()):
      with self._CreateLevel() as level_id:
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level ' + level_id)
        self._UpdateLevel(level_id, 'My Level Redux ' + level_id)
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level Redux ' + level_id)
        with self._CreateZone() as zone_id:
          zone = self._DescribeZone(zone_id)
          self.assertEqual(zone.title, 'My Zone ' + zone_id)
          self._UpdateZone(zone_id, 'My Zone Redux ' + zone_id)
          zone = self._DescribeZone(zone_id)
          self.assertEqual(zone.title, 'My Zone Redux ' + zone_id)


if __name__ == '__main__':
  test_case.main()
