# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Tests for the e2e_base module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case


class AuthTests(cli_test_base.CliTestBase):

  def testRefreshToken(self):
    with e2e_base.RefreshTokenAuth() as auth:
      # Make sure activated credentials are usable.
      self.Run('compute zones list --project={0}'.format(auth.Project()))
      self.AssertOutputContains('us-central1')

  def testNoAuth(self):
    with self.assertRaisesRegex(
        store.TokenRefreshError,
        'There was a problem refreshing your current auth tokens'):
      with e2e_base.RefreshTokenAuth('fake-token'):
        pass

  def testServiceAccount(self):
    with e2e_base.ServiceAccountAuth() as auth:
      # Make sure activated credentials are usable.
      self.Run('compute zones list --project={0}'.format(auth.Project()))
      self.AssertOutputContains('us-central1')

  def testP12ServiceAccount(self):
    try:
      import OpenSSL  # pylint: disable=g-import-not-at-top,unused-variable
    except ImportError:
      raise self.SkipTest('Needs PyOpenSSL installed.')

    with e2e_base.P12ServiceAccountAuth() as auth:
      # Make sure activated credentials are usable.
      self.Run('compute zones list --project={0}'.format(auth.Project()))
      self.AssertOutputContains('us-central1')


if __name__ == '__main__':
  test_case.main()
