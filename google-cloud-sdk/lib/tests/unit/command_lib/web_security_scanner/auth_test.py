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

"""Tests for google3.third_party.py.tests.unit.command_lib.web_security_scanner.auth."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.web_security_scanner import auth
from tests.lib import test_case
from tests.lib.surface.web_security_scanner import base


class AuthTest(base.WebSecurityScannerScanConfigsBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  class FakeAuthArgs(object):

    def __init__(self,
                 auth_type=None,
                 auth_user=None,
                 auth_pass=None,
                 auth_url=None):
      self.auth_type = auth_type
      self.auth_user = auth_user
      self.auth_password = auth_pass
      self.auth_url = auth_url

  def testSetScanConfigAuth_MissingAuthType(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_user='user', auth_pass='pass')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-type'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_NoneAuthTypeWithOtherAuthFields(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='none', auth_pass='pass')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-type'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_None(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='none')

    actual = auth.SetScanConfigAuth(None, args, request)

    self.assertEqual(request, actual)

  def testSetScanConfigAuth_GoogleAuth(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(
        auth_type='google', auth_user='user@gmail.com', auth_pass='pass')
    expected = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
        scanConfig=self.messages.ScanConfig(
            authentication=self.messages.Authentication(
                googleAccount=self.messages.GoogleAccount(
                    username='user@gmail.com',
                    password='pass',
                ))))

    actual = auth.SetScanConfigAuth(None, args, request)

    self.assertEqual(actual, expected)

  def testSetScanConfigAuth_GoogleAuthMissingUser(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='google', auth_pass='pass')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-user'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_GoogleAuthMissingPassword(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='google', auth_user='user@gmail.com')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-password'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_CustomAuth(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(
        auth_type='custom',
        auth_user='user@gmail.com',
        auth_pass='pass',
        auth_url='http://example.com/login')
    expected = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
        scanConfig=self.messages.ScanConfig(
            authentication=self.messages.Authentication(
                customAccount=self.messages.CustomAccount(
                    username='user@gmail.com',
                    password='pass',
                    loginUrl='http://example.com/login',
                ))))

    actual = auth.SetScanConfigAuth(None, args, request)

    self.assertEqual(actual, expected)

  def testSetScanConfigAuth_CustomAuthMissingUser(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(
        auth_type='custom',
        auth_pass='pass',
        auth_url='http://example.com/login')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-user'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_CustomAuthMissingPassword(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(
        auth_type='custom',
        auth_user='user',
        auth_url='http://example.com/login')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-password'):
      auth.SetScanConfigAuth(None, args, request)

  def testSetScanConfigAuth_CustomAuthMissingUrl(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(
        auth_type='custom', auth_user='user', auth_pass='pass')

    with self.AssertRaisesToolExceptionRegexp(r'--auth-url'):
      auth.SetScanConfigAuth(None, args, request)

  def testAddAuthFieldMask_withOtherEntries(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
        updateMask='something')
    args = self.FakeAuthArgs(auth_type='custom')

    actual = auth.AddAuthFieldMask(None, args, request)

    self.assertEqual(actual.updateMask, 'something,authentication')

  def testAddAuthFieldMask_withoutOtherEntries(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='custom')

    actual = auth.AddAuthFieldMask(None, args, request)

    self.assertEqual(actual.updateMask, 'authentication')

  def testAddAuthFieldMask_withTypeNone_setsUpdateField(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest()
    args = self.FakeAuthArgs(auth_type='none')

    actual = auth.AddAuthFieldMask(None, args, request)

    self.assertEqual(actual.updateMask, 'authentication')

  def testAddAuthFieldMask_withoutAuthType(self):
    request = self.messages.WebsecurityscannerProjectsScanConfigsPatchRequest(
        updateMask='something')
    args = self.FakeAuthArgs()

    actual = auth.AddAuthFieldMask(None, args, request)

    self.assertEqual(actual.updateMask, 'something')


if __name__ == '__main__':
  test_case.main()
