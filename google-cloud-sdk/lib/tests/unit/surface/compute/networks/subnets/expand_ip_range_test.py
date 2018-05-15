# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the subnets expand-ip-range subcommand."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.util import apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class SubnetsExpandIpRangeTest(test_base.BaseTest):

  api_version = 'alpha'
  messages = apis.GetMessagesModule('compute', 'alpha')

  def SetUp(self):
    self.SelectApi(self.api_version)

  def testExpandIpRange(self):
    self._SetupMock(original_ip_range='10.130.0.0/20')
    self._RunExpandIpRangeCommand(prefix_length=14, interactive=False)
    self._VerifyRequests(
        expect_get_request=True,
        expect_expand_request=True,
        expected_new_ip_range='10.128.0.0/14')

  def testValidSmallestPrefixLength(self):
    self._SetupMock(original_ip_range='172.16.131.0/24')
    self._RunExpandIpRangeCommand(prefix_length=0, interactive=False)
    self._VerifyRequests(
        expect_get_request=True,
        expect_expand_request=True,
        expected_new_ip_range='0.0.0.0/0')

  def testValidLargestPrefixLength(self):
    self._SetupMock(original_ip_range='192.168.128.0/20')
    self._RunExpandIpRangeCommand(prefix_length=29, interactive=False)
    self._VerifyRequests(
        expect_get_request=True,
        expect_expand_request=True,
        expected_new_ip_range='192.168.128.0/29')

  def testInvalidSmallPrefixLength(self):
    expected_error_message = (
        'Invalid value for [--prefix-length]: Prefix length must be in the '
        'range [0, 29].')
    with self.AssertRaisesToolExceptionMatches(expected_error_message):
      self._RunExpandIpRangeCommand(prefix_length=-1, interactive=False)
    self._VerifyRequests(
        expect_get_request=False,
        expect_expand_request=False)

  def testInvalidLargePrefixLength(self):
    expected_error_message = (
        'Invalid value for [--prefix-length]: Prefix length must be in the '
        'range [0, 29].')
    with self.AssertRaisesToolExceptionMatches(expected_error_message):
      self._RunExpandIpRangeCommand(prefix_length=30, interactive=False)
    self._VerifyRequests(
        expect_get_request=False,
        expect_expand_request=False)

  def testPromptingWithYes(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self._SetupMock(original_ip_range='10.132.131.0/24')
    self.WriteInput('y\n')
    self._RunExpandIpRangeCommand(prefix_length=22, interactive=True)
    self._VerifyRequests(
        expect_get_request=True,
        expect_expand_request=True,
        expected_new_ip_range='10.132.128.0/22')

  def testPromptingWithNo(self):
    self.StartPatch('googlecloudsdk.core.console.console_io.CanPrompt',
                    return_value=True)
    self._SetupMock(original_ip_range='10.128.0.0/20')
    self.WriteInput('n\n')
    with self.AssertRaisesToolExceptionRegexp('Operation aborted by user.'):
      self._RunExpandIpRangeCommand(prefix_length=16, interactive=True)
    self._VerifyRequests(
        expect_get_request=True, expect_expand_request=False)

  def testSubnetDoesNotExist(self):
    self._SetupMock(original_ip_range=None)
    expected_error_message = (
        'Subnet [my-subnet1] was not found in region us-central1.')
    with self.AssertRaisesToolExceptionMatches(expected_error_message):
      self._RunExpandIpRangeCommand(prefix_length=16, interactive=False)
    self._VerifyRequests(
        expect_get_request=True,
        expect_expand_request=False)

  def _SetupMock(self, original_ip_range):
    if original_ip_range is None:
      responses = [[]]
    else:
      subnetwork = self.messages.Subnetwork(
          name='my-subnet1',
          network=(
              'https://www.googleapis.com/compute/v1/projects/my-project/'
              'global/networks/my-network'),
          ipCidrRange=original_ip_range,
          region=('https://www.googleapis.com/compute/v1/projects/my-project/'
                  'regions/us-central1'),
      )
      responses = [[subnetwork], [],]
    self.make_requests.side_effect = iter(responses)

  def _RunExpandIpRangeCommand(self, prefix_length, interactive=True):
    command_template = (
        '{api_version} compute networks subnets expand-ip-range my-subnet1 '
        '--region us-central1 --prefix-length {prefix_length} {quiet}')
    command = command_template.format(
        api_version=self.api_version if self.api_version else '',
        prefix_length=prefix_length,
        quiet='' if interactive else '--quiet')
    self.Run(command.strip())

  def _VerifyRequests(
      self,
      expect_get_request,
      expect_expand_request,
      expected_new_ip_range=None):
    expected_requests = []
    if expect_get_request:
      expected_requests.append([(
          self.compute.subnetworks,
          'Get',
          self.messages.ComputeSubnetworksGetRequest(
              subnetwork='my-subnet1',
              project='my-project',
              region='us-central1'))])
    if expect_expand_request:
      expected_request_body = self.messages.SubnetworksExpandIpCidrRangeRequest(
          ipCidrRange=expected_new_ip_range)
      expected_requests.append([(
          self.compute.subnetworks,
          'ExpandIpCidrRange',
          self.messages.ComputeSubnetworksExpandIpCidrRangeRequest(
              subnetwork='my-subnet1',
              subnetworksExpandIpCidrRangeRequest=expected_request_body,
              project='my-project',
              region='us-central1'))])
    self.CheckRequests(*expected_requests)

if __name__ == '__main__':
  test_case.main()
