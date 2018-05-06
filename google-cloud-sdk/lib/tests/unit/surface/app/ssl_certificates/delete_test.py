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
from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.app import ssl_certificates_base

CERTIFICATE = 'cert_data'
PRIVATE_KEY = 'key_data'


class SslCertificatesDeleteTest(ssl_certificates_base.SslCertificatesBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testDeleteSslCertificate(self):
    self.ExpectDeleteSslCertificate('1234')
    self.Run('app ssl-certificates delete 1234')
    self.AssertErrContains('Deleted [1234].')


class SslCertificatesDeleteBetaTest(
    ssl_certificates_base.SslCertificatesBetaBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.certificate_file = self.Touch(
        self.temp_path, 'cert.crt', contents=CERTIFICATE)
    self.private_key_file = self.Touch(
        self.temp_path, 'private.key', contents=PRIVATE_KEY)

  def testDeleteSslCertificate(self):
    self.ExpectDeleteSslCertificate('1234')
    self.Run('app ssl-certificates delete 1234')
    self.AssertErrContains('Deleted [1234].')
