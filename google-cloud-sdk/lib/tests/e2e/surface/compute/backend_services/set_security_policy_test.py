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
"""Integration tests for setting security-policies."""

from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


def _UniqueName(name):
  return next(
      e2e_utils.GetResourceNameGenerator(
          prefix='compute-set-security-policy-test-' + name))


class SetSecurityPolicyTestAlpha(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.command_name = 'set-security-policy'

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass

  @contextlib.contextmanager
  def _HttpHealthCheck(self, name):
    try:
      yield self.RunCompute('http-health-checks', 'create', name)
    finally:
      self.CleanUpResource('http-health-checks', name)

  @contextlib.contextmanager
  def _BackendService(self, name, http_health_check):
    try:
      yield self.RunCompute(
          'backend-services', 'create', name,
          '--load-balancing-scheme', 'external',
          '--http-health-checks', http_health_check,
          '--protocol=HTTP',
          '--global')
    finally:
      self.CleanUpResource('backend-services', name, '--global')

  @contextlib.contextmanager
  def _SecurityPolicy(self, name):
    try:
      yield self.RunCompute('security-policies', 'create', name)
    finally:
      self.CleanUpResource('security-policies', name)

  def testSetSecurityPolicyForBackendService(self):
    hc_name = _UniqueName('hc')
    bs_name = _UniqueName('bs')
    sp_name = _UniqueName('sp')

    with self._HttpHealthCheck(hc_name), self._BackendService(
        bs_name, hc_name), self._SecurityPolicy(sp_name):

      # Set security policy
      self.Run("""
          compute backend-services {0} {1}
            --security-policy {2}
            --global
          """.format(self.command_name, bs_name, sp_name))
      result = self.Run('compute backend-services describe {0} --global'
                        .format(bs_name))
      self.assertEqual(sp_name, result.securityPolicy.rsplit('/', 1)[-1])

      # Clear security policy
      self.Run("""
          compute backend-services {0} {1}
            --security-policy ''
            --global
          """.format(self.command_name, bs_name))
      result = self.Run('compute backend-services describe {0} --global'
                        .format(bs_name))
      self.assertIsNone(result.securityPolicy)


class SetSecurityPolicyTestBeta(SetSecurityPolicyTestAlpha):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.command_name = 'update'


if __name__ == '__main__':
  e2e_test_base.main()
