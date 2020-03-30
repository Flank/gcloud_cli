# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Integration tests for organization security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


ORGANIZATION_ID = 486696711978


class OrgSecurityPoliciesTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.display_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='compute-security-policy-test')
    )

  def testSecurityPolicy(self):
    try:
      # Create a security policy.
      self.Run('compute org-security-policies create --organization={0} '
               '--description={1} --display-name={2}'.format(
                   ORGANIZATION_ID, 'test-e2e-sp', self.display_name))
      self.AssertErrContains('SUCCESS')
      self.ClearErr()

      # Describe security policy.
      security_policy_describe = self.Run(
          'compute org-security-policies describe {0} --organization={1}'
          .format(self.display_name, ORGANIZATION_ID))[0]
      self.assertEqual(security_policy_describe.description, 'test-e2e-sp')
      self.ClearErr()

      # Patch
      self.Run(
          'compute org-security-policies update {0} --description={1} --organization={2}'
          .format(self.display_name, 'test-e2e-sp-1', ORGANIZATION_ID))
      self.AssertErrContains('SUCCESS')
      self.ClearErr()
      security_policy_describe = self.Run(
          'compute org-security-policies describe {0} --organization={1}'
          .format(self.display_name, ORGANIZATION_ID))[0]
      self.assertEqual(security_policy_describe.description, 'test-e2e-sp-1')
      self.ClearErr()

      # Add Rule
      self.Run(
          'compute org-security-policies rules create {0}  --action={1}  '
          '--security-policy={2} --src-ip-ranges={3} --dest-ports={4} --organization={5}'
          .format(10, 'allow', self.display_name, '10.0.0.0/24', 'tcp:80-90',
                  ORGANIZATION_ID))
      self.AssertNewErrContains('SUCCESS')
      self.ClearErr()

      # Patch Rule
      self.Run(
          'compute org-security-policies rules update {0}  --action={1}  '
          '--security-policy={2} --src-ip-ranges={3} --dest-ports={4} --organization={5}'
          .format(10, 'deny', self.display_name, '10.0.0.0/24', 'tcp:90-100',
                  ORGANIZATION_ID))
      self.AssertNewErrContains('SUCCESS')
      self.ClearErr()

      # Delete Rule
      self.Run(
          'compute org-security-policies rules delete {0} --security-policy={1}'
          ' --organization={2}'.format(10, self.display_name, ORGANIZATION_ID))
      self.AssertNewErrContains('SUCCESS')
      self.ClearErr()

      # Add association
      self.Run('compute org-security-policies associations create --name={0} '
               '--security-policy={1} --organization={2} '
               '--replace-association-on-target'.format('test-association',
                                                        self.display_name,
                                                        ORGANIZATION_ID))
      self.AssertNewErrContains('SUCCESS')
      self.ClearErr()

      # List associations
      self.Run(
          'compute org-security-policies associations list  --organization={0}'
          .format(ORGANIZATION_ID))
      association_list = self.GetOutput().splitlines()
      self.assertGreater(len(association_list), 0)
      self.ClearErr()

      try:
        # Remove association
        self.Run('compute org-security-policies associations delete {0} '
                 ' --security-policy={1} --organization={2} '.format(
                     'test-association', self.display_name, ORGANIZATION_ID))
        self.AssertNewErrContains('SUCCESS')
      except:  # pylint: disable=bare-except
        # It is expected that removing association would throw exception since
        # if the test has multiple runs in parallel, there is a high chance the
        # association is replaced. Just ignore the exception.
        pass
    finally:
      # Delete the security policy.
      self.ClearErr()
      self.Run(
          'compute org-security-policies delete {0} --organization={1}'.format(
              self.display_name, ORGANIZATION_ID))
      self.AssertNewErrContains('SUCCESS')


if __name__ == '__main__':
  e2e_test_base.main()
