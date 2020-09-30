# Lint as: python3
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
"""Tests for the subordinates create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.core import properties
from surface.privateca.subordinates import create
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util

import mock


_DEFAULT_PROJECT = 'p1'
_DEFAULT_LOCATION = 'us-west1'


class CreateFlagsTest(cli_test_base.CliTestBase, sdk_test_base.WithFakeAuth):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    create.Create.Args(self.parser)
    properties.VALUES.core.project.Set(_DEFAULT_PROJECT)
    properties.VALUES.privateca.location.Set(_DEFAULT_LOCATION)
    self.resource_args = [
        'new-ca', '--kms-key-version',
        'projects/{}/locations/{}/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1'
        .format(_DEFAULT_PROJECT, _DEFAULT_LOCATION)
    ]

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testCsrOutputFileWithoutCreateCsrRaisesException(self, _):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                '--create-csr: Must be specified.'):
      self.parser.parse_args(self.resource_args + [
          '--csr-output-file=csr.pem',
      ])

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testCreateCsrCannotBeFalse(self, _):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                '--create-csr: .*false'):
      self.parser.parse_args(self.resource_args + [
          '--create-csr=false',
          '--csr-output-file=csr.pem',
      ])

  @mock.patch.object(
      locations,
      'GetSupportedLocations',
      autospec=True,
      return_value=['us-west1', 'us-east1', 'europe-west1'])
  def testBothCreateCsrAndIssuerRaisesException(self, _):
    with self.assertRaisesRegex(cli_test_base.MockArgumentError,
                                'Exactly one of .*--create-csr.*--issuer'):
      self.parser.parse_args(self.resource_args + [
          '--create-csr',
          '--csr-output-file=csr.pem',
          '--issuer=my-root',
          '--issuer-location=us-west1',
      ])


if __name__ == '__main__':
  test_case.main()
