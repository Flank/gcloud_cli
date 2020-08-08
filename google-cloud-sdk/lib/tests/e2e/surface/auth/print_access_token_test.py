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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base


class PrintAccessTokenTestServiceAccount(e2e_base.WithServiceAuth):

  def testPrintAccessToken(self):
    self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')

  def testPrintAccessToken_Oauth2client(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)
    self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')


class PrintAccessTokenTestUserAccount(e2e_base.WithExpiredUserAuth):

  def testPrintAccessToken(self):
    self.assertTrue(self.Run('config get-value account').endswith('@gmail.com'))
    self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')

  def testPrintAccessToken_Oauth2client(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)
    self.assertTrue(self.Run('config get-value account').endswith('@gmail.com'))
    self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')


@sdk_test_base.Filters.RunOnlyOnGCE
class PrintAccessTokenGceServiceAccount(cli_test_base.CliTestBase):

  def testPrintAccessToken(self):
    with e2e_base.GceServiceAccount() as auth:
      self.Run('auth print-access-token {}'.format(auth.Account()))
    self.AssertOutputNotEquals('')

  def testPrintAccessToken_Oauth2client(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)
    with e2e_base.GceServiceAccount() as auth:
      self.Run('auth print-access-token {}'.format(auth.Account()))
    self.AssertOutputNotEquals('')


class PrintAccessTokenImpersonation(cli_test_base.CliTestBase):

  def testPrintAccessToken(self):
    with e2e_base.ImpersonationAccountAuth():
      self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')
    self.AssertErrContains(
        'This command is using service account impersonation')

  def testPrintAccessToken_Oauth2client(self):
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)
    with e2e_base.ImpersonationAccountAuth():
      self.Run('auth print-access-token')
    self.AssertOutputNotEquals('')
    self.AssertErrContains(
        'This command is using service account impersonation')


class PrintAccessTokenP12ServiceAccount(cli_test_base.CliTestBase):

  def testPrintAccessToken(self):
    try:
      import OpenSSL  # pylint: disable=g-import-not-at-top,unused-variable
    except ImportError:
      raise self.SkipTest('Needs PyOpenSSL installed.')
    with e2e_base.P12ServiceAccountAuth() as auth:
      self.Run('auth print-access-token {}'.format(auth.Account()))
    self.AssertOutputNotEquals('')

  def testPrintAccessToken_Oauth2client(self):
    try:
      import OpenSSL  # pylint: disable=g-import-not-at-top,unused-variable
    except ImportError:
      raise self.SkipTest('Needs PyOpenSSL installed.')
    self.StartObjectPatch(
        properties.VALUES.auth.disable_load_google_auth,
        'GetBool',
        return_value=True)
    with e2e_base.P12ServiceAccountAuth() as auth:
      self.Run('auth print-access-token {}'.format(auth.Account()))
    self.AssertOutputNotEquals('')
