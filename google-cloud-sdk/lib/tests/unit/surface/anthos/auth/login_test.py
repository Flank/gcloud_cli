# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""anthos auth login tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.anthos import anthoscli_backend
from tests.lib import test_case
from tests.lib.surface.anthos import test_base as anthos_test_base


class LoginTest(anthos_test_base.AuthUnitTestBase):

  def SetUp(self):
    self.StartObjectPatch(anthoscli_backend,
                          'GetFileOrURL',
                          return_value=('my-login-config.yaml', None, False))
    self.StartObjectPatch(anthoscli_backend,
                          'GetPreferredAuthForCluster',
                          return_value=('oidc1', None, None))

  def testLoginWithDefaults(self):
    self.Run('anthos auth login  --cluster my-test-cluster '
             '--login-config my-login-config.yaml')
    self.AssertValidBinaryCall(
        env={'COBRA_SILENCE_USAGE': 'true', 'GCLOUD_AUTH_PLUGIN': 'true'},
        command_args=[
            anthos_test_base._MOCK_ANTHOS_AUTH_BINARY,
            'login',
            '--cluster',
            'my-test-cluster',
            '--login-config',
            'my-login-config.yaml',
            '--preferred-auth',
            'oidc1',])
    self.AssertErrContains('Configuring Anthos authentication')

  def testLoginDryRun(self):
    self.Run('anthos auth login  --cluster my-test-cluster '
             '--login-config my-login-config.yaml --dry-run')
    self.AssertValidBinaryCall(
        env={'COBRA_SILENCE_USAGE': 'true', 'GCLOUD_AUTH_PLUGIN': 'true'},
        command_args=[
            anthos_test_base._MOCK_ANTHOS_AUTH_BINARY,
            'login',
            '--cluster',
            'my-test-cluster',
            '--login-config',
            'my-login-config.yaml',
            '--dry-run',
            '--preferred-auth',
            'oidc1',])
    self.AssertErrContains('Configuring Anthos authentication')

  def testLoginExplicit(self):
    self.Run('anthos auth login  --cluster my-test-cluster '
             '--login-config my-login-config.yaml --login-config-cert mycert '
             '--kubeconfig my-kube.yaml --user testuser --set-preferred-auth')
    self.AssertValidBinaryCall(
        env={'COBRA_SILENCE_USAGE': 'true', 'GCLOUD_AUTH_PLUGIN': 'true'},
        command_args=[
            anthos_test_base._MOCK_ANTHOS_AUTH_BINARY,
            'login',
            '--cluster',
            'my-test-cluster',
            '--kubeconfig',
            'my-kube.yaml',
            '--login-config',
            'my-login-config.yaml',
            '--login-config-cert',
            'mycert',
            '--user',
            'testuser',
            '--preferred-auth',
            'oidc1',])
    self.AssertErrContains('Configuring Anthos authentication')


if __name__ == '__main__':
  test_case.main()
