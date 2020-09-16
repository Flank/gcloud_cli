# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for network diagnostics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socket
import ssl

from googlecloudsdk.core import config
from googlecloudsdk.core import http
from googlecloudsdk.core import properties
from googlecloudsdk.core.diagnostics import check_base
from googlecloudsdk.core.diagnostics import http_proxy_setup
from googlecloudsdk.core.diagnostics import network_diagnostics
from tests.lib import test_case
from tests.lib.core.diagnostics import diagnostics_test_base
import httplib2
from six.moves import http_client
import socks


CHANGE_PROXY = http_proxy_setup.ChangeGcloudProxySettings


def CheckFailResult(urls, first_run=True,
                    exception=http_client.ResponseNotReady()):
  message = 'Reachability Check {0}.\n'.format('failed' if first_run else
                                               'still does not pass')
  def CreateFailure(url, err):
    msg = 'Cannot reach {0} ({1})'.format(url, type(err).__name__)
    return check_base.Failure(message=msg, exception=err)
  failures = [CreateFailure(url, exception) for url in urls]
  for failure in failures:
    message += '    {0}\n'.format(failure.message)
  if first_run:
    message += ('Network connection problems may be due to proxy or firewall '
                'settings.\n')
  return check_base.Result(passed=False, message=message, failures=failures)


class ReachabilityCheckerTests(diagnostics_test_base.DiagnosticTestBase):

  def SetUp(self):
    self.http_request_mock = self.StartObjectPatch(
        http, 'Http').return_value.request
    self.reachability_checker = network_diagnostics.ReachabilityChecker()

  def testCantConnectNoInternet(self):
    self.http_request_mock.side_effect = http_client.ResponseNotReady
    expected_result = CheckFailResult(['https://www.googleapis.com'])
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://www.googleapis.com'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(CHANGE_PROXY, actual_fixer)

  def testCantConnectNoInternetTimeout(self):
    self.http_request_mock.side_effect = socket.timeout
    expected_result = CheckFailResult(['https://www.googleapis.com'],
                                      exception=socket.timeout())
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://www.googleapis.com'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(CHANGE_PROXY, actual_fixer)

  def testCantConnectSSLError(self):
    self.http_request_mock.side_effect = ssl.SSLError
    expected_result = CheckFailResult(['https://www.googleapis.com'],
                                      exception=ssl.SSLError())
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://www.googleapis.com'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(CHANGE_PROXY, actual_fixer)

  def testCantConnectSocks5ProxyError(self):
    self.http_request_mock.side_effect = socks.HTTPError((403, 'Forbidden'))
    expected_result = CheckFailResult(['https://accounts.google.com'],
                                      exception=socks.HTTPError(
                                          (403, 'Forbidden')))
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://accounts.google.com'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(CHANGE_PROXY, actual_fixer)

  def testCantConnectBadURL(self):
    self.http_request_mock.side_effect = httplib2.ServerNotFoundError
    expected_result = CheckFailResult(
        ['https://badurl.badurl'], exception=httplib2.ServerNotFoundError())
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://badurl.badurl'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(CHANGE_PROXY, actual_fixer)

  def testGoodConnection(self):
    self.http_request_mock.return_value = 'dummy_response', 'dummy_content'
    expected_result = check_base.Result(
        passed=True, message='Reachability Check passed.')
    actual_result, actual_fixer = self.reachability_checker.Check(
        ['https://www.googleapis.com'])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(None, actual_fixer)

  def testGoodConnectionNoUrls(self):
    self.http_request_mock.return_value = 'dummy_response', 'dummy_content'
    expected_result = check_base.Result(
        passed=True, message='Reachability Check passed.')
    actual_result, actual_fixer = self.reachability_checker.Check()
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(None, actual_fixer)

  def testEmptyUrlList(self):
    self.http_request_mock.return_value = 'dummy_response', 'dummy_content'
    expected_result = check_base.Result(passed=True,
                                        message='No URLs to check.')
    actual_result, actual_fixer = self.reachability_checker.Check([])
    self.AssertResultEqual(expected_result, actual_result)
    self.assertEqual(None, actual_fixer)


