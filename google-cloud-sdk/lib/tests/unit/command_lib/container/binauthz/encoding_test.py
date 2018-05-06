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

"""Tests for tests.unit.command_lib.container.binauthz.encoding."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.command_lib.container.binauthz import encoding
from tests.lib import test_case


class EncodingTest(test_case.TestCase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule()

  def testUnknownField(self):
    with self.assertRaisesRegexp(encoding.DecodeError, r'\.foo'):
      encoding.DictToMessageWithErrorCheck(
          {'foo': {'bar': 'baz'}}, self.messages.Policy)

  def testRepeatedField(self):
    with self.assertRaisesRegexp(
        encoding.DecodeError, r'\.admissionWhitelistPatterns\[0\]\.foo'):
      encoding.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [{'foo': 'bar'}]},
          self.messages.Policy)

  def testMap(self):
    with self.assertRaisesRegexp(
        encoding.DecodeError,
        r'\.clusterAdmissionRules\[us-east1-b.my-cluster-1\]\.evaluationMode'):
      encoding.DictToMessageWithErrorCheck(
          {
              'clusterAdmissionRules': {
                  'us-east1-b.my-cluster-1': {
                      'evaluationMode': 'NOT_A_REAL_ENUM'
                  }
              }
          },
          self.messages.Policy)

  def testMultiple_SameMessage(self):
    with self.assertRaisesRegexp(
        encoding.DecodeError,
        r'\.defaultAdmissionRule\.\{evaluationMode,nonConformanceAction\}'):
      encoding.DictToMessageWithErrorCheck(
          {
              'defaultAdmissionRule': {
                  'evaluationMode': 'NOT_A_REAL_ENUM',
                  'nonConformanceAction': 'NOT_A_REAL_ENUM',
              }
          },
          self.messages.Policy)

  def testMultiple_DifferentMessages(self):
    with self.assertRaisesRegexp(
        encoding.DecodeError,
        r'\.clusterAdmissionRules\[cluster-[12]\]\.evaluationMode[\w\W]*'
        r'\.clusterAdmissionRules\[cluster-[12]\]\.evaluationMode'):
      encoding.DictToMessageWithErrorCheck(
          {
              'clusterAdmissionRules': {
                  'cluster-1': {
                      'evaluationMode': 'NOT_A_REAL_ENUM'
                  },
                  'cluster-2': {
                      'evaluationMode': 'NOT_A_REAL_ENUM'
                  }
              }
          },
          self.messages.Policy)

  def testTypeMismatch_HeterogeneousRepeated(self):
    with self.assertRaisesRegexp(
        encoding.DecodeError,
        r'\.admissionWhitelistPatterns\[0\]\.namePatterns'):
      encoding.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [{'namePatterns': ['a', 1]}]},
          self.messages.Policy)

  def testTypeMismatch_Scalar(self):
    with self.assertRaisesRegexp(
        encoding.ScalarTypeMismatchError,
        r'Expected type <type.* for field updateTime, found 1'):
      encoding.DictToMessageWithErrorCheck(
          {'updateTime': 1},
          self.messages.Policy)

  def testTypeMismatch_Message_None(self):
    # TODO(b/77547931): Improve this error case.
    with self.assertRaises(AttributeError):
      encoding.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [None]},
          self.messages.Policy)

  def testTypeMismatch_Message_Int(self):
    # TODO(b/77547931): Improve this error case.
    with self.assertRaises(AttributeError):
      encoding.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [1]},
          self.messages.Policy)


if __name__ == '__main__':
  test_case.main()
