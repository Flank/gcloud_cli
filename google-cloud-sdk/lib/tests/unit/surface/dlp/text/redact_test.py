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
"""dlp text redact tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class RedactTest(base.DlpUnitTestBase):
  """dlp text redact tests."""

  @parameterized.named_parameters(
      ('RedactTextDefault', calliope_base.ReleaseTrack.ALPHA, 'txt',
       ['PHONE_NUMBER', 'PERSON_NAME'], '', 'redact', None),
      ('ReplaceText', calliope_base.ReleaseTrack.ALPHA, 'txt',
       ['PHONE_NUMBER', 'PERSON_NAME', 'CREDIT_CARD_NUMBER'],
       'LIKELY', 'text', 'FOO'),
      ('ReplaceWithInfoTypes', calliope_base.ReleaseTrack.ALPHA, 'csv',
       ['EMAIL_ADDRESS'], 'VERY-LIKELY', 'info-type', None),
  )
  def testRedactWithFile(self, track, file_type, info_types, min_likelihood,
                         redaction_type, replacement_text):
    self.track = track
    test_file = self.MakeTestTextFile()
    if min_likelihood:
      likelihood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelihood_enum_string = 'POSSIBLE'

    if file_type == 'txt':
      test_file = self.MakeTestTextFile()
      file_content = self.TEST_CONTENT
    else:
      test_file = self.MakeTestTextFile(
          file_name='tmp.csv', contents=self.TEST_CSV_CONTENT)
      file_content = self.TEST_CSV_CONTENT

    if redaction_type == 'info-type':
      redaction_flag = '--replace-with-info-type'
    elif redaction_type == 'text':
      redaction_flag = '--replacement-text '+ replacement_text
    else:
      redaction_flag = '--remove-findings'

    redact_request = self.MakeTextRedactRequest(
        file_content, info_types, likelihood_enum_string, redaction_type,
        replacement_text)
    redact_response = self.MakeTextRedactResponse(
        file_content, info_types, likelihood_enum_string, redaction_type,
        replacement_text)
    self.client.projects_content.Deidentify.Expect(request=redact_request,
                                                   response=redact_response)
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood if min_likelihood else '')
    info_type_values = ','.join(info_types)

    cmd = ('dlp text redact --content-file {content_file} '
           '--info-types {infotypes} {redaction_type} '
           '{likelihood}'.format(content_file=test_file,
                                 infotypes=info_type_values,
                                 redaction_type=redaction_flag,
                                 likelihood=likelihood_flag))

    self.assertEqual(redact_response, self.Run(cmd))

  @parameterized.named_parameters(
      ('RedactTextDefault', calliope_base.ReleaseTrack.ALPHA,
       ['PHONE_NUMBER', 'PERSON_NAME'], '', 'redact', None),
      ('ReplaceText', calliope_base.ReleaseTrack.ALPHA,
       ['PHONE_NUMBER', 'PERSON_NAME', 'CREDIT_CARD_NUMBER'],
       'LIKELY', 'text', 'FOO'),
      ('ReplaceWithInfoTypes', calliope_base.ReleaseTrack.ALPHA,
       ['EMAIL_ADDRESS'], 'VERY-LIKELY', 'info-type', None),
  )
  def testRedactWithContent(self, track, info_types, min_likelihood,
                            redaction_type, replacement_text):
    self.track = track
    test_content = 'My Name is Bob. 212-555-1212'
    if min_likelihood:
      likelihood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelihood_enum_string = 'POSSIBLE'

    if redaction_type == 'info-type':
      redaction_flag = '--replace-with-info-type'
    elif redaction_type == 'text':
      redaction_flag = '--replacement-text '+ replacement_text
    else:
      redaction_flag = '--remove-findings'

    redact_request = self.MakeTextRedactRequest(
        test_content, info_types, likelihood_enum_string, redaction_type,
        replacement_text)
    redact_response = self.MakeTextRedactResponse(
        test_content, info_types, likelihood_enum_string, redaction_type,
        replacement_text)
    self.client.projects_content.Deidentify.Expect(request=redact_request,
                                                   response=redact_response)
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood if min_likelihood else '')
    info_type_values = ','.join(info_types)

    cmd = ('dlp text redact --content "{content}" '
           '--info-types {infotypes} {redaction_type} '
           '{likelihood}'.format(content=test_content,
                                 infotypes=info_type_values,
                                 redaction_type=redaction_flag,
                                 likelihood=likelihood_flag))

    self.assertEqual(redact_response, self.Run(cmd))

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testRedactWithContentAndFileFails(self, track):
    self.track = track
    test_file = self.MakeTestTextFile()
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'Exactly one of (--content | '
                                           '--content-file) must be specified'):
      self.Run('dlp text redact --content "My Name is Bob. 212-555-1212" '
               '--content-file {} --info-types PHONE_NUMBER,PERSON_NAME '
               '--remove-findings'.format(test_file))

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testRedactWithMultipleRedactOptionsFails(self, track):
    self.track = track
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError,
        'Exactly one of (--remove-findings | --replace-with-info-type | '
        '--replacement-text) must be specified'):
      self.Run('dlp text redact --content "My Name is Bob. 212-555-1212" '
               '--info-types PHONE_NUMBER,PERSON_NAME --remove-findings '
               '--replace-with-info-type')

  @parameterized.named_parameters(
      ('OneInfoType', calliope_base.ReleaseTrack.ALPHA, 'EMAIL_ADDRESS',
       ['EMAIL_ADDRESS']),
      ('MultipleInfoTypes', calliope_base.ReleaseTrack.ALPHA,
       'EMAIL_ADDRESS,PERSON_NAME', ['EMAIL_ADDRESS', 'PERSON_NAME']))
  def testRedactWithOutputFile(self, track, info_types, expected_info_types):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.track = track
    output_file = os.path.join(self.temp_path, 'output.csv')
    test_content = 'test,content'
    redacted_content = b'redacted,content'
    redact_request = self.MakeTextRedactRequest(
        test_content, expected_info_types, 'POSSIBLE', 'info-type')
    redact_response = self.MakeTextRedactResponse(
        redacted_content, expected_info_types, 'POSSIBLE', 'info-type', None)
    self.client.projects_content.Deidentify.Expect(request=redact_request,
                                                   response=redact_response)

    self.Run('dlp text redact --content "{content}" --info-types {info_types} '
             '--replace-with-info-type --output-file {output}'
             .format(content=test_content, info_types=info_types,
                     output=output_file))
    self.AssertErrContains('The redacted contents can be viewed in [{}]'
                           .format(output_file))
    self.assertEqual(redacted_content,
                     files.ReadBinaryFileContents(output_file))


if __name__ == '__main__':
  test_case.main()
