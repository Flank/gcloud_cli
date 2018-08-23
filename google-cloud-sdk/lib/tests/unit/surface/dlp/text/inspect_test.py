# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""dlp text inspect tests."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class InspectTest(base.DlpUnitTestBase):
  """dlp text inspect tests."""

  @parameterized.named_parameters(
      ('DefaultCase', calliope_base.ReleaseTrack.ALPHA, 'txt',
       ['PHONE_NUMBER', 'PERSON_NAME'], False, False, '', None),
      ('AllOptions', calliope_base.ReleaseTrack.ALPHA, 'csv', [
          'PHONE_NUMBER', 'PERSON_NAME', 'EMAIL_ADDRESS'
      ], True, True, 'very-likely', 10),
  )
  def testInspectWithFile(self, track, file_type, info_types, include_quote,
                          exclude_info_types, min_likelihood, max_findings):
    self.track = track
    if file_type == 'txt':
      test_file = self.MakeTestTextFile()
      file_content = self.TEST_CONTENT
    else:
      test_file = self.MakeTestTextFile(
          file_name='tmp.csv', contents=self.TEST_CSV_CONTENT)
      file_content = self.TEST_CSV_CONTENT

    if min_likelihood:
      likelyhood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelyhood_enum_string = 'POSSIBLE'

    inspect_request = self.MakeTextInspectRequest(
        file_content,
        info_types=info_types,
        limit=max_findings,
        include_quote=include_quote,
        exclude_info_types=exclude_info_types,
        min_likelihood=likelyhood_enum_string)

    inspect_response = self.MakeTextInspectResponse(
        likelihood=likelyhood_enum_string,
        include_quote=include_quote,
        exclude_info_types=exclude_info_types,
        info_types=info_types,
        limit=max_findings)
    self.client.projects_content.Inspect.Expect(
        request=inspect_request, response=inspect_response)
    include_qt_flag = '--include-quote' if include_quote else ''
    exclude_it_flag = '--exclude-info-types' if exclude_info_types else ''
    likelihood_flag = ('--min-likelihood ' + min_likelihood
                       if min_likelihood else '')
    info_type_values = ','.join(info_types)
    max_findings_flag = ('--max-findings {}'.format(max_findings)
                         if max_findings else '')

    self.assertEqual(
        inspect_response,
        self.Run('dlp text inspect --content-file {content_file} '
                 '--info-types {infotypes} {maxfindings}  '
                 '{includequote} {excludeinfotypes} {likelihood}'.format(
                     content_file=test_file,
                     infotypes=info_type_values,
                     includequote=include_qt_flag,
                     excludeinfotypes=exclude_it_flag,
                     likelihood=likelihood_flag,
                     maxfindings=max_findings_flag)))

  @parameterized.named_parameters(
      ('DefaultCase', calliope_base.ReleaseTrack.ALPHA,
       ['PHONE_NUMBER', 'PERSON_NAME'], False, False, '', None),
      ('AllOptionsCase', calliope_base.ReleaseTrack.ALPHA, [
          'PHONE_NUMBER', 'PERSON_NAME', 'EMAIL_ADDRESS'
      ], True, True, 'very-likely', 10))
  def testInpectWithContent(self, track, info_types, include_quote,
                            exclude_info_types, min_likelihood, max_findings):
    self.track = track
    if min_likelihood:
      likelyhood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelyhood_enum_string = 'POSSIBLE'
    content = 'My Name is Bob. 212-555-1212'
    inspect_request = self.MakeTextInspectRequest(
        content,
        info_types=info_types,
        limit=max_findings,
        include_quote=include_quote,
        exclude_info_types=exclude_info_types,
        min_likelihood=likelyhood_enum_string)

    inspect_response = self.MakeTextInspectResponse(
        likelihood=likelyhood_enum_string,
        include_quote=include_quote,
        exclude_info_types=exclude_info_types,
        info_types=info_types,
        limit=max_findings)

    self.client.projects_content.Inspect.Expect(
        request=inspect_request, response=inspect_response)
    include_qt_flag = '--include-quote' if include_quote else ''
    exclude_it_flag = '--exclude-info-types' if exclude_info_types else ''
    likelihood_flag = ('--min-likelihood ' + min_likelihood
                       if min_likelihood else '')
    info_type_values = ','.join(info_types)
    max_findings_flag = ('--max-findings {}'.format(max_findings)
                         if max_findings else '')

    self.assertEqual(
        inspect_response,
        self.Run('dlp text inspect --content "{content}" '
                 '--info-types {infotypes} {maxfindings}  '
                 '{includequote} {excludeinfotypes} {likelihood}'.format(
                     content=content,
                     infotypes=info_type_values,
                     includequote=include_qt_flag,
                     excludeinfotypes=exclude_it_flag,
                     likelihood=likelihood_flag,
                     maxfindings=max_findings_flag)))

  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testInpectWithFileAndContentFails(self, track):
    self.track = track
    test_file = self.MakeTestTextFile()
    with self.AssertRaisesExceptionMatches(
        cli_test_base.MockArgumentError, 'Exactly one of (--content | '
        '--content-file) must be specified'):
      self.Run('dlp text inspect --content "My Name is Bob. 212-555-1212" '
               '--content-file {} --info-types PHONE_NUMBER,PERSON_NAME'.format(
                   test_file))


if __name__ == '__main__':
  test_case.main()
