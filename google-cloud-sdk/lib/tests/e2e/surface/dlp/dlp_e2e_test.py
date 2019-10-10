# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""End to End tests for the dlp commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import test_case

TEST_CONTENT = (
    'My name is Paul Jones 333-555-1212 and my email is nan@testemail.com')


TEST_CONTENT_RESULT = ('My name is [REDACTED] [REDACTED] and '
                       'my email is [REDACTED]')


class DlpE2ETest(e2e_base.WithServiceAuth, cli_test_base.CliTestBase):
  """End to End tests for gcloud dlp commands."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def testTextRedact(self):
    self.Run('dlp text redact --content "{}" --info-types '
             'PHONE_NUMBER,PERSON_NAME,EMAIL_ADDRESS --replacement-text '
             '"[REDACTED]" '.format(TEST_CONTENT))
    self.AssertOutputContains(TEST_CONTENT_RESULT)


if __name__ == '__main__':
  test_case.main()
