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
"""dlp images redact tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.dlp import hooks
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.dlp import base


class RedactTest(base.DlpUnitTestBase):
  """dlp images redact tests."""

  @parameterized.named_parameters(
      ('DefaultJpg', calliope_base.ReleaseTrack.ALPHA, '.jpg',
       ['PHONE_NUMBER', 'PERSON_NAME'], False, None, False, None),
      ('JPEG', calliope_base.ReleaseTrack.ALPHA, '.jpeg',
       ['PHONE_NUMBER', 'PERSON_NAME', 'EMAIL_ADDRESS'], True, 'likely', True,
       '0,0,0'),
      ('SVG', calliope_base.ReleaseTrack.ALPHA, '.svg',
       ['EMAIL_ADDRESS'], True, 'unlikely', True, '0,1.0,0.5'),
      ('PNG', calliope_base.ReleaseTrack.ALPHA, '.png',
       ['PERSON_NAME'], True, 'very-unlikely', False, '0.4,0.5,0.5'),
      ('BMP', calliope_base.ReleaseTrack.ALPHA, '.bmp',
       ['PHONE_NUMBER', 'CREDIT_CARD', 'EMAIL_ADDRESS'], False, 'likely', True,
       '0.4,0,0.0'),
      ('NoExtension', calliope_base.ReleaseTrack.ALPHA, '',
       ['PHONE_NUMBER', 'PERSON_NAME', 'SSN'], False, 'possible', False,
       '0.1,0.0,0.0')
  )
  def testRedact(self,
                 track,
                 extension,
                 info_types,
                 include_quote,
                 min_likelihood,
                 remove_text,
                 redact_color_string):
    self.track = track
    test_file = self.MakeTestTextFile(
        file_name='tmp{}'.format(extension), contents=self.TEST_IMG_CONTENT)

    extension = extension or 'n_a'
    file_type = hooks.VALID_IMAGE_EXTENSIONS[extension]
    if min_likelihood:
      likelihood_enum_string = min_likelihood.replace('-', '_').upper()
    else:
      likelihood_enum_string = 'POSSIBLE'

    redact_request = self.MakeImageRedactRequest(
        file_type=file_type,
        info_types=info_types,
        min_likelihood=likelihood_enum_string,
        include_quote=include_quote,
        remove_text=remove_text,
        redact_color_string=redact_color_string)

    redact_response = self.MakeImageRedactResponse()
    self.client.projects_image.Redact.Expect(request=redact_request,
                                             response=redact_response)
    include_qt_flag = '--include-quote' if include_quote else ''
    likelihood_flag = (
        '--min-likelihood ' + min_likelihood if min_likelihood else '')
    info_type_values = ','.join(info_types)
    redact_text_flag = '--redact-all-text' if remove_text else ''
    if redact_color_string:
      redact_color_flag = '--redact-color '+ redact_color_string
    else:
      redact_color_flag = ''
    self.assertEqual(redact_response,
                     self.Run('dlp images redact {content_file} {likelihood} '
                              '--info-types {infotypes} {redact_text} '
                              '{color_flag} {includequote}'.format(
                                  content_file=test_file,
                                  infotypes=info_type_values,
                                  color_flag=redact_color_flag,
                                  includequote=include_qt_flag,
                                  likelihood=likelihood_flag,
                                  redact_text=redact_text_flag)))

  @parameterized.parameters(
      (calliope_base.ReleaseTrack.ALPHA, '0,1.3,0',
       'Invalid Color Value(s) [0,1.3,0].'),
      (calliope_base.ReleaseTrack.ALPHA, '1,2,3,4',
       'You must specify exactly 3 color values [1,2,3,4].'),
      (calliope_base.ReleaseTrack.ALPHA, '1',
       'You must specify exactly 3 color values [1].')
  )
  def testRedactWithBadColorFails(self, track, color_string, error_message):
    self.track = track
    test_file = self.MakeTestTextFile(
        file_name='tmp.svg', contents=self.TEST_IMG_CONTENT)
    with self.AssertRaisesExceptionMatches(hooks.RedactColorError,
                                           error_message):
      self.Run('dlp images redact {} --redact-color "{}" '
               '--info-types LAST_NAME'.format(test_file, color_string))

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters([calliope_base.ReleaseTrack.ALPHA])
  def testRedactWithBadExtensionFails(self, track):
    self.track = track
    test_file = self.MakeTestTextFile(file_name='tmp.txt',
                                      contents=self.TEST_IMG_CONTENT)

    with self.AssertRaisesExceptionMatches(
        hooks.ImageFileError, 'Must be one of [jpg, jpeg, png, bmp or svg]. '
        'Please double-check your input and try again.'):
      self.Run('dlp images redact {} --info-types '
               'PHONE_NUMBER,PERSON_NAME'.format(test_file))

  # TODO(b/117336602) Stop using parameterized for track parameterization.
  @parameterized.parameters((calliope_base.ReleaseTrack.ALPHA,))
  def testRedactWithOutputFile(self, track):
    properties.VALUES.core.user_output_enabled.Set(True)
    self.track = track
    test_file = self.MakeTestTextFile(
        file_name='tmp.jpeg', contents=self.TEST_IMG_CONTENT)
    output_file = os.path.join(self.temp_path, 'output.jpeg')

    redact_request = self.MakeImageRedactRequest(
        file_type='IMAGE_JPEG',
        info_types=['PHONE_NUMBER'],
        min_likelihood='POSSIBLE',
        include_quote=False)

    redacted_content = b'redacted content'
    redact_response = self.msg.GooglePrivacyDlpV2RedactImageResponse(
        extractedText='Foo', redactedImage=redacted_content)
    self.client.projects_image.Redact.Expect(request=redact_request,
                                             response=redact_response)
    self.assertEqual(
        redact_response,
        self.Run('dlp images redact {content_file} '
                 '--info-types PHONE_NUMBER --output-file {output_file}'.format(
                     content_file=test_file,
                     output_file=output_file)))
    self.AssertErrContains('The redacted contents can be viewed in [{}]'
                           .format(output_file))
    self.assertEqual(redacted_content,
                     files.ReadBinaryFileContents(output_file))


if __name__ == '__main__':
  test_case.main()
