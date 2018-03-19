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

"""Tests for `gcloud app open-console` commands."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.app import api_test_util


class BrowseTest(api_test_util.ApiTestBase):

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    self.open_mock = self.StartPatch('webbrowser.open_new_tab')

  def testOpenConsole_NoProject(self):
    self.UnsetProject()
    with self.assertRaisesRegexp(properties.RequiredPropertyError,
                                 'is not currently set.'):
      self.Run('app open-console')

  def testOpenConsole_NoArgs(self):
    self.Run('app open-console')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/appengine?project={0}&'
        'serviceId=default'.format(self.Project()))

  def testOpenConsole_SpecifyVersionNoService(self):
    self.Run('app open-console -v v1')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/appengine?project={0}&'
        'serviceId=default&versionId=v1'.format(self.Project()))

  def testOpenConsole_SpecifyServiceNoVersion(self):
    self.Run('app open-console -s service1')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/appengine?project={0}&'
        'serviceId=service1'.format(self.Project()))

  def testOpenConsole_SpecifyServiceAndVersion(self):
    self.Run('app open-console --service service1 --version v2')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/appengine?project={0}&'
        'serviceId=service1&versionId=v2'.format(self.Project()))

  # The following tests are for testing the --logs flag
  def testOpenConsoleLogs_NoProject(self):
    self.UnsetProject()
    with self.assertRaisesRegexp(properties.RequiredPropertyError,
                                 'is not currently set.'):
      self.Run('app open-console --logs')

  def testOpenConsoleLogs_NoArgs(self):
    self.Run('app open-console --logs')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/logs?project={0}&'
        'serviceId=default'.format(self.Project()))

  def testOpenConsoleLogs_SpecifyVersionNoService(self):
    self.Run('app open-console --logs -v v1')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/logs?project={0}&'
        'serviceId=default&versionId=v1'.format(self.Project()))

  def testOpenConsoleLogs_SpecifyServiceNoVersion(self):
    self.Run('app open-console -l -s service1')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/logs?project={0}&'
        'serviceId=service1'.format(self.Project()))

  def testOpenConsoleLogs_SpecifyServiceAndVersion(self):
    self.Run('app open-console --service service1 --version v2 -l')
    self.open_mock.assert_called_once_with(
        'https://console.developers.google.com/logs?project={0}&'
        'serviceId=service1&versionId=v2'.format(self.Project()))


if __name__ == '__main__':
  test_case.main()
