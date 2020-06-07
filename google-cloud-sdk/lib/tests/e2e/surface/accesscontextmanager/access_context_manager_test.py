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
"""E2E tests for `gcloud access-context-manager` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util.platforms import OperatingSystem
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


def _GetResourceName(prefix):
  return next(e2e_utils.GetResourceNameGenerator(prefix, delimiter='_')).upper()


class AccessContextManagerE2eTests(e2e_base.WithServiceAuth,
                                   cli_test_base.CliTestBase):
  # A mapping of which billing project to use for this instance of e2e test
  # based on the operating system and release track.
  SHARDING_QUOTA_PROJECT = {
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.GA: '888422664032',
          calliope_base.ReleaseTrack.BETA: '334969862',
          calliope_base.ReleaseTrack.ALPHA: '227997894940',
      },
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.GA: '502734576903',
          calliope_base.ReleaseTrack.BETA: '937099147667',
          calliope_base.ReleaseTrack.ALPHA: '686404499936',
      },
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.GA: '618624148297',
          calliope_base.ReleaseTrack.BETA: '974650614028',
          calliope_base.ReleaseTrack.ALPHA: '86178890000',
      }
  }
  # A mapping of which organization to use for this instance of e2e test based
  # on the operating system and release track.
  SHARDING_ORG = {
      OperatingSystem.LINUX: {
          calliope_base.ReleaseTrack.GA: '76738297746',
          calliope_base.ReleaseTrack.BETA: '340595059913',
          calliope_base.ReleaseTrack.ALPHA: '191131751739',
      },
      OperatingSystem.WINDOWS: {
          calliope_base.ReleaseTrack.GA: '995906764022',
          calliope_base.ReleaseTrack.BETA: '45731270610',
          calliope_base.ReleaseTrack.ALPHA: '221222174612',
      },
      OperatingSystem.MACOSX: {
          calliope_base.ReleaseTrack.GA: '507192639236',
          calliope_base.ReleaseTrack.BETA: '880393349060',
          calliope_base.ReleaseTrack.ALPHA: '62963706250',
      }
  }

  BASIC_LEVEL_SPEC = ('[{"ipSubnetworks": ["8.8.8.8/32"]}, '
                      '{"regions": ["CA", "US"]}, '
                      '{"members": ["user:example@example.com"]}, '
                      '{"devicePolicy": {"requireScreenlock": true}}]')
  CUSTOM_LEVEL_SPEC = 'expression: "inIpRange(origin.ip, [\'8.8.8.8/32\'])"'

  ACCESS_LEVEL_SPECS = """
    [
      {{
        "name": "accessPolicies/{policy}/accessLevels/{basicLevel}",
        "title": "My Basic Level {basicLevel}",
        "description": "level description 1",
        "basic": {{
          "conditions": [
                {{"ipSubnetworks": ["8.8.8.8/32"]}},
                {{"members": ["user:example@example.com"]}}
          ],
          "combiningFunction": "AND"
        }}
      }},
      {{
        "name": "accessPolicies/{policy}/accessLevels/{customLevel}",
        "title": "My Custom Level {customLevel}",
        "description": "level description 2",
        "custom": {{
          "expr": {{
            "expression": "inIpRange(origin.ip, ['8.8.8.8/32'])"
          }}
        }}
      }}
    ]
  """

  DEFAULT_ORG_ID = '1054311078602'
  DEFAULT_PROJECT_NUMBER = '175742511250'

  # Requires an already-set-up regular perimeter, in case it runs multiple times
  # simultaneously (a single project can only belong to one regular perimeter,
  # but many bridge perimeters; however, to belong to a bridge perimeter, it
  # needs to belong to one regular perimeter).

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._policy_id = None
    self._current_org = self.SHARDING_ORG.get(OperatingSystem.Current(),
                                              {}).get(self.track,
                                                      self.DEFAULT_ORG_ID)
    self._current_billing_project = self.SHARDING_QUOTA_PROJECT.get(
        OperatingSystem.Current(), {}).get(self.track,
                                           self.DEFAULT_PROJECT_NUMBER)

  @contextlib.contextmanager
  def _SetBillingProject(self):
    properties.VALUES.billing.quota_project.Set(self._current_billing_project)
    try:
      yield
    finally:
      properties.VALUES.billing.quota_project.Set(None)

  @contextlib.contextmanager
  def _SetPolicyProperty(self, policy):
    properties.VALUES.access_context_manager.policy.Set(policy)
    try:
      yield
    finally:
      properties.VALUES.access_context_manager.policy.Set(None)

  @contextlib.contextmanager
  def _CreateBasicLevel(self):
    level_spec_file = self.Touch(
        self.temp_path, 'level.yaml', contents=self.BASIC_LEVEL_SPEC)
    level_id = _GetResourceName('LEVEL')
    try:
      self.Run('access-context-manager levels create'
               '    --title "My Level {level}" '
               '    --basic-level-spec {spec} '
               '   {level}'.format(spec=level_spec_file, level=level_id))
      yield level_id
    finally:
      self.Run('access-context-manager levels delete '
               '    --quiet '
               '   {}'.format(level_id))

  @contextlib.contextmanager
  def _CreateCustomLevel(self):
    level_spec_file = self.Touch(
        self.temp_path, 'level.yaml', contents=self.CUSTOM_LEVEL_SPEC)
    level_id = _GetResourceName('LEVEL')
    try:
      self.Run('access-context-manager levels create'
               '    --title "My Level {level}" '
               '    --custom-level-spec {spec} '
               '   {level}'.format(spec=level_spec_file, level=level_id))
      yield level_id
    finally:
      self.Run('access-context-manager levels delete '
               '    --quiet '
               '   {}'.format(level_id))

  def _UpdateBasicLevel(self, level_id, new_title):
    level_spec_file = self.Touch(
        self.temp_path, 'level.yaml', contents=self.BASIC_LEVEL_SPEC)
    return self.Run('access-context-manager levels update '
                    '    --title "{title}" '
                    '    --basic-level-spec {spec} '
                    '    {level}'.format(
                        title=new_title, level=level_id, spec=level_spec_file))

  def _UpdateCustomLevel(self, level_id, new_title):
    level_spec_file = self.Touch(
        self.temp_path, 'level.yaml', contents=self.CUSTOM_LEVEL_SPEC)
    return self.Run('access-context-manager levels update '
                    '    --title "{title}" '
                    '    --custom-level-spec {spec} '
                    '    {level}'.format(
                        title=new_title, level=level_id, spec=level_spec_file))

  def _DescribeLevel(self, level_id):
    return self.Run(
        'access-context-manager levels describe '
        '    --format disable '  # Disable format to get a return value
        '    {}'.format(level_id))

  @contextlib.contextmanager
  def _ReplaceLevels(self, policy):
    basic_level_id = _GetResourceName('BASICLEVEL')
    custom_level_id = _GetResourceName('CUSTOMLEVEL')
    level_spec_file = self.Touch(
        self.temp_path,
        'level.yaml',
        contents=self.ACCESS_LEVEL_SPECS.format(
            policy=policy,
            basicLevel=basic_level_id,
            customLevel=custom_level_id))
    try:
      self.Run(
          'access-context-manager levels replace-all --source-file {}'.format(
              level_spec_file))
      yield (basic_level_id, custom_level_id)
    finally:
      self.Run('access-context-manager levels delete '
               '    --quiet '
               '   {}'.format(basic_level_id))
      self.Run('access-context-manager levels delete '
               '    --quiet '
               '   {}'.format(custom_level_id))

  @contextlib.contextmanager
  def _CreatePerimeter(self):
    perimeter_id = _GetResourceName('PERIMETER')
    try:
      self.Run('access-context-manager perimeters create'
               '    --title "My Perimeter {perimeter}" '
               '   {perimeter}'.format(
                   perimeter=perimeter_id))
      yield perimeter_id
    finally:
      self.Run('access-context-manager perimeters delete '
               '    --quiet '
               '   {}'.format(perimeter_id))

  def _UpdatePerimeter(self, perimeter_id, new_title):
    return self.Run('access-context-manager perimeters update '
                    '    --title "{}" '
                    '    {}'.format(new_title, perimeter_id))

  def _DescribePerimeter(self, perimeter_id):
    return self.Run(
        'access-context-manager perimeters describe '
        '    --format disable '  # Disable format to get a return value
        '    {}'.format(perimeter_id))

  def _CreateDryRunPerimeter(self, perimeter_id):
    return self.Run(
        'access-context-manager perimeters dry-run create'
        '    --perimeter-type "regular" '
        '    --perimeter-title "My Perimeter {perimeter}" '
        '    --perimeter-restricted-services "bigquery.googleapis.com" '
        '   {perimeter}'.format(perimeter=perimeter_id))

  def _UpdateDryRunPerimeter(self, perimeter_id, restricted_service_to_add):
    return self.Run('access-context-manager perimeters dry-run update '
                    '    --add-restricted-services "{}" '
                    '    {}'.format(restricted_service_to_add, perimeter_id))

  def _DeleteDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run delete '
                    '    {}'.format(perimeter_id))

  def _EnforceDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run enforce '
                    '    {}'.format(perimeter_id))

  def _DropDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run drop '
                    '    {}'.format(perimeter_id))

  def _EnforceAllDryRunPerimeters(self):
    full_policy_id = self._GetTestPolicyId()
    just_policy_number = full_policy_id[full_policy_id.find('/') + 1:]
    return self.Run('access-context-manager perimeters dry-run enforce-all '
                    ' --policy {}'.format(just_policy_number))

  def _DescribeDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run describe '
                    '    {}'.format(perimeter_id))

  def _DestroyPerimeter(self, perimeter_id):
    full_policy_id = self._GetTestPolicyId()
    just_policy_number = full_policy_id[full_policy_id.find('/') + 1:]
    self.Run('access-context-manager perimeters delete '
             '    --policy {}'
             '    --quiet '
             '   {}'.format(just_policy_number, perimeter_id))

  def _GetTestPolicyId(self):
    if self._policy_id is None:
      policies = list(
          self.Run('access-context-manager policies list '
                   '    --format disable '
                   '    --organization ' + self._current_org))
      self.assertEqual(len(policies), 1)
      policy_ref = resources.REGISTRY.Parse(
          policies[0].name, collection='accesscontextmanager.accessPolicies')
      self._policy_id = policy_ref.Name()
    return self._policy_id

  def testAccessContextManager(self):
    policy_id = self._GetTestPolicyId()
    with self._SetPolicyProperty(policy_id):
      if self.track == calliope_base.ReleaseTrack.ALPHA or self.track == calliope_base.ReleaseTrack.BETA:
        # TODO(b/150383794): Re-enable tests for ReplaceAccessLevels.
        # pylint: disable=using-constant-test
        if False:
          # NOTE: Currently the replace levels includes a custom level.
          # If replace levels goes to GA before custom levels, we will need to
          # modify the replaceAll GA test to only reference basic levels.
          with self._ReplaceLevels(policy_id) as (basic_level_id,
                                                  custom_level_id):
            basic_level = self._DescribeLevel(basic_level_id)
            self.assertEqual(basic_level.title,
                             'My Basic Level ' + basic_level_id)
            custom_level = self._DescribeLevel(custom_level_id)
            self.assertEqual(custom_level.title,
                             'My Custom Level ' + custom_level_id)
        # pylint: enable=using-constant-test
      with self._CreateBasicLevel() as level_id:
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level ' + level_id)
        self._UpdateBasicLevel(level_id, 'My Level Redux ' + level_id)
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level Redux ' + level_id)
      with self._CreateCustomLevel() as level_id:
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level ' + level_id)
        self._UpdateCustomLevel(level_id, 'My Level Redux ' + level_id)
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level Redux ' + level_id)
      with self._CreatePerimeter() as perimeter_id:
        perimeter = self._DescribePerimeter(perimeter_id)
        self.assertEqual(perimeter.title, 'My Perimeter ' + perimeter_id)
        self._UpdatePerimeter(perimeter_id,
                              'My Perimeter Redux ' + perimeter_id)
        perimeter = self._DescribePerimeter(perimeter_id)
        self.assertEqual(perimeter.title, 'My Perimeter Redux ' + perimeter_id)

  def testServicePerimeterDryRunCreateAndUpdate(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        self._UpdateDryRunPerimeter(perimeter_id, 'bigtable.googleapis.com')
        self._DescribeDryRunPerimeter(perimeter_id)
        # This is the combined output of the two 'describe' calls.
        self.AssertOutputEquals("""\
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigquery.googleapis.com
  +bigtable.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
