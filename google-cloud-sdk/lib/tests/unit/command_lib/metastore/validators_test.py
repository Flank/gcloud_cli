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
"""Unit tests for Dataproc Metastore validators."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.metastore import validators
from tests.lib import test_case


class ValidatorsTest(test_case.TestCase):
  """Dataproc Metastore validator tests class."""

  def testValidPort(self):
    """Tests valid port number."""
    valid_port = 9090
    self.assertEqual(validators.ValidatePort(valid_port), valid_port)

  def testInvalidPort(self):
    """Tests invalid port number."""
    invalid_port = 1
    with self.assertRaisesRegex(exceptions.BadArgumentException,
                                'Invalid value for [--port]'):
      validators.ValidatePort(invalid_port)

  def testValidGcsUri(self):
    """Tests valid gcs uri."""
    valid_gcs_uri = 'gs://'
    self.assertEqual(
        validators.ValidateGcsUri('--test-arg')(valid_gcs_uri), valid_gcs_uri)

  def testInvalidGcsUri(self):
    """Tests invalid gcs uri."""
    invalid_gcs_uri = 'invalid-test-uri'
    with self.assertRaisesRegex(exceptions.BadArgumentException,
                                r'Invalid value for \[--test-arg]'):
      validators.ValidateGcsUri('--test-arg')(invalid_gcs_uri)

  def testValidKerberosPrincipal(self):
    """Tests valid kerberos principal."""
    valid_kerberos_principal = 'foo/bar@baz.com'
    self.assertEqual(
        validators.ValidateKerberosPrincipal(valid_kerberos_principal),
        valid_kerberos_principal)

  def testInvalidKerberosPrincipal(self):
    """Tests invalid kerberos principal."""
    invalid_kerberos_principal = 'invalid-principal'
    with self.assertRaisesRegex(exceptions.BadArgumentException,
                                r'Invalid value for \[--kerberos-principal]'):
      validators.ValidateKerberosPrincipal(invalid_kerberos_principal)


if __name__ == '__main__':
  test_case.main()
