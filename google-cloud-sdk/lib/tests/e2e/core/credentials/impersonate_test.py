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

from tests.lib import cli_test_base
from tests.lib import e2e_base


class TestServiceAccountImpersonation(cli_test_base.CliTestBase):

  # TODO(b/147255499): remove this test after everything is on google-auth.
  def testOauth2client(self):
    with e2e_base.ImpersonationAccountAuth():
      self.Run('compute instances list')
    self.AssertErrContains(
        'This command is using service account impersonation')

  def testGoogleAuth(self):
    with e2e_base.ImpersonationAccountAuth():
      # dns surface is on google-auth
      self.Run('dns managed-zones list')
    self.AssertErrContains(
        'This command is using service account impersonation')
