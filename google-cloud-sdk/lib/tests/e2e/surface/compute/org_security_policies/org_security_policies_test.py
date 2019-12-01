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

import re
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base


def _UniqueName(name):
  return next(
      e2e_utils.GetResourceNameGenerator(
          prefix='compute-security-policy-test-' + name))


ORGANIZATION_ID = 486696711978


class OrgSecurityPoliciesTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @test_case.Filters.skipAlways('Breaking apitools regen', 'b/144098296')
  def testSecurityPolicy(self):
    try:
      # Create a security policy.
      self.Run(
          'compute org-security-policies create --organization={0} --description={1}'
          .format(ORGANIZATION_ID, 'test-sp'))
      create_sp = self.GetErr()
      sp_id = ''
      if create_sp.startswith('Created'):
        self_link = re.search(r'\[(.*?)\]', create_sp).group(1)
        sp_id = self_link.split('/')[-1]
      self.assertNotEqual(sp_id, '')

      self.ClearOutput()
      # Describe security policy.
      security_policy_describe = self.Run(
          'compute org-security-policies describe {0}'.format(sp_id))[0]
      self.assertEqual(security_policy_describe.description, 'test-sp')

      self.ClearOutput()
      # Patch
      self.Run(
          'compute org-security-policies update {0} --description={1}'.format(
              sp_id, 'test-sp-1'))
      security_policy_describe = self.Run(
          'compute org-security-policies describe {0}'.format(sp_id))[0]
      self.assertEqual(security_policy_describe.description, 'test-sp-1')

      # Add Rule
      self.Run(
          'compute org-security-policies rules create {0}  --action={1}  '
          '--security-policy={2} --src-ip-ranges={3} --dest-ports={4}'.format(
              10, 'allow', sp_id, '10.0.0.0/24', 'tcp:80-90'))
      # Patch Rule
      self.Run(
          'compute org-security-policies rules update {0}  --action={1}  '
          '--security-policy={2} --src-ip-ranges={3} --dest-ports={4}'.format(
              10, 'deny', sp_id, '10.0.0.0/24', 'tcp:90-100'))
      # Delete Rule
      self.Run(
          'compute org-security-policies rules delete {0} --security-policy={1}'
          .format(10, sp_id))

      # Add association
      self.Run('compute org-security-policies associations create --name={0} '
               '--security-policy={1} --organization={2} '
               '--replace-association-on-target'.format('test-association',
                                                        sp_id, ORGANIZATION_ID))
      # List associations
      self.Run(
          'compute org-security-policies associations list  --organization={0}'
          .format(ORGANIZATION_ID))
      association_list = self.GetOutput().splitlines()
      self.assertGreater(len(association_list), 0)

      # Remove association
      # Only one association is allowed for the organization. It is possible
      # the association has been removed in different runs in python 2 or 3,
      # thus it might throw exception.
      self.Run('compute org-security-policies associations delete {0} '
               ' --security-policy={1}'.format('test-association', sp_id))
    finally:
      # Delete the security policy.
      self.Run('compute org-security-policies delete {0}'.format(sp_id))


if __name__ == '__main__':
  e2e_test_base.main()
