# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import os
import os.path
import tempfile

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.code import yaml_helper
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import retry
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib.surface.iam import e2e_test_base
import six


@contextlib.contextmanager
def EnvironmentVariable(key, value):
  if key in os.environ:
    old_value = os.environ[key]

    def Reset():
      os.environ[key] = old_value

    revert = Reset
  else:

    def Clear():
      del os.environ[key]

    revert = Clear

  try:
    os.environ[key] = value
    yield
  finally:
    revert()


_LOCAL_DEVELOPMENT_DIR = (
    os.environ['TEST_TMPDIR']
    if 'TEST_TMPDIR' in os.environ else tempfile.mkdtemp())
_LOCAL_CREDENTIAL_FILE_PATH = os.path.join(
    _LOCAL_DEVELOPMENT_DIR, 'local_developer_application_credential.json')
_SKAFFOLD_FILE_PATH = os.path.join(_LOCAL_DEVELOPMENT_DIR, 'skaffold.yaml')


class SetupTest(e2e_base.WithServiceAuth, e2e_base.WithServiceAccountFile):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.account_name_generator = e2e_utils.GetResourceNameGenerator(
        prefix='dev')

  def SetUp(self):
    account_name = next(self.account_name_generator)
    self.local_account_email = ('{0}@{1}.iam.gserviceaccount.com'.format(
        account_name, self.Project()))
    properties.VALUES.core.disable_prompts.Set(True)

  def TearDown(self):
    with e2e_base.RefreshTokenAuth() as _:
      keys = self.Run(('iam service-accounts keys list '
                       '--iam-account={0}').format(self.local_account_email))

      user_keys = (
          key for key in keys if six.text_type(key.keyType) == 'USER_MANAGED')
      for key in user_keys:
        self.Run(
            'iam service-accounts keys delete {0} --iam-account={1}'.format(
                key.name, self.local_account_email))

      retry.RetryOnException(  # IAM policy can't accommodate concurrent changes
          f=self.Run,
          max_retrials=5,
          sleep_ms=500,
          exponential_sleep_multiplier=2)(
              'projects remove-iam-policy-binding {0} '
              '--role roles/editor --member serviceAccount:{1}'.format(
                  self.Project(), self.local_account_email))

      self.Run('iam service-accounts delete {email}'.format(
          email=self.local_account_email))

  def testCreateServiceAccountCredential(self):
    refresh_token = e2e_base.RefreshTokenAuth()
    local_credential_variable = EnvironmentVariable(
        'LOCAL_CREDENTIAL_PATH', _LOCAL_CREDENTIAL_FILE_PATH)

    pod_and_services_path = os.path.join(_LOCAL_DEVELOPMENT_DIR,
                                         'pods_and_services.yaml')
    with refresh_token as auth, local_credential_variable as _:
      command = ('code export --project {0} --kubernetes-file={1} '
                 '--skaffold-file={2} --service-account={3}').format(
                     auth.Project(), pod_and_services_path, _SKAFFOLD_FILE_PATH,
                     self.local_account_email)
      self.Run(command)
      self.WriteInput('y')

    with open(pod_and_services_path) as pods_and_services_file:
      pods_and_services = list(yaml.load_all(pods_and_services_file))

    pod_specs = [
        spec for spec in pods_and_services if spec['kind'] == 'Deployment'
    ]
    self.assertGreaterEqual(len(pod_specs), 1)
    for spec in pod_specs:
      env_vars = yaml_helper.GetAll(
          spec, path=('spec', 'template', 'spec', 'containers', 'env'))
      credential_vars = (
          var['value']
          for var in env_vars
          if var['name'] == 'GOOGLE_APPLICATION_CREDENTIALS')
      env_var_path = next(credential_vars, None)
      self.assertEqual(
          env_var_path, '/etc/local_development_credential/'
          'local_development_service_account.json')

    secret_specs = [
        spec for spec in pods_and_services if spec['kind'] == 'Secret'
    ]
    self.assertEqual(len(secret_specs), 1)
    self.assertEqual(secret_specs[0]['metadata']['name'],
                     'local-development-credential')


if __name__ == '__main__':
  e2e_test_base.main()
