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

"""Tests for googlecloudsdk.api_lib.auth.util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from googlecloudsdk.api_lib.auth import util as auth_util
from tests.lib import cli_test_base


class UtilTest(cli_test_base.CliTestBase):

  def SetUp(self):
    client_id_file_content = {
        'installed': {
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'auth_uri': 'auth_uri',
            'token_uri': 'token_uri'
        }
    }
    wrong_client_id_file_content = {
        'web': {
            'client_id': 'client_id',
            'client_secret': 'client_secret',
            'auth_uri': 'auth_uri',
            'token_uri': 'token_uri'
        }
    }

    self.client_id_file = self.Touch(
        self.temp_path, contents=json.dumps(client_id_file_content))
    self.wrong_client_id_file = self.Touch(
        self.temp_path, contents=json.dumps(wrong_client_id_file_content))

  def testAssertClientSecretIsInstalledType_Correct(self):
    auth_util.AssertClientSecretIsInstalledType(self.client_id_file)

  def testAssertClientSecretIsInstalledType_Wrong(self):
    with self.AssertRaisesExceptionRegexp(
        auth_util.InvalidClientSecretsError,
        "Only client IDs of type 'installed' are allowed.*"):
      auth_util.AssertClientSecretIsInstalledType(self.wrong_client_id_file)


