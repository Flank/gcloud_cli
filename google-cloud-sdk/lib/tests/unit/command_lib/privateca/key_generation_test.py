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
"""Tests for google3.third_party.py.googlecloudsdk.api_lib.privateca.key_generation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import stat

from googlecloudsdk.command_lib.privateca import exceptions
from googlecloudsdk.command_lib.privateca import key_generation
from tests.lib import sdk_test_base
from tests.lib import test_case

RSA_PRIVATE_RE = (
    r'-----BEGIN RSA PRIVATE KEY-----[a-zA-Z0-9+/=\s]*-----END RSA PRIVATE '
    r'KEY-----')
RSA_PUBLIC_RE = (r'-----BEGIN PUBLIC KEY-----[a-zA-Z0-9+/=\s]*-----END PUBLIC '
                 r'KEY-----')


@test_case.Filters.RunOnlyIfModulePresent('cryptography',
                                          'not installed on all test platforms')
@test_case.Filters.DoNotRunInKokoro('Cryptography library not installed')
class TestKeyGen(sdk_test_base.WithLogCapture, sdk_test_base.WithTempCWD):

  def testRsa2048KeyGen(self):
    private_key, public_key = key_generation.RSAKeyGen()
    rsa_pub_compile = re.compile(RSA_PUBLIC_RE)
    rsa_priv_compile = re.compile(RSA_PRIVATE_RE)
    self.assertTrue(re.match(rsa_pub_compile, public_key.decode('utf-8')))
    self.assertTrue(re.match(rsa_priv_compile, private_key.decode('utf-8')))

    # pylint: disable=g-import-not-at-top
    from cryptography.hazmat.backends.openssl.backend import backend
    from cryptography.hazmat.primitives import serialization

    # Serialize keys bytes into key objects to ensure correctness of the data.
    private_key = serialization.load_pem_private_key(
        private_key, password=None, backend=backend)
    private_key = serialization.load_pem_public_key(public_key, backend=backend)

  def testFileExport(self):
    key_file_name = './private_key2.pem'
    private_key, _ = key_generation.RSAKeyGen()
    key_generation.ExportPrivateKey(key_file_name, private_key)
    self.AssertFileExists(key_file_name)
    self.AssertFileMatches(RSA_PRIVATE_RE, key_file_name)
    self.AssertLogContains(
        'A private key was exported to {}'.format(key_file_name))

    # Check that file is 0o400 after export
    st = os.stat(key_file_name)
    oct_perm = oct(st.st_mode)
    self.assertEqual(oct_perm, oct(0o100400))

  def testUnwritableFile(self):
    # Owner has only read permission before write.
    os.chmod(self.cwd_path, stat.S_IRUSR)
    key_file_name = './private_key.pem'
    with self.assertRaises(exceptions.FileOutputError):
      private_key, _ = key_generation.RSAKeyGen()
      key_generation.ExportPrivateKey(key_file_name, private_key)