""".format(perimeter=perimeter_id))
    finally:
      self._DestroyPerimeter(perimeter_id)

  def testServicePerimeterDryRunCreateAndUpdateWithInheritance(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    policy_id = self._GetTestPolicyId()
    with self._SetPolicyProperty(policy_id):
      with self._CreateBasicLevel() as level_id:
        try:
          self.Run('access-context-manager perimeters create'
                   '    --perimeter-type regular '
                   '    --title "My Perimeter {perimeter}" '
                   '    --restricted-services "storage.googleapis.com" '
                   '    --access-levels "{level_id}" '
                   '   {perimeter}'.format(
                       level_id=level_id, perimeter=perimeter_id))
          self._DescribeDryRunPerimeter(perimeter_id)
          self._UpdateDryRunPerimeter(perimeter_id, 'bigtable.googleapis.com')
          self._DescribeDryRunPerimeter(perimeter_id)
          # This is the combined output of the two 'describe' calls.
          self.AssertOutputEquals("""\
This Service Perimeter does not have an explicit dry-run mode configuration. The enforcement config will be used as the dry-run mode configuration.
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
   storage.googleapis.com
accessLevels:
   accessPolicies/{policy_id}/accessLevels/{level_id}
vpcAccessibleServices:
   NONE
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigtable.googleapis.com
   storage.googleapis.com
