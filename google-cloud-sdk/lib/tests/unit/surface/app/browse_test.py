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

"""Tests for `gcloud app browse` commands."""

from googlecloudsdk.command_lib.app import exceptions as app_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import api_test_util

import mock


class BrowseTest(api_test_util.ApiTestBase):

  def SetUp(self):
    named_configs.ActivePropertiesFile.Invalidate()
    self.open_mock = self.StartPatch('webbrowser.open_new_tab')
    # Mock ShouldLaunchBrowser with a function that ignores environment stuff,
    # and just returns whether the user *wanted* to launch the browser.
    self.launch_browser_mock = self.StartPatch(
        'googlecloudsdk.command_lib.util.check_browser.ShouldLaunchBrowser',
        wraps=lambda x: x)

  def testBrowse_NoProject(self):
    """Test app browse command raises error when core/project unset."""
    self.UnsetProject()
    with self.assertRaisesRegexp(properties.RequiredPropertyError,
                                 'is not currently set.'):
      self.Run('app browse')

  def testBrowse_NoArgs(self):
    """Test basic case of running app browse opens correct page."""
    self.Run('app browse')
    self.launch_browser_mock.assert_called_with(True)
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://{0}.appspot.com'.format(self.Project())),
    ])

  def testBrowse_NoLaunchBrowser(self):
    """Test when the user does not want to open the browser."""
    self.Run('app browse --no-launch-browser')
    self.open_mock.assert_not_called()
    self.launch_browser_mock.assert_called_with(False)
    self.AssertOutputContains('https://{0}.appspot.com'.format(self.Project()))
    self.AssertErrNotContains('Opening [')

  def testBrowse_SpecifyVersionNoService(self):
    """Test running app browse with specific version opens correct page."""
    self.Run('app browse -v v1')
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://v1-dot-{0}.appspot.com'.format(self.Project())),
    ])

  def testBrowse_SpecifyServiceNoVersion(self):
    """Test running app browse with specific service opens correct page."""
    self.Run('app browse -s service1')
    self.assertEqual(
        self.open_mock.call_args_list,
        [mock.call(
            'https://service1-dot-{0}.appspot.com'.format(self.Project()))])

  def testBrowse_SpecifyServiceAndVersion(self):
    """Test running app browse with specific service and version."""
    self.Run('app browse --service service1 --version v2')
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://v2-dot-service1-dot-{0}.appspot.com'.format(
            self.Project())),
    ])
    self.AssertErrContains('Opening [')

  def testBrowse_CustomDomain(self):
    """Test running app browse with custom domain project opens correct page."""
    project = 'example.com:appid'
    properties.VALUES.core.project.Set(project)
    self.ExpectGetApplicationRequest(project, hostname='appid.exampleplex.com')
    self.Run('app browse')
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://appid.exampleplex.com'),
    ])

  def testBrowse_NoApp(self):
    """Test app browse command raises error when no app exists."""
    project = 'example.com:appid'
    properties.VALUES.core.project.Set(project)
    self.ExpectGetApplicationRequest(
        project,
        hostname='appid.exampleplex.com',
        exception=http_error.MakeDetailedHttpError(
            code=404,
            details=http_error.ExampleErrorDetails()))
    missing_app_regex = (r'The current Google Cloud project '
                         r'\[example.com:appid\] does not contain an App '
                         r'Engine application. Use `gcloud app create` to '
                         r'initialize an App Engine application within the '
                         r'project.')
    with self.assertRaisesRegexp(app_exceptions.MissingApplicationError,
                                 missing_app_regex):
      self.Run('app browse')

  def testBrowse_CustomDomainServiceAndVersion(self):
    """Test app browse with custom domain and specific service/version."""
    project = 'example.com:appid'
    properties.VALUES.core.project.Set(project)
    self.ExpectGetApplicationRequest(project, hostname='appid.exampleplex.com')
    self.Run('app browse --service service1 --version v2')
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://v2-dot-service1-dot-appid.exampleplex.com'),
    ])

  def testBrowse_DevShell(self):
    """Test running app browse with specific service and version."""
    self.StartDictPatch('os.environ', {'DEVSHELL_CLIENT_PORT': '1000'})
    self.Run('app browse --service service1 --version v2')
    self.assertEqual(self.open_mock.call_args_list, [
        mock.call('https://v2-dot-service1-dot-{0}.appspot.com'.format(
            self.Project())),
    ])
    self.AssertErrNotContains('Opening [')


if __name__ == '__main__':
  test_case.main()
