# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for gcloud app ssl-certificates."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import parameterized
from tests.lib.surface.app import ssl_certificates_base

CERTIFICATE = 'cert_data'
PRIVATE_KEY = 'key_data'


class SslCertificatesUpdateTest(ssl_certificates_base.SslCertificatesBase,
                                parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testUpdateSslCertificate(self):
    self.ExpectUpdateSslCertificate('1234', 'example.com', 'cert_data',
                                    'key_data',
                                    'displayName,certificateRawData')
    self.Run("""app ssl-certificates update 1234
             --display-name=example.com
             --certificate={certificate_file}
             --private-key={key_file}
        """.format(
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))
    self.AssertErrContains('Updated [1234].')

  @parameterized.parameters(
      ('--certificate', '--private-key'),
      ('--private-key', '--certificate')
  )
  def testUpdateSslCertificate_RequiredArgs(self, flag, missing_flag):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [{}]: The certificate and the private key '
        'must both be updated together.'.format(missing_flag)):
      self.Run('app ssl-certificates update 1234 '
               '--display-name=example.com '
               '{}=file_path'.format(flag))


class SslCertificatesUpdateBetaTest(
    ssl_certificates_base.SslCertificatesBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testUpdateSslCertificate(self):
    self.ExpectUpdateSslCertificate('1234', 'example.com', 'cert_data',
                                    'key_data',
                                    'displayName,certificateRawData')
    self.Run("""app ssl-certificates update 1234
             --display-name=example.com
             --certificate={certificate_file}
             --private-key={key_file}
        """.format(
            certificate_file=self.certificate_file,
            key_file=self.private_key_file))
    self.AssertErrContains('Updated [1234].')
