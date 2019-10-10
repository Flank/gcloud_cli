# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.util.files import Error as FileError
from tests.lib import cli_test_base
from tests.lib.surface.app import ssl_certificates_base

CERTIFICATE = 'cert_data'
PRIVATE_KEY = 'key_data'


class SslCertificatesCreateTest(ssl_certificates_base.SslCertificatesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testCreateSslCertificate(self):
    self.ExpectCreateSslCertificate('1234', 'example.com', 'cert_data',
                                    'key_data')
    result = self.Run("""app ssl-certificates create
            --display-name=example.com
            --certificate={certificate_file}
            --private-key={key_file}
         """.format(
             certificate_file=self.certificate_file,
             key_file=self.private_key_file))
    self.assertEqual(result.id, '1234')
    self.assertEqual(result.certificateRawData.publicCertificate, 'cert_data')
    self.assertEqual(result.certificateRawData.privateKey, 'key_data')
    self.AssertErrContains('Created [1234].')

  def testCreateSslCertificate_missingKey(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --private-key: Must be specified.'):
      self.Run("""app ssl-certificates create
                --display-name=example.com
                --certificate={certificate_file}
          """.format(certificate_file=self.certificate_file))

  def testCreateSslCertificate_missingCert(self):
    with self.assertRaisesRegex(
        cli_test_base.MockArgumentError,
        'argument --certificate: Must be specified.'):
      self.Run("""app ssl-certificates create
              --display-name=example.com
              --private-key={key_file}
          """.format(key_file=self.private_key_file))

  def testCreateSslCertificate_invalidFile(self):
    with self.assertRaises(FileError):
      self.Run("""app ssl-certificates create
              --display-name=example.com
              --certificate=non-existent.cer
              --private-key={key_file}
          """.format(key_file=self.private_key_file))

    self.AssertErrContains('Unable to read file [non-existent.cer]')


class SslCertificatesCreateBetaTest(
    ssl_certificates_base.SslCertificatesBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testCreateSslCertificate(self):
    self.ExpectCreateSslCertificate('1234', 'example.com', 'cert_data',
                                    'key_data')
    result = self.Run("""app ssl-certificates create
            --display-name=example.com
            --certificate={certificate_file}
            --private-key={key_file}
         """.format(
             certificate_file=self.certificate_file,
             key_file=self.private_key_file))
    self.assertEqual(result.id, '1234')
    self.assertEqual(result.certificateRawData.publicCertificate, 'cert_data')
    self.assertEqual(result.certificateRawData.privateKey, 'key_data')
