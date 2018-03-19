# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests for functions argument parsing."""

import re

from googlecloudsdk.api_lib.functions import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import properties
from tests.lib import sdk_test_base
from tests.lib import test_case


class ArgumentParsingTest(sdk_test_base.SdkBase):

  def __formatError(self, name, error_message):
    re.escape("Invalid value '{0}': {1}".format(name, error_message))

  # Tests for util.ValidateFunctionNameOrRaise
  def __goodFunctionName(self, name):
    self.assertEqual(util.ValidateFunctionNameOrRaise(name), name)

  def __badFunctionName(self, name):
    error_pattern = self.__formatError(name, util._FUNCTION_NAME_ERROR)
    with self.assertRaisesRegexp(arg_parsers.ArgumentTypeError, error_pattern):
      util.ValidateFunctionNameOrRaise(name)

  def testValidateFunctionName_singleLetter(self):
    self.__goodFunctionName('a')

  def testValidateFunctionName_letterAndDigits(self):
    self.__goodFunctionName('abcd1234')

  def testValidateFunctionName_letterAndDigitsUnordered(self):
    self.__goodFunctionName('a1b2c3d4')

  def testValidateFunctionName_withDash(self):
    self.__goodFunctionName('a-0')

  def testValidateFunctionName_withUnderscore(self):
    self.__goodFunctionName('a_b')

  def testValidateFunctionName_uppercaseAtStart(self):
    self.__goodFunctionName('Aa')

  def testValidateFunctionName_uppercaseInside(self):
    self.__goodFunctionName('aA')

  def testValidateFunctionName_maxLength(self):
    self.__goodFunctionName('a' + '0123456789' * 6 + '12')

  def testValidateFunctionName_maxLengthPlus1(self):
    self.__badFunctionName('a' + '0123456789' * 6 + '123')

  def testValidateFunctionName_endsWithDash(self):
    self.__badFunctionName('a-')

  def testValidateFunctionName_startsWithDigit(self):
    self.__badFunctionName('0a')

  def testValidateFunctionName_dollarSignInside(self):
    self.__badFunctionName('a$b')

  def testValidateFunctionName_atSignInside(self):
    self.__badFunctionName('a@b')

  def testValidateFunctionName_dotInside(self):
    self.__badFunctionName('a.b')

  # Tests for util.ValidateEntryPointNameOrRaise
  def __goodEntryPoint(self, name):
    self.assertEqual(util.ValidateEntryPointNameOrRaise(name), name)

  def __badEntryPoint(self, name):
    error_pattern = self.__formatError(name, util._ENTRY_POINT_NAME_ERROR)
    with self.assertRaisesRegexp(arg_parsers.ArgumentTypeError, error_pattern):
      util.ValidateEntryPointNameOrRaise(name)

  def testValidateEntryPointName_singleLetter(self):
    self.__goodEntryPoint('a')

  def testValidateEntryPointName_withDigit(self):
    self.__goodEntryPoint('a0')

  def testValidateEntryPointName_startsWithDigit(self):
    self.__goodEntryPoint('0a')

  def testValidateEntryPointName_justDigits(self):
    self.__goodEntryPoint('01')

  def testValidateEntryPointName_uppercase(self):
    self.__goodEntryPoint('A0')

  def testValidateEntryPointName_maxLength(self):
    self.__goodEntryPoint('0123456789' * 12 + '01234567')

  def testValidateEntryPointName_withUnderscore(self):
    self.__goodEntryPoint('a_b')

  def testValidateEntryPointName_startsWithUnderscore(self):
    self.__goodEntryPoint('_a')

  def testValidateEntryPointName_justUnderscore(self):
    self.__goodEntryPoint('_')

  def testValidateEntryPointName_withDot(self):
    self.__goodEntryPoint('abc.abc')

  def testValidateEntryPointName_withManyDots(self):
    self.__goodEntryPoint('a.b.c.d')

  def testValidateEntryPointName_maxLengthPlus1(self):
    self.__badEntryPoint('0123456789' * 12 + '012345678')

  def testValidateEntryPointName_withDash(self):
    self.__badEntryPoint('a-b')

  def testValidateEntryPointName_withDotFirst(self):
    self.__badEntryPoint('.abc')

  def testValidateEntryPointName_withDotLast(self):
    self.__badEntryPoint('abc.')

  def testValidateEntryPointName_withConsecutiveDots(self):
    self.__badEntryPoint('abc..abc')

  # Tests for util.ValidatePubsubTopicNameOrRaise
  def __goodTopic(self, name):
    properties.VALUES.core.project.Set('myproject')
    self.assertEqual(util.ValidatePubsubTopicNameOrRaise(name), name)

  def __badTopic(self, name):
    properties.VALUES.core.project.Set('myproject')
    error_pattern = self.__formatError(name, util._TOPIC_NAME_ERROR)
    with self.assertRaisesRegexp(arg_parsers.ArgumentTypeError, error_pattern):
      util.ValidatePubsubTopicNameOrRaise(name)

  def testValidateTopic_minLength(self):
    self.__goodTopic('abc')

  def testValidateTopic_withDigits(self):
    self.__goodTopic('a0123')

  def testValidateTopic_withPlus(self):
    self.__goodTopic('aaa+')

  def testValidateTopic_withPoint(self):
    self.__goodTopic('aaa.')

  def testValidateTopic_withUnderscore(self):
    self.__goodTopic('aaa_')

  def testValidateTopic_withTilde(self):
    self.__goodTopic('aaa~')

  def testValidateTopic_withPercent(self):
    self.__goodTopic('aaa%')

  def testValidateTopic_maxLength(self):
    self.__goodTopic('a' + '0123456789' * 25 + '0123')

  def testValidateTopic_maxLengthPlus1(self):
    self.__badTopic('a' + '0123456789' * 25 + '01234')

  def testValidateTopic_wayTooShort(self):
    self.__badTopic('a')

  def testValidateTopic_tooShort(self):
    self.__badTopic('aa')

  def testValidateTopic_withAsterisk(self):
    self.__badTopic('aaaa*')

  def testValidateTopic_startsWithUnderscore(self):
    self.__badTopic('_aaa')

  def testValidateTopic_fullName(self):
    self.__badTopic('projects/myproject/topics/topic')

  def testValidateTopic_withSlash(self):
    self.__badTopic('a/b')

  # Tests for util.ValidateAndStandarizeBucketUriOrRaise
  def __goodBareBucket(self, name):
    properties.VALUES.core.project.Set('myproject')
    self.assertEqual(util.ValidateAndStandarizeBucketUriOrRaise(name),
                     'gs://' + name.rstrip('/') + '/')

  def __badBucket(self, name):
    properties.VALUES.core.project.Set('myproject')
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      util.ValidateAndStandarizeBucketUriOrRaise(name)

  def __validMaxURL(self):
    # Generates a valid max length Bucket url based on these rules
    # https://cloud.google.com/storage/docs/naming#requirements
    lseg = '0123456789' * 6 + '012'
    sseg = '012345678'
    return '{l}.{l}.{l}.{s}.{s}.{s}'.format(l=lseg, s=sseg)

  def testValidateBucket_minLength(self):
    self.__goodBareBucket('aaa')

  def testValidateBucket_withDights(self):
    self.__goodBareBucket('a0000')

  def testValidateBucket_startsWithDights(self):
    self.__goodBareBucket('0000a')

  def testValidateBucket_justDigits(self):
    self.__goodBareBucket('00000')

  def testValidateBucket_withPoint(self):
    self.__goodBareBucket('abc.123')

  def testValidateBucket_withUnderscore(self):
    self.__goodBareBucket('abc_123')

  def testValidateBucket_withDash(self):
    self.__goodBareBucket('abc-123')

  def testValidateBucket_maxLength(self):
    self.__goodBareBucket(self.__validMaxURL())

  def testValidateBucket_withGcs(self):
    self.assertEqual(
        util.ValidateAndStandarizeBucketUriOrRaise('gs://aaa'), 'gs://aaa/')

  def testValidateBucket_withTrailingSlash(self):
    self.assertEqual(
        util.ValidateAndStandarizeBucketUriOrRaise('aaa/'), 'gs://aaa/')

  def testValidateBucket_withGcsAndTrailingSlash(self):
    self.assertEqual(
        util.ValidateAndStandarizeBucketUriOrRaise('gs://aaa/'), 'gs://aaa/')

  def testValidateBucket_maxLengthWithGcsAndTrailingSlash(self):
    full_length = 'gs://' + self.__validMaxURL() + '/'
    self.assertEqual(
        util.ValidateAndStandarizeBucketUriOrRaise(full_length), full_length)

  def testValidateBucket_maxLengthPlus1(self):
    self.__badBucket('0123456789' * 23 + '012')

  def testValidateBucket_wayTooShort(self):
    self.__badBucket('a')

  def testValidateBucket_tooShort(self):
    self.__badBucket('ab')

  def testValidateBucket_startsWithPoint(self):
    self.__badBucket('.abcd')

  def testValidateBucket_startsWithDash(self):
    self.__badBucket('-abcd')

  def testValidateBucket_startsWithUnderscore(self):
    self.__badBucket('_abcd')

  def testValidateBucket_endsWithPoint(self):
    self.__badBucket('abcd.')

  def testValidateBucket_endsWithDash(self):
    self.__badBucket('abcd-')

  def testValidateBucket_endsWithUnderscore(self):
    self.__badBucket('abcd_')

  def testValidateBucket_tooShortWithGcs(self):
    self.__badBucket('gcs:/aa')

  def testValidateBucket_invalidGcsPrefix_tooManySlashes(self):
    self.__badBucket('gcs:///aaaaa')

  def testValidateBucket_invalidGcsPrefix_tooFewSlashes(self):
    self.__badBucket('gcs:/aaaaa')

  def testValidateBucket_startsWithSlash(self):
    self.__badBucket('/aaaaa')

  def testValidateBucket_endsWithDoubleSlash(self):
    self.__goodBareBucket('aaaaa//')


if __name__ == '__main__':
  test_case.main()
