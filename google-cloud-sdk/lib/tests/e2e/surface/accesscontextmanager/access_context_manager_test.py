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
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import test_case


def _GetResourceName(prefix):
  return next(e2e_utils.GetResourceNameGenerator(prefix, delimiter='_')).upper()


class AccessContextManagerE2eTests(e2e_base.WithServiceAuth,
                                   cli_test_base.CliTestBase):

  ORG_ID = '1054311078602'
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

  PROJECT_NUMBER = '175742511250'

  # Requires an already-set-up regular perimeter, in case it runs multiple times
  # simultaneously (a single project can only belong to one regular perimeter,
  # but many bridge perimeters; however, to belong to a bridge perimeter, it
  # needs to belong to one regular perimeter).

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self._policy_id = None

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
               '    --perimeter-type bridge '
               '    --title "My Perimeter {perimeter}" '
               '    --resources projects/{project} '
               '   {perimeter}'.format(
                   project=self.PROJECT_NUMBER, perimeter=perimeter_id))
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

  def _ResetDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run reset '
                    '    {}'.format(perimeter_id))

  def _DropDryRunPerimeter(self, perimeter_id):
    return self.Run('access-context-manager perimeters dry-run drop '
                    '    {}'.format(perimeter_id))

  def _CommitDryRunConfig(self):
    full_policy_id = self._GetTestPolicyId()
    just_policy_number = full_policy_id[full_policy_id.find('/') + 1:]
    return self.Run('access-context-manager perimeters dry-run commit '
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
                   '    --organization ' + self.ORG_ID))
      self.assertEqual(len(policies), 1)
      policy_ref = resources.REGISTRY.Parse(
          policies[0].name, collection='accesscontextmanager.accessPolicies')
      self._policy_id = policy_ref.Name()
    return self._policy_id

  def testAccessContextManager(self):
    policy_id = self._GetTestPolicyId()
    with self._SetPolicyProperty(policy_id):
      if self.track == calliope_base.ReleaseTrack.ALPHA or self.track == calliope_base.ReleaseTrack.BETA:
        # pylint: disable=using-constant-test
        if False:  # TODO(b/150383794): Re-enable tests for ReplaceAccessLevels.
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
        with self._CreateCustomLevel() as level_id:
          level = self._DescribeLevel(level_id)
          self.assertEqual(level.title, 'My Level ' + level_id)
          self._UpdateCustomLevel(level_id, 'My Level Redux ' + level_id)
          level = self._DescribeLevel(level_id)
          self.assertEqual(level.title, 'My Level Redux ' + level_id)
      with self._CreateBasicLevel() as level_id:
        level = self._DescribeLevel(level_id)
        self.assertEqual(level.title, 'My Level ' + level_id)
        self._UpdateBasicLevel(level_id, 'My Level Redux ' + level_id)
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
    if (self.track is not calliope_base.ReleaseTrack.ALPHA and
        self.track is not calliope_base.ReleaseTrack.BETA):
      return
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

  def testServicePerimeterDryRunCreateAndDelete(self):
    if (self.track is not calliope_base.ReleaseTrack.ALPHA and
        self.track is not calliope_base.ReleaseTrack.BETA):
      return
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

  def testServicePerimeterDryRunCreateAndReset(self):
    if (self.track is not calliope_base.ReleaseTrack.ALPHA and
        self.track is not calliope_base.ReleaseTrack.BETA):
      return
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._DescribeDryRunPerimeter(perimeter_id)
        self._ResetDryRunPerimeter(perimeter_id)
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

  def testServicePerimeterDryRunCreateAndDrop(self):
    if (self.track is not calliope_base.ReleaseTrack.ALPHA and
        self.track is not calliope_base.ReleaseTrack.BETA):
      return
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

  def testServicePerimeterDryRunCreateAndCommit(self):
    if (self.track is not calliope_base.ReleaseTrack.ALPHA and
        self.track is not calliope_base.ReleaseTrack.BETA):
      return
    perimeter_id = _GetResourceName('DRY_RUN_PERIMETER')
    try:
      with self._SetPolicyProperty(self._GetTestPolicyId()):
        self._CreateDryRunPerimeter(perimeter_id)
        self._CommitDryRunConfig()
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


class AccessContextManagerE2eTestsBeta(AccessContextManagerE2eTests):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class AccessContextManagerE2eTestsAlpha(AccessContextManagerE2eTests):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
