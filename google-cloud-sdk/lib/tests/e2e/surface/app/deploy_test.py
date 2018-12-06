# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for dev_app_server for java and python."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import glob
import json
import os
import shutil
import subprocess

from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import exec_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.gsutil import gsutil_e2e_utils


class DeployConfigTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can deploy config files (cron, dispatch etc)."""

  TIMEOUT = 60  # 1 minute

  def SetUp(self):
    self.test_config_dir = self.Resource('tests', 'e2e', 'surface', 'app',
                                         'test_data', 'app_engine_config_files')

  def TearDown(self):
    pass

  @sdk_test_base.Retry(
      why=('App deploy is flaky but eventually consistent.'),
      max_retrials=5,
      sleep_ms=500)
  def _deployConfig(self, filename):
    config_path = os.path.join(self.test_config_dir, filename)
    self.ExecuteScript(
        'gcloud',
        ['--verbosity=debug', 'app', 'deploy', config_path],
        timeout=DeployConfigTests.TIMEOUT)

  def testDeployCron(self):
    self._deployConfig('cron.yaml')

  def testDeployQueue(self):
    self._deployConfig('queue.yaml')

  def testDeployDispatch(self):
    self._deployConfig('dispatch.yaml')

  def testDeployDos(self):
    self._deployConfig('dos.yaml')

  def testDeployIndex(self):
    self._deployConfig('index.yaml')


class DeployTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth):
  """Test we can deploy an app."""

  TIMEOUT = 240  # 4 minutes

  def SetUp(self):
    @sdk_test_base.Retry(
        why=('gsutil may return a 409 even if bucket creation succeeds'),
        max_retrials=3,
        sleep_ms=300)
    def _TestIdAndBucketName():
      # Identifier for this test, used for service names etc.
      self.test_id = next(e2e_utils.GetResourceNameGenerator('gaedeptest'))
      self.bucket_name = 'gs://' + self.test_id + 'bucket'
      self.ExecuteScript('gsutil', ['mb', self.bucket_name])
    _TestIdAndBucketName()
    self.test_dir = self.Resource('tests', 'e2e', 'surface', 'app', 'test_data')
    self.deployed_services = []  # To be cleaned up

  def TearDown(self):
    @sdk_test_base.Retry(
        why=('App delete is flaky but eventually consistent.'),
        max_retrials=3,
        sleep_ms=300)
    def DeleteService(service_id):
      self.ExecuteScript(
          'gcloud',
          ['--verbosity=debug', 'app', 'services', 'delete', service_id])
    # Deletes are somewhat flaky; this prevents resources from leaking
    for service_id in self.deployed_services:
      try:
        DeleteService(service_id)
      # Don't fail the test if service deletion fails for any reason.
      # The cleanup script will remove undeleted services anyway.
      except Exception as e:  # pylint: disable=broad-except
        log.error('Error {e} tearing down app service: {service}'
                  .format(e=e, service=service_id))
    try:
      self.ExecuteScript('gsutil', ['rb', self.bucket_name])
    except exec_utils.ExecutionError as e:
      log.error('Error {e} could not delete bucket [{bucket}].'
                .format(e=e, bucket=self.bucket_name))

  def _serviceIdFromAppName(self, app_name):
    return '{0}-{1}'.format(self.test_id, app_name.replace('_', '-'))

  def _deployStandardApp(self, app_name, versions=None, release_track=None):
    """Deploy an app to a particular service, can happen in parallel.

    Args:
      app_name: The name of the directory in test_data that contains the app.
          This app needs an app.yaml with no service assigned (default).
      versions: An optional list of version names.
      release_track: If there should be a release track (such as `beta`).

    Returns:
      Array of results of `gcloud app deploy' for reach version specified.
    """
    @sdk_test_base.Retry(why=('App deploy is flaky but eventually consistent.'),
                         max_retrials=5,
                         sleep_ms=500)
    def DeployService(args):
      """Gcloud execute with retries.."""
      return self.ExecuteScript('gcloud', args, timeout=DeployTests.TIMEOUT)

    with files.TemporaryDirectory() as tmpdir:
      result = []
      if versions is None:
        versions = [self.test_id]

      log.debug('Tmp Dir: [{0}].'.format(tmpdir))
      app_root = os.path.join(tmpdir, 'app')
      shutil.copytree(os.path.join(self.test_dir, app_name), app_root)
      appyaml_path = os.path.join(app_root, 'app.yaml')
      service_id = self._serviceIdFromAppName(app_name)
      with open(appyaml_path, 'a') as appyaml:
        appyaml.write('\nservice: {0}\n'.format(service_id))

      self.deployed_services.append(service_id)
      for version in versions:
        args = ['--verbosity=debug', 'app', 'deploy',
                '--version={0}'.format(version), appyaml_path]
        if release_track:
          args.insert(0, release_track)
        result.append(DeployService(args))

    return result

  def _getTrafficSplits(self, service_id):
    """Fetch the traffic splits for an app.

    Args:
      service_id: The name of the service for which to fetch traffic splits.

    Returns:
      A dict mapping version name to traffic split.
    """
    args = ['--verbosity', 'debug', 'app', 'versions', 'list', '--format=json',
            '--service={0}'.format(service_id)]
    result = self.ExecuteScript('gcloud', args, timeout=DeployTests.TIMEOUT)
    json_list = json.loads(result.stdout)

    return dict([(version['id'], version['traffic_split'])
                 for version in json_list])

  def testDeployPythonUsingApi(self):
    self._deployStandardApp('app_engine_python_data')

  def testDeployPythonUsingApiBeta(self):
    self._deployStandardApp('app_engine_python_data', release_track='beta')

  def testDeployPhpUsingApi(self):
    self._deployStandardApp('app_engine_php_data')

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires component app-engine-java
  @sdk_test_base.Filters.RunOnlyIfExecutablePresent('java')
  def testDeployJavaUsingApi(self):
    app_dir = os.path.join(self.test_dir, 'app_engine_java_xml_data')
    version = self.test_id
    args = ['--verbosity=debug', 'app', 'deploy',
            '--version={0}'.format(version), app_dir]
    self.ExecuteScript('gcloud', args, timeout=DeployTests.TIMEOUT)
    self.deployed_services.append('default')

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires component app-engine-go
  def testDeployGoUsingApi(self):
    """Deploy a standard Go app.

    Ensures that the staging step is invoked, since a depencency will be
    intentionally be placed outside the app directory -- in the GOPATH.

    The test is designed to fail if the staging step/vendoring fails.
    """
    encoding.SetEncodedValue(
        os.environ, 'GOPATH', os.path.join(self.test_dir, 'gopath'))
    try:
      self._deployStandardApp('app_engine_go_data')
    finally:
      encoding.SetEncodedValue(os.environ, 'GOPATH', None)

  def testTrafficSplit(self):
    app_name = 'app_engine_python_data'
    splits = {
        'v1': 0.5,
        'v2': 0.2,
        'v3': 0.3
    }
    splits_total = sum(splits.values())

    # Deploy multiple versions of an app.
    self._deployStandardApp(app_name, list(splits.keys()))
    service_id = self._serviceIdFromAppName(app_name)
    self.assertAlmostEqual(sum(self._getTrafficSplits(service_id).values()),
                           1,
                           delta=0.01)

    # Split traffic between the versions.
    args_splits = ','.join(
        ['{0}={1}'.format(v, s) for (v, s) in sorted(splits.items())])
    args = ['--verbosity', 'debug', 'app', 'services', 'set-traffic',
            service_id, '--splits', args_splits]
    self.ExecuteScript('gcloud', args, timeout=DeployTests.TIMEOUT)

    # Verify that the reported traffic split matches the expected traffic split.
    reported_splits = self._getTrafficSplits(service_id)
    for version, traffic in sorted(reported_splits.items()):
      self.assertTrue(version in splits)
      self.assertAlmostEqual(splits[version] / splits_total,
                             traffic,
                             delta=0.01)

  @sdk_test_base.Filters.RunOnlyIfExecutablePresent('git')
  def testDeployPythonWithGit(self):
    app_root = os.path.join(self.test_dir, 'app_engine_python_with_git')
    git_dir = os.path.join(app_root, '.git')

    try:
      with gsutil_e2e_utils.ModifiedGsutilStateDir(self.Account()):
        subprocess.check_call(['git', 'init', app_root])
        subprocess.check_call(['git', '-C', app_root, 'config',
                               'user.email', 'nobody@google.com'])
        subprocess.check_call(['git', '-C', app_root, 'config',
                               'user.name', 'Dummy Name'])
        subprocess.check_call(['git', '-C', app_root, 'remote', 'add', 'origin',
                               'https://github.com/NoSuchProject__/dummy.git'])
        subprocess.check_call(['git', '-C', app_root, 'add', '-A'])
        subprocess.check_call(['git', '-C', app_root, 'commit',
                               '-m', 'Dummy commit'])

        self.assertFalse(
            glob.glob(os.path.join(app_root, 'source-cont*.json')))
        result = self._deployStandardApp('app_engine_python_with_git')[0]
        # Verify that the upload included generated source contexts.
        self.assertTrue('source-context.json' in result.stderr)

        # Ensure that the test didn't create any source context files in the
        # source directory.
        self.assertFalse(
            glob.glob(os.path.join(app_root, 'source-cont*.json')))
    finally:
      # Removal of the git in the TearDown method is flaky. Unclear
      # why. It seems to work consistently here though.
      if os.path.exists(git_dir):
        files.RmTree(git_dir)

  @test_case.Filters.skip('Failing', 'b/118604661')
  def testDeployNodejsUsingApi(self):
    self._deployStandardApp('app_engine_nodejs_data')


if __name__ == '__main__':
  test_case.main()