accessLevels:
   accessPolicies/{policy_id}/accessLevels/{level_id}
vpcAccessibleServices:
   NONE
""".format(perimeter=perimeter_id, level_id=level_id, policy_id=policy_id))
        finally:
          self._DestroyPerimeter(perimeter_id)

  def testServicePerimeterDryRunCreateAndDelete(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        self._DeleteDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        # This is the combined output of the two 'describe' calls.
        self.AssertOutputEquals("""\
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
This Service Perimeter has been marked for deletion dry-run mode.
""".format(perimeter=perimeter_id))
    finally:
      self._DestroyPerimeter(perimeter_id)

  def testServicePerimeterDryRunCreateAndDrop(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        self._DropDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        # This is the combined output of the two 'describe' calls.
        self.AssertOutputEquals("""\
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
This Service Perimeter has no dry-run or enforcement mode config.
""".format(perimeter=perimeter_id))
    finally:
      self._DestroyPerimeter(perimeter_id)

  def testServicePerimeterDryRunCreateAndEnforce(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        self._EnforceDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        # This is the combined output of the two 'describe' calls.
        self.AssertOutputEquals("""\
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
  +bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
This Service Perimeter does not have an explicit dry-run mode configuration. The enforcement config will be used as the dry-run mode configuration.
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
   bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
""".format(perimeter=perimeter_id))
    finally:
      self._DestroyPerimeter(perimeter_id)

  def testServicePerimeterDryRunCreateAndEnforceAll(self):
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._EnforceAllDryRunPerimeters()
        self._DescribeDryRunPerimeter(perimeter_id)
        self.AssertOutputEquals("""\
This Service Perimeter does not have an explicit dry-run mode configuration. The enforcement config will be used as the dry-run mode configuration.
name: {perimeter}
title: My Perimeter {perimeter}
type: PERIMETER_TYPE_REGULAR
resources:
   NONE
restrictedServices:
   bigquery.googleapis.com
accessLevels:
   NONE
vpcAccessibleServices:
   NONE
""".format(perimeter=perimeter_id))
    finally:
      self._DestroyPerimeter(perimeter_id)


@test_case.Filters.skipAlways('Write quota exhaustion', 'b/152382402')
class AccessContextManagerE2eTestsBeta(AccessContextManagerE2eTests):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


@test_case.Filters.skipAlways('Write quota exhaustion', 'b/152382402')
class AccessContextManagerE2eTestsAlpha(AccessContextManagerE2eTests):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