class NetworkDiagnosticTests(diagnostics_test_base.DiagnosticTestBase):

  _FAIL_RESULT = CheckFailResult(network_diagnostics.DefaultUrls())

  def SetUp(self):
    self.run_check_mock = self.StartObjectPatch(
        network_diagnostics.ReachabilityChecker, 'Check')
    self.fixer_mock = self.StartObjectPatch(http_proxy_setup,
                                            'ChangeGcloudProxySettings')

  def testNoNetworkIssues(self):
    self.run_check_mock.return_value = check_base.Result(passed=True), None
    self.assertTrue(network_diagnostics.NetworkDiagnostic().RunChecks())
    self.assertEqual(1, self.run_check_mock.call_count)
    self.assertFalse(self.fixer_mock.called)
    self.AssertErrContains(
        'Network diagnostic passed (1/1 checks passed).')

  def testNetworkIssuesNoProxyChangesMade(self):
    self.run_check_mock.return_value = self._FAIL_RESULT, self.fixer_mock
    self.fixer_mock.return_value = False
    self.assertFalse(network_diagnostics.NetworkDiagnostic().RunChecks())
    self.assertEqual(1, self.run_check_mock.call_count)
    self.assertEqual(1, self.fixer_mock.call_count)
    self.AssertErrContains(
        'ERROR: Network diagnostic failed (0/1 checks passed).')

  def testNetworkIssuesProxyChangesMadeStillIssuesExit(self):
    self.run_check_mock.return_value = self._FAIL_RESULT, self.fixer_mock
    self.fixer_mock.side_effect = [True, False]
    self.assertFalse(network_diagnostics.NetworkDiagnostic().RunChecks())
    self.assertEqual(2, self.run_check_mock.call_count)
    self.assertEqual(2, self.fixer_mock.call_count)
    self.AssertErrContains(
        'ERROR: Network diagnostic failed (0/1 checks passed).')

  def testNetworkIssuesProxyChangesMadeIssuesFixed(self):
    self.run_check_mock.side_effect = [
        (self._FAIL_RESULT, self.fixer_mock),
        (check_base.Result(passed=True), None)]
    self.fixer_mock.return_value = True
    self.assertTrue(network_diagnostics.NetworkDiagnostic().RunChecks())
    self.assertEqual(2, self.run_check_mock.call_count)
    self.assertEqual(1, self.fixer_mock.call_count)
    self.AssertErrContains(
        'Network diagnostic passed (1/1 checks passed).')

  def testNetworkIssuesMaxFixRetriesMet(self):
    self.run_check_mock.return_value = (self._FAIL_RESULT, self.fixer_mock)
    self.fixer_mock.return_value = True
    self.assertFalse(network_diagnostics.NetworkDiagnostic().RunChecks())
    max_retries = network_diagnostics.NetworkDiagnostic._MAX_RETRIES
    self.assertEqual(max_retries + 1, self.run_check_mock.call_count)
    self.assertEqual(max_retries, self.fixer_mock.call_count)
    self.AssertErrContains('Unable to fix Network diagnostic failure after 5 '
                           'attempts.')
    self.AssertErrContains(
        'ERROR: Network diagnostic failed (0/1 checks passed).')


class DefaultUrlsTests(test_case.Base):

  _BASE_DEFAULT_URLS = [
      'https://accounts.google.com',
      'https://cloudresourcemanager.googleapis.com/v1beta1/projects',
      'https://www.googleapis.com/auth/cloud-platform']

  def SetUp(self):
    properties.VALUES.component_manager.snapshot_url.Set(None)
    # Some of our testing environments use a snapshot url that would interfere
    # with these tests.
    self.StartObjectPatch(config.INSTALLATION_CONFIG, 'snapshot_url',
                          return_value='')

  def testNoSnapshotUrls(self):
    self.assertEqual(self._BASE_DEFAULT_URLS,
                     network_diagnostics.DefaultUrls())

  def testSnapshotUrlPropertySetNonlocal(self):
    properties.VALUES.component_manager.snapshot_url.Set('https://repo.repo')
    self.assertEqual(self._BASE_DEFAULT_URLS + ['https://repo.repo'],
                     network_diagnostics.DefaultUrls())

  def testSnapshotUrlPropertySetLocalFile(self):
    properties.VALUES.component_manager.snapshot_url.Set('file://repo')
    self.assertEqual(self._BASE_DEFAULT_URLS,
                     network_diagnostics.DefaultUrls())

  def testSnapshotUrlPropertySetNonlocalMultipleUrls(self):
    properties.VALUES.component_manager.snapshot_url.Set(
        'https://repo1.repo,https://repo2.repo')
    self.assertEqual(self._BASE_DEFAULT_URLS + ['https://repo1.repo',
                                                'https://repo2.repo'],
                     network_diagnostics.DefaultUrls())

  def testSnapshotUrlPropertySetLocalFileMultipleFiles(self):
    properties.VALUES.component_manager.snapshot_url.Set(
        'file://repo1,file://repo2')
    self.assertEqual(self._BASE_DEFAULT_URLS,
                     network_diagnostics.DefaultUrls())

if __name__ == '__main__':
  test_case.main()
