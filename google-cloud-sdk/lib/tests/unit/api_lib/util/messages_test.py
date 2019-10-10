# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.util.messages."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import messages as messages_util
from tests.lib import subtests
from tests.lib import test_case


class UpdateMessageTest(subtests.Base):
  """Tests messages.UpdateMessage."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('sql', 'v1beta4')
    self.update_message = messages_util.UpdateMessage

  def testUpdateWithBasicDiff(self):
    instance = self.messages.DatabaseInstance(
        name='test-instance',
        region='us-central',
        settings=self.messages.Settings(
            userLabels=None, availabilityType='ZONAL'))
    diff = {
        'name': 'different-test',
        'settings': {
            'availabilityType': 'REGIONAL'
        }
    }
    instance = self.update_message(instance, diff)

    # Ensure that the values in the diff have changed
    self.assertEqual(instance.name, 'different-test')
    self.assertEqual(instance.settings.availabilityType, 'REGIONAL')

    # Ensure that values outside the diff have not changed
    self.assertEqual(instance.region, 'us-central')

  def testUpdateWithBadProp(self):
    instance = self.messages.DatabaseInstance(
        name='test-instance',
        settings=self.messages.Settings(
            userLabels=None, availabilityType='ZONAL'))
    diff = {'settings': {'ohno': 234, 'availabilityType': 'REGIONAL'}}
    instance = self.update_message(instance, diff)

    # Test that the bad property didn't somehow get added
    self.assertFalse(hasattr(instance, 'ohno'))

    # Test that valid property got added
    self.assertEqual(instance.settings.availabilityType, 'REGIONAL')


class DictToMessagesWithErrorCheckTest(test_case.WithContentAssertions):

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule(
        'binaryauthorization', 'v1alpha2')

  def testValid(self):
    self.assertEqual(
        messages_util.DictToMessageWithErrorCheck(
            {'name': 'sam'}, self.messages.Policy),
        self.messages.Policy(name='sam'))

  def testUnknownField(self):
    with self.assertRaisesRegexp(messages_util.DecodeError, r'\.foo'):
      messages_util.DictToMessageWithErrorCheck(
          {'foo': {'bar': 'baz'}}, self.messages.Policy)

  def testRepeatedField(self):
    with self.assertRaisesRegexp(
        messages_util.DecodeError, r'\.admissionWhitelistPatterns\[0\]\.foo'):
      messages_util.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [{'foo': 'bar'}]},
          self.messages.Policy)

  def testMap(self):
    with self.assertRaisesRegexp(
        messages_util.DecodeError,
        r'\.clusterAdmissionRules\[us-east1-b.my-cluster-1\]\.evaluationMode'):
      messages_util.DictToMessageWithErrorCheck(
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
        messages_util.DecodeError,
        r'\.defaultAdmissionRule\.\{evaluationMode,nonConformanceAction\}'):
      messages_util.DictToMessageWithErrorCheck(
          {
              'defaultAdmissionRule': {
                  'evaluationMode': 'NOT_A_REAL_ENUM',
                  'nonConformanceAction': 'NOT_A_REAL_ENUM',
              }
          },
          self.messages.Policy)

  def testMultiple_DifferentMessages(self):
    with self.assertRaisesRegexp(
        messages_util.DecodeError,
        r'\.clusterAdmissionRules\[cluster-[12]\]\.evaluationMode[\w\W]*'
        r'\.clusterAdmissionRules\[cluster-[12]\]\.evaluationMode'):
      messages_util.DictToMessageWithErrorCheck(
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
        messages_util.DecodeError,
        r'\.admissionWhitelistPatterns\[0\]\.namePatterns'):
      messages_util.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [{'namePatterns': ['a', 1]}]},
          self.messages.Policy)

  def testTypeMismatch_Scalar(self):
    with self.assertRaisesRegexp(
        messages_util.ScalarTypeMismatchError,
        r'Expected type <(type|class).* for field updateTime, found 1'):
      messages_util.DictToMessageWithErrorCheck(
          {'updateTime': 1},
          self.messages.Policy)

  def testTypeMismatch_Message_None(self):
    # TODO(b/77547931): Improve this error case.
    with self.assertRaises(AttributeError):
      messages_util.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [None]},
          self.messages.Policy)

  def testTypeMismatch_Message_Int(self):
    # TODO(b/77547931): Improve this error case.
    with self.assertRaises(AttributeError):
      messages_util.DictToMessageWithErrorCheck(
          {'admissionWhitelistPatterns': [1]},
          self.messages.Policy)


if __name__ == '__main__':
  test_case.main()
