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
"""Tests for revoking a certificate."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import certificate_utils
from googlecloudsdk.calliope import exceptions
from surface.privateca.certificates import revoke
from tests.lib import cli_test_base
from tests.lib.calliope import util

import mock


class RevokeFlagsTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    revoke.Revoke.Args(self.parser)

  def testCertificateFlowWithFullCertificateNameSucceeds(self):
    args = self.parser.parse_args([
        '--certificate',
        'projects/foo/locations/us-west1/certificateAuthorities/ca/certificates/c',
    ])
    cert_ref = revoke._ParseCertificateResource(args)
    self.assertEqual(cert_ref.projectsId, 'foo')
    self.assertEqual(cert_ref.locationsId, 'us-west1')
    self.assertEqual(cert_ref.certificateAuthoritiesId, 'ca')
    self.assertEqual(cert_ref.certificatesId, 'c')

  def testCertificateFlowWithCertificateIdAndIssuerSucceeds(self):
    args = self.parser.parse_args([
        '--certificate', 'c', '--issuer', 'ca', '--issuer-location', 'us-west1'
    ])
    cert_ref = revoke._ParseCertificateResource(args)
    self.assertEqual(cert_ref.projectsId, 'fake-project')
    self.assertEqual(cert_ref.locationsId, 'us-west1')
    self.assertEqual(cert_ref.certificateAuthoritiesId, 'ca')
    self.assertEqual(cert_ref.certificatesId, 'c')

  @mock.patch.object(
      certificate_utils, 'GetCertificateBySerialNum', autospec=True)
  def testSerialFlowWithIssuerSucceeds(self, mock_fn):
    messages = privateca_base.GetMessagesModule()
    mock_fn.return_value = messages.Certificate(
        name='projects/fake-project/locations/us-west1/certificateAuthorities/ca/certificates/c'
    )

    args = self.parser.parse_args([
        '--serial-number', 'FFF', '--issuer', 'ca', '--issuer-location',
        'us-west1'
    ])
    cert_ref = revoke._ParseCertificateResource(args)
    self.assertEqual(cert_ref.projectsId, 'fake-project')
    self.assertEqual(cert_ref.locationsId, 'us-west1')
    self.assertEqual(cert_ref.certificateAuthoritiesId, 'ca')
    self.assertEqual(cert_ref.certificatesId, 'c')

  def testCertificateFlowWithoutIssuerFails(self):
    args = self.parser.parse_args(['--certificate', 'cert'])
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--issuer]'):
      revoke._ParseCertificateResource(args)

  def testCertificateFlowWithoutIssuerLocationFails(self):
    args = self.parser.parse_args(['--certificate', 'cert', '--issuer', 'ca'])
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        '--issuer-location'):
      revoke._ParseCertificateResource(args)

  def testCertificateFlowWithIssuerLocationButNoIssuerFails(self):
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'argument --issuer-location: --issuer must be specified.'):
      self.parser.parse_args(
          ['--certificate', 'cert', '--issuer-location', 'us-west1'])

  def testSerialFlowWithoutIssuerFails(self):
    args = self.parser.parse_args(['--serial-number', 'FFF'])
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--issuer]'):
      revoke._ParseCertificateResource(args)
