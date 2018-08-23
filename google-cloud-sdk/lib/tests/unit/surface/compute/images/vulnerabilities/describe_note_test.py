# -*- coding: utf-8 -*- #
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
"""Tests for images vulnerabilities describe-note subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as apitools_mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base


class DescribeNoteTest(
    sdk_test_base.WithFakeAuth,
    cli_test_base.CliTestBase,
    parameterized.TestCase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.mock_client = apitools_mock.Client(
        core_apis.GetClientClass('containeranalysis', 'v1alpha1'),
        real_client=core_apis.GetClientInstance(
            'containeranalysis', 'v1alpha1', no_http=True),
    )
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.messages = apis.GetMessagesModule('containeranalysis', 'v1alpha1')

  @parameterized.named_parameters(
      ('ByRelativeName', 'providers/goog-vulnz/notes/CVE-2017-16531'),
      ('ByNameAndProject', 'CVE-2017-16531 --project goog-vulnz'),
  )
  def testDescribeNote(self, note_string):
    expected_request = self.messages.ContaineranalysisProvidersNotesGetRequest(
        name='providers/goog-vulnz/notes/CVE-2017-16531',
    )
    expected_response = self.messages.Note(
        longDescription='foobar',
        name='barfoo',
        shortDescription='fbr',
    )
    self.mock_client.providers_notes.Get.Expect(
        expected_request, expected_response)
    response = self.Run(
        'compute images vulnerabilities describe-note ' + note_string)
    self.assertEqual(expected_response, response)
