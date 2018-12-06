# -*- coding: utf-8 -*- #
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

"""Tests for deploying a MVM app."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import log
from googlecloudsdk.core import url_opener
from googlecloudsdk.core.util import retry

from tests.lib import e2e_base
from tests.lib import e2e_utils
from tests.lib import exec_utils
from tests.lib import sdk_test_base
from tests.lib import test_case

from six.moves import urllib


@sdk_test_base.Filters.RunOnlyIfLongrunning
class DeployCustomTests(sdk_test_base.BundledBase, e2e_base.WithServiceAuth,
                        sdk_test_base.WithTempCWD):
  """Test we can deploy an app."""

  # Total test time: DEPLOY_TIMEOUT + DELETE_TIMEOUT * DELETE_RETRIALS + ε
  # Make sure to allow for enough time in the test runner for these to complete.
  DEPLOY_TIMEOUT = 1200  # 20 minutes
  DELETE_TIMEOUT = 180  # 3 minutes
  DELETE_RETRIALS = 3  # Total of 29 minutes

  def SetUp(self):
    self.version = next(e2e_utils.GetResourceNameGenerator(prefix='gaetest'))
    # Use Cloud Build by default.

  def _Resource(self, *parts):
    return super(sdk_test_base.BundledBase, self).Resource(
        'tests', 'e2e', 'surface', 'app', 'test_data', *parts)

  def deployApp(self, test_app, image_url=None, release_track=None):
    """Deploy an app to a particular service, can happen in parallel.

    Args:
      test_app: Path to app.yaml for the app to be deployed.
      image_url: If the `--image-url` flag should be populated.
      release_track: If there should be a release track (such as `beta`).

    Returns:
      tests.lib.exec_utils.ExecutionResult, the result
        of the script runner used to run the command.
    """
    args = ['--verbosity', 'debug', 'app', 'deploy', '--no-promote',
            test_app, '--version', self.version, '-q']
    if release_track:
      # NOTE: Since `gcloud beta app deploy` depends on the Appengine Flexible
      # Environment API being enabled, tests in beta track will fail if run in a
      # project where the API isn't enabled.
      args.insert(0, release_track)
    if image_url:
      args.append('--image-url=%s' % image_url)

    return self.ExecuteScript('gcloud', args,
                              timeout=DeployCustomTests.DEPLOY_TIMEOUT)

  def testDeployCustom(self):
    test_app = self._Resource('app_engine_custom_data', 'app.yaml')
    self.deployApp(test_app)

  @sdk_test_base.Filters.RunOnlyInBundle  # Requires component app-engine-go
  def testDeployGo(self):
    """Deploy a flex Go app.

    Ensures that the staging step is invoked, since a depencency will be
    intentionally be placed outside the app directory -- in the GOPATH.

    Furthermore, a local installation of Go is normally required -- something
    we'd like to avoid in the testing infrastructure. Instead, an artificial
    GOROOT is provided, which contains a few mock packages with names from the
    actual standard library, such as "net/http", which the test app depends on.
    If a dependency is in the GOROOT, it shouldn't be vendored.

    The test is designed to fail if the staging step/vendoring fails.
    """
    test_app = self._Resource('app_engine_go_flex_data', 'app.yaml')
    os.environ['GOPATH'] = self._Resource('gopath')
    os.environ['GOROOT'] = self._Resource('goroot')
    try:
      self.deployApp(test_app)
    finally:
      del os.environ['GOPATH']
      del os.environ['GOROOT']

  def testDeployPythonVanilla(self):
    test_app = self._Resource('app_engine_python_vanilla_vm_data', 'app.yaml')
    self.deployApp(test_app)
    url = ('https://{0}-dot-{1}.appspot.com/headers'.format(
        self.version, self.Project()))
    req = urllib.request.Request(url)
    r = retry.RetryOnException(f=url_opener.urlopen, max_retrials=3,
                               sleep_ms=300)(req)
    self.assertEqual(r.getcode(), 200)

  def testDeployNodejs(self):
    test_app = self._Resource('app_engine_nodejs_flex_data', 'app.yaml')
    self.deployApp(test_app)

  def testDeployRuby(self):
    test_data_dir = self._Resource('app_engine_ruby_data')
    test_app = os.path.join(test_data_dir, 'app.yaml')

    # We have to "bundle install" the app prior to testing deployment.
    os.chdir(test_data_dir)
    os.system('bundle install')

    self.deployApp(test_app)

  def testDeployPhp(self):
    test_app = self._Resource('app_engine_php_flex_data', 'app.yaml')
    self.deployApp(test_app)

  @test_case.Filters.skip('Flaky', 'b/117423915')
  def testDeployOpenJDK8(self):
    test_app = self._Resource('app_engine_java_vm_openjdk8_data', 'app.yaml')
    self.deployApp(test_app)

  def testDeployPureJetty9(self):
    test_app = self._Resource('app_engine_java_vm_jetty9_data', 'app.yaml')
    self.deployApp(test_app)

  def testDeployJavaFlex(self):
    test_app = self._Resource('app_engine_java_flex', 'app.yaml')
    self.deployApp(test_app)

  def testDeployWithGivenImage(self):
    test_app = self._Resource('app_engine_custom_data', 'app.yaml')
    # We use google-appengine-qa over cloud-sdk-integration-testing in order to
    # test cross-project image copying.
    # The image tag is the latest date at which this test has been updated.
    img = 'gcr.io/google-appengine-qa/e2eimage:20170302'
    self.deployApp(test_app, image_url=img)

  def testDeployCustomPrivateBase(self):
    test_app = self._Resource('app_engine_custom_private_base_data', 'app.yaml')
    self.deployApp(test_app)

  def TearDown(self):
    @retry.RetryOnException(max_retrials=DeployCustomTests.DELETE_RETRIALS)
    def _InnerTearDown():
      self.ExecuteScript('gcloud', ['app', 'versions', 'delete', '--service',
                                    'default', '-q',
                                    self.version,
                                    '--verbosity=debug'],
                         timeout=DeployCustomTests.DELETE_TIMEOUT)
    try:
      _InnerTearDown()
    except exec_utils.ExecutionError as e:
      log.error('Error {e} tearing down app version: {version}'
                .format(e=e, version=self.version))


if __name__ == '__main__':
  sdk_test_base.main()
