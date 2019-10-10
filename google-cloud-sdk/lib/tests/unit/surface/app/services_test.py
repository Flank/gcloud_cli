# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests for gcloud app services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import api_test_util
import mock


class ServicesListTest(api_test_util.ApiTestBase):
  """Tests for the `gcloud app services list` command."""

  SERVICES = {'service1': {'1': {'trafficSplit': .1},
                           '2': {'trafficSplit': .1},
                           '3': {'trafficSplit': .1}},
              'service2': {'1': {'trafficSplit': 1.0},
                           '2': {'trafficSplit': 0}}}

  def testList_NoProject(self):
    """Test `gcloud app services list` command raises with unset project."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app services list')

  def testList_NoResponse(self):
    """Test `services list` command lists 0 items when no services exist."""
    self.ExpectListServicesRequest(self.Project(), services={})
    self.Run('app services list')
    self.AssertErrContains('Listed 0 items.')

  def testList_AllServices(self):
    """Test `services list` command output."""
    self.ExpectListServicesRequest(self.Project(), services=self.SERVICES)
    for service in sorted(self.SERVICES):
      self.ExpectListVersionsRequest(self.Project(), service, self.SERVICES)
    self.Run('app services list')
    self.AssertOutputContains("""\
        SERVICE   NUM_VERSIONS
        service1  3
        service2  2""", normalize_space=True)

  def testList_AllServicesMissingSplit(self):
    """Test `services list` command when no split is present."""
    # API sometimes returns Service resources that have None for the 'split'
    # field
    self.ExpectListServicesRequest(self.Project(), self.SERVICES,
                                   with_split=False)
    for service in sorted(self.SERVICES):
      self.ExpectListVersionsRequest(self.Project(), service, self.SERVICES)
    self.Run('app services list')
    self.AssertOutputContains("""\
        SERVICE   NUM_VERSIONS
        service1  3
        service2  2""", normalize_space=True)


class ServicesDescribeTest(api_test_util.ApiTestBase):
  """Tests for the `gcloud app services describe` command."""

  def testDescribe_NoServiceSpecified(self):
    """Test describe command with missing argument."""
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument SERVICE: Must be specified.'):
      self.Run('app services describe')

  def testDescribe_One(self):
    """Test describing a service with a single version."""
    versions_split = [('1', 1.0)]
    self.ExpectGetServiceRequest(self.Project(), 's1', versions_split)
    self.Run('app services describe s1')
    self.AssertOutputContains("id: s1\n"
                              "name: apps/{}/services/s1\n"
                              "split:\n"
                              "allocations:\n"
                              "'1': 1.0".format(self.Project()),
                              normalize_space=True)

  def testDescribe_Many(self):
    """Test describing a service with multiple versions."""
    versions_split = [('1', .1), ('2', .1), ('3', .1)]
    self.ExpectGetServiceRequest(self.Project(), 's1', versions_split)
    self.Run('app services describe s1')
    self.AssertOutputContains("id: s1\n"
                              "name: apps/{}/services/s1\n"
                              "split:\n"
                              "allocations:\n"
                              "'1': 0.1\n"
                              "'2': 0.1\n"
                              "'3': 0.1\n".format(self.Project()),
                              normalize_space=True)


class ServicesDeleteTest(api_test_util.ApiTestBase):

  def testDelete_NoServiceSpecified(self):
    """Test `services delete` command errors out with no service provided."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument SERVICES [SERVICES ...]: Must be specified.'):
      self.Run('app services delete')

  def testDelete_OneService(self):
    """Test `services delete` command with one service."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    self.ExpectDeleteServiceRequest(self.Project(), 'service1')

    self.Run('app services delete service1')

    self.AssertErrContains(
        'Deleting service [{}/service1].'.format(self.Project()))
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_OneService_Default(self):
    """Test `services delete` command where there is one default."""
    self.ExpectListServicesRequest(self.Project(), {'default': {}})
    # A message very similar to this was observed with a default service
    exception = http_error.MakeDetailedHttpError(
        code=400, message=('The default service cannot be deleted.'))
    self.ExpectDeleteServiceRequest(self.Project(), 'default',
                                    exception=exception)
    with self.assertRaisesRegex(exceptions.Error,
                                'The default service cannot be deleted'):
      self.Run('app services delete default')

  def testDelete_OneServiceNotFound(self):
    """Test `services delete` command fails where service is not found."""
    self.ExpectListServicesRequest(self.Project(), {'service1': {}})

    with self.assertRaisesRegex(
        service_util.ServicesNotFoundError,
        re.escape('The following service was not found: [badservice]\n\n'
                  'All services: [service1]')):
      self.Run('app services delete badservice')

  def testDelete_MultipleServices(self):
    """Test `services delete` command deleting multiple services."""
    self.ExpectListServicesRequest(self.Project(), {'service1': {},
                                                    'service2': {},
                                                    'service3': {}})
    self.ExpectDeleteServiceRequest(self.Project(), 'service1')
    self.ExpectDeleteServiceRequest(self.Project(), 'service2')

    self.Run('app services delete service1 service2')

    self.AssertErrContains('Deleting services [{0}/service1, '
                           '{0}/service2].'.format(self.Project()))
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_MultipleServicesOneError(self):
    """Test `services delete` command where one service results in an error."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exception = http_error.MakeDetailedHttpError(
        code=500, message=('Internal Error'))
    self.ExpectDeleteServiceRequest(self.Project(), 'service1')
    self.ExpectDeleteServiceRequest(self.Project(), 'service2',
                                    exception=exception)
    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('Issue deleting service: [service2]')):
      self.Run('app services delete service1 service2')

  def testDelete_MultipleServicesMultiError(self):
    """Test `services delete` command where multiple services results in errors.
    """
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exception = http_error.MakeDetailedHttpError(
        code=500, message=('Internal Error'))
    self.ExpectDeleteServiceRequest(self.Project(), 'service1',
                                    exception=exception)
    self.ExpectDeleteServiceRequest(self.Project(), 'service2',
                                    exception=exception)
    with self.assertRaisesRegex(
        exceptions.Error,
        (r'Issue deleting services: \[service[12], service[12]\]')):
      self.Run('app services delete service1 service2')

  def testDelete_MultipleServicesMultiError_SpecialErrors(self):
    """Test `services delete` command where multiple services results in errors.
    """
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exc_nf = http_error.MakeDetailedHttpError(code=404, message='Error.')
    exc_c = http_error.MakeDetailedHttpError(code=409, message='Error.')
    self.ExpectDeleteServiceRequest(self.Project(), 'service1',
                                    exception=exc_nf)
    self.ExpectDeleteServiceRequest(self.Project(), 'service2',
                                    exception=exc_c)
    with self.assertRaisesRegex(
        exceptions.Error,
        (r'Issue deleting services: \[service[12], service[12]\]\n\n'
         r'\[service[12]\]: (?:Resource not found|'
         r'Resource already exists).*\n\n'
         r'\[service[12]\]: (?:Resource not found|'
         r'Resource already exists)')):
      self.Run('app services delete service1 service2')

  def testDelete_MultipleServicesNotFound(self):
    """Test `services delete` command where multiple services not found."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})

    with self.assertRaisesRegex(
        exceptions.Error,
        (r'The following services were not found: '
         r'\[service[34], service[34]\]\n\n'
         r'All services: \[service1, service2\]')):
      self.Run('app services delete service3 service4')

  def testDelete_VersionOneService(self):
    """Test `services delete` command where a version is being deleted."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    self.ExpectDeleteVersionRequest(self.Project(), 'service1', 'version1')

    self.Run('app services delete service1 --version=version1')

    self.AssertErrContains('Deleting version [version1] of service '
                           '[{}/service1].'.format(self.Project()))
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_VersionOneServiceError(self):
    """Test `services delete` command with --version where error is returned."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exception = http_error.MakeDetailedHttpError(code=404,
                                                 message='Error Response')
    self.ExpectDeleteVersionRequest(self.Project(), 'service1', 'version1',
                                    exception=exception)

    with self.assertRaisesRegex(
        exceptions.Error, re.escape(
            'Issue deleting version: [service1/version1]\n\n'
            '[service1/version1]: Resource not found')):
      self.Run('app services delete service1 --version=version1')

  def testDelete_VersionMultiService(self):
    """Test `services delete` command with --version and multiple services."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    self.ExpectDeleteVersionRequest(self.Project(), 'service1', 'version1')
    self.ExpectDeleteVersionRequest(self.Project(), 'service2', 'version1')

    self.Run('app services delete service1 service2 --version=version1')

    self.AssertErrContains('Deleting version [version1] of services '
                           '[{0}/service1, {0}/service2].'
                           .format(self.Project()))
    self.AssertErrContains('PROMPT_CONTINUE')

  def testDelete_VersionMultiServiceOneError(self):
    """Test delete command with --version where one service fails."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exception = http_error.MakeDetailedHttpError(code=404,
                                                 message='Error Response')
    self.ExpectDeleteVersionRequest(self.Project(), 'service1', 'version1')
    self.ExpectDeleteVersionRequest(self.Project(), 'service2', 'version1',
                                    exception=exception)

    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape(
            'Issue deleting version: [service2/version1]\n\n'
            '[service2/version1]: Resource not found')):
      self.Run('app services delete service1 service2 --version=version1')

  def testDelete_VersionMultiServiceMultiError(self):
    """Test delete command with --version where multiple services fail."""
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    exception = http_error.MakeDetailedHttpError(code=404,
                                                 message='Error Response')
    self.ExpectDeleteVersionRequest(self.Project(), 'service1', 'version1',
                                    exception=exception)
    self.ExpectDeleteVersionRequest(self.Project(), 'service2', 'version1',
                                    exception=exception)

    with self.assertRaisesRegex(
        exceptions.Error,
        r'Issue deleting versions: '
        r'\[service[12]/version1, service[12]/version1\]\n\n'
        r'\[service[12]/version1\]: Resource not found.*\n\n'
        r'\[service[12]/version1\]: Resource not found'):
      self.Run('app services delete service1 service2 --version=version1')

  def testDelete_OneResourcePath(self):
    """Test delete command fails with project/service format."""
    self.ExpectListServicesRequest(self.Project(), {'service1': {}})
    with self.assertRaisesRegex(
        exceptions.Error,
        re.escape('The following service was not found: [{0}/service1]\n\n'
                  'All services: [service1]'.format(self.Project()))):
      self.Run('app services delete {0}/service1'.format(self.Project()))

  def testDelete_PollsOperation(self):
    """Test delete command polls operation if it doesn't immediately finish."""
    self.StartPatch('time.sleep')
    self.ExpectListServicesRequest(self.Project(),
                                   {'service1': {}, 'service2': {}})
    self.ExpectDeleteServiceRequest(self.Project(), 'service1', retries=10)
    self.Run('app services delete service1')


class SetTrafficTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.services = {'service1': {}, 'service2': {}, 'service3': {}}

  def testOneServiceOneVersion(self):
    """Test `set-traffic` command with one service/version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': 1.0})
    self.Run('app services set-traffic service1 --splits v1=1')

  def testOneServiceOneVersionZeroSum(self):
    """Test `set-traffic` command errors when splits add to 0."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    with self.assertRaisesRegex(
        service_util.ServicesSplitTrafficError,
        'Cannot set traffic split to zero'):
      self.Run('app services set-traffic service1 --splits v1=0')

  def testMultiServicesOneVersion(self):
    """Test `set-traffic` command with multiple services, single version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    for service in ['service1', 'service2']:
      self.ExpectSetTraffic(self.Project(), service, {'v1': 1.0})
    self.Run('app services set-traffic service1 service2 --splits v1=1')

  def testServiceDoesNotExistError(self):
    """Test `set-traffic` command fails if service not found."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    with self.assertRaises(exceptions.Error):
      self.Run('app services set-traffic service1 badservice --splits v1=1')
    self.AssertErrContains(
        'The following service was not found: [badservice]')

  def testAllServicesOneVersion(self):
    """Test `set-traffic` command with no service specified, one version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    for service in sorted(self.services):
      self.ExpectSetTraffic(self.Project(), service, {'v1': 1.0})

    self.Run('app services set-traffic --splits v1=1')

  def testOneServiceMultiSplit(self):
    """Test `set-traffic` command with one service and multiple versions."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': .5, 'v2': .5})
    self.Run('app services set-traffic service1 --splits v1=1,v2=1')

  def testMultiServicesMultiSplit(self):
    """Test `set-traffic` command with multiple services and versions."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    for service in ['service1', 'service2']:
      self.ExpectSetTraffic(self.Project(), service, {'v1': .5, 'v2': .5})
    self.Run('app services set-traffic service1 service2 --splits v1=1,v2=1')

  def testRounding(self):
    """Test `set-traffic` command rounds to hundredths place for split."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': .33, 'v2': .67})
    self.Run('app services set-traffic service1 --splits v1=1,v2=2')

  def testResolutionIP(self):
    """Test `set-traffic` command with no --split-by specified defaults to IP.
    """
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': .17, 'v2': .83})
    self.Run('app services set-traffic service1 --splits v1=1,v2=5')

  def testResolutionCookie(self):
    """Test `set-traffic` command with --split-by flag."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': .167, 'v2': .833},
                          shard_by='COOKIE')
    self.Run('app services set-traffic service1 --splits v1=1,v2=5 '
             '--split-by=cookie')

  def testMigrateError(self):
    """Test `set-traffic` command errors if --migrate used with 2 versions."""
    with self.assertRaises(exceptions.Error):
      self.Run('app services set-traffic service1 --splits v1=1,v2=1 --migrate')

  def testMigrate(self):
    """Test `set-traffic` command with --migrate flag."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': 1.0}, migrate=True)
    self.Run('app services set-traffic service1 --splits v1=1 --migrate')

  def testSplitByCookie(self):
    """Test `set-traffic` command with --split-by flag and only one version."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': 1.0},
                          shard_by='COOKIE')
    self.Run('app services set-traffic service1 --splits v1=1 '
             '--split-by=cookie')

  def testSplitByRandom(self):
    """Test `set-traffic` command with --split-by=random."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': 1.0},
                          shard_by='RANDOM')
    self.Run('app services set-traffic service1 --splits v1=1 '
             '--split-by=random')

  def testResourcePath(self):
    """Test `set-traffic` command fails using project/service format."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    with self.assertRaisesRegex(
        service_util.ServicesNotFoundError,
        re.escape('The following service was not found: [{}/service1]'
                  '\n\nAll services: [service1, service2, service3]'
                  .format(self.Project())
                 )):
      self.Run('app services set-traffic {}/service1 --splits v1=1'
               .format(self.Project()))

  def testApiError(self):
    """Test `set-traffic` command raises error when one service fails."""
    self.ExpectListServicesRequest(self.Project(), self.services)
    error = http_error.MakeDetailedHttpError(code=501, message='Error')
    self.ExpectSetTraffic(self.Project(), 'service1', {'v1': 1.0},
                          exception=error)
    self.ExpectSetTraffic(self.Project(), 'service2', {'v1': 1.0})
    with self.assertRaises(exceptions.Error):
      self.Run('app services set-traffic service1 service2 --splits v1=1')
    self.AssertErrContains('Issue setting traffic on service(s): service1')


class BrowseTest(api_test_util.ApiTestBase):

  def SetUp(self):
    self.open_mock = self.StartPatch('webbrowser.open_new_tab')
    # Mock ShouldLaunchBrowser with a function that ignores environment stuff,
    # and just returns whether the user *wanted* to launch the browser.
    self.launch_browser_mock = self.StartPatch(
        'googlecloudsdk.command_lib.util.check_browser.ShouldLaunchBrowser',
        wraps=lambda x: x)

  def testBrowse_NoProject(self):
    """Test `app services browse` fails with no project set."""
    self.UnsetProject()
    with self.assertRaisesRegex(properties.RequiredPropertyError,
                                'is not currently set.'):
      self.Run('app services browse default')

  def testBrowse_NoArgs(self):
    """Test `app services browse` fails with no args."""
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument SERVICES [SERVICES ...]: Must be specified.'):
      self.Run('app services browse')

  def testBrowse_NoLaunchBrowser(self):
    """Test when the user does not want to open the browser."""
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse --no-launch-browser service1 service2')
    self.open_mock.assert_not_called()
    self.launch_browser_mock.assert_called_with(False)
    self.AssertOutputContains("""\
        SERVICE   URL
        service1  https://service1-dot-{0}.appspot.com
        service2  https://service2-dot-{0}.appspot.com""".format(
            self.Project()
        ), normalize_space=True)

  def testBrowse_SpecifyOneService(self):
    """Test `app services browse` with one service specified."""
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse service1')
    self.launch_browser_mock.assert_called_with(True)
    self.open_mock.assert_called_once_with(
        'https://service1-dot-{0}.appspot.com'.format(self.Project()))

  def testBrowse_SpecifyMultipleServices(self):
    """Test `app services browse` with multiple services specified."""
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse service1 service2')
    self.open_mock.assert_has_calls([
        mock.call(
            'https://service1-dot-{0}.appspot.com'.format(self.Project())),
        mock.call(
            'https://service2-dot-{0}.appspot.com'.format(self.Project())),
    ], any_order=True)
    self.assertEqual(self.open_mock.call_count, 2)

  def testBrowse_SpecifyVersionDefaultService(self):
    """Test `app services browse` with no service specified and --version."""
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse default --version="v1"')
    self.open_mock.assert_called_once_with(
        'https://v1-dot-{0}.appspot.com'.format(self.Project()))

  def testBrowse_SpecifyVersionAndService(self):
    """Test `app services browse` with one service and version specified."""
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse service1 --version=v1')
    self.open_mock.assert_called_once_with(
        'https://v1-dot-service1-dot-{0}.appspot.com'.format(self.Project()))

  def testBrowse_MultiServicesSpecifyVersion(self):
    """Test `app services browse` with one version and 2 services specified."""
    self.ExpectGetApplicationRequest(self.Project())
    self.ExpectGetApplicationRequest(self.Project())
    self.Run('app services browse service1 service2 -v=v1')
    self.open_mock.assert_has_calls([
        mock.call(
            'https://v1-dot-service1-dot-{0}.appspot.com'.format(
                self.Project())),
        mock.call(
            'https://v1-dot-service2-dot-{0}.appspot.com'.format(
                self.Project())),
    ], any_order=True)
    self.assertEqual(self.open_mock.call_count, 2)


if __name__ == '__main__':
  test_case.main()
