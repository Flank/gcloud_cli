# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.core.context_aware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.core import context_aware
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from tests.lib import sdk_test_base
from tests.lib import test_case

CERT_KEY_SECTION = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
"""
PASSWORD = '##invalid-password##'
PASSWORD_SECTION = """
-----BEGIN PASSPHRASE-----
%s
-----END PASSPHRASE-----
""" % PASSWORD


class ContextAwareTest(sdk_test_base.SdkBase):

  def SetUp(self):
    context_aware.singleton_config = None

  def TearDown(self):
    context_aware.singleton_config = None

  def testClientCertConfigError(self):
    properties.VALUES.context_aware.use_client_certificate.Set(True)
    # property validation will throw an error for invalid configuration path
    with file_utils.TemporaryDirectory() as t:
      file_path = os.path.join(t, 'context_aware.json')
      with self.assertRaises(properties.InvalidValueError):
        properties.VALUES.context_aware.auto_discovery_file_path.Set(file_path)

  def ConfigureCertProvider(self, temp_dir, pem_contents):
    # Create a certificate file that will be output by the test cert
    # provisioner
    cert_path = os.path.join(temp_dir, 'test_cert.pem')
    file_utils.WriteFileContents(cert_path, pem_contents)
    # Create context aware configuration which specifies the cert provisioner
    file_path = os.path.join(temp_dir, 'context_aware_metadata.json')
    scripts_dir = self.Resource(
        'tests', 'unit', 'core', 'test_data', 'context_aware', 'scripts')
    script = 'test.' + ('cmd' if test_case.Filters.IsOnWindows() else 'sh')
    data = {}
    data['cert_provider_command'] = [os.path.join(scripts_dir, script),
                                     cert_path]
    contents = json.dumps(data)
    file_utils.WriteFileContents(file_path, contents)
    # Override auto discovery path to use the test file path
    properties.VALUES.context_aware.auto_discovery_file_path.Set(file_path)

  def testAutoDiscovery(self):
    properties.VALUES.context_aware.use_client_certificate.Set(True)
    with file_utils.TemporaryDirectory() as t:
      self.ConfigureCertProvider(t, CERT_KEY_SECTION + PASSWORD_SECTION)
      cfg = context_aware.Config()
      self.assertTrue(cfg.client_cert_path)
      self.AssertFileEquals(CERT_KEY_SECTION, cfg.client_cert_path)
      self.assertEqual(PASSWORD, cfg.client_cert_password)

  def testAutoDiscoveryWithBadFormat(self):
    properties.VALUES.context_aware.use_client_certificate.Set(True)
    with file_utils.TemporaryDirectory() as t:
      self.ConfigureCertProvider(t, '*invalid-contents*')
      with self.assertRaises(context_aware.ConfigException):
        context_aware.Config()

  def testAutoDiscoveryWithNoCertProvider(self):
    properties.VALUES.context_aware.use_client_certificate.Set(True)
    with file_utils.TemporaryDirectory() as t:
      file_path = os.path.join(t, 'context_aware_metadata.json')
      file_utils.WriteFileContents(file_path, '{}')
      properties.VALUES.context_aware.auto_discovery_file_path.Set(file_path)
      with self.assertRaises(context_aware.ConfigException):
        context_aware.Config()


if __name__ == '__main__':
  sdk_test_base.main()
