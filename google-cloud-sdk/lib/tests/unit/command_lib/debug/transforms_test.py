# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Tests for the debug API wrapper module."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.debug import transforms
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import sdk_test_base


class TransformTests(sdk_test_base.SdkBase):

  def SetUp(self):
    self.debug_messages = core_apis.GetMessagesModule('clouddebugger', 'v2')

  def testShortStatusNotFinal(self):
    err = {}
    self.assertEqual(transforms.TransformShortStatus(err), 'ACTIVE')

  def testShortStatusNoStatus(self):
    err = {'isFinalState': True}
    self.assertEqual(transforms.TransformShortStatus(err), 'COMPLETED')

  def testShortStatusNoError(self):
    err = {'isFinalState': True, 'status': {'isError': False}}
    self.assertEqual(transforms.TransformShortStatus(err), 'COMPLETED')

  def testShortStatusWithSourceLocationError(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'refersTo': (
                self.debug_messages.StatusMessage.
                RefersToValueValuesEnum.BREAKPOINT_SOURCE_LOCATION
            )
        }
    }
    self.assertEqual(transforms.TransformShortStatus(err),
                     'SOURCE_LOCATION_ERROR')

  def testFullStatusNotFinal(self):
    err = {}
    self.assertEqual(transforms.TransformFullStatus(err), 'ACTIVE')

  def testFullStatusNoStatus(self):
    err = {'isFinalState': True}
    self.assertEqual(transforms.TransformFullStatus(err), 'COMPLETED')

  def testFullStatusNoError(self):
    err = {'isFinalState': True, 'status': {'isError': False}}
    self.assertEqual(transforms.TransformFullStatus(err), 'COMPLETED')

  def testFullStatusWithSourceLocationError(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'refersTo': (
                self.debug_messages.StatusMessage.
                RefersToValueValuesEnum.BREAKPOINT_SOURCE_LOCATION
            ),
            'description': {
                'format': 'Invalid location $0:$1',
                'parameters': ['foo.py', '9999']
            }
        }
    }
    self.assertEqual(transforms.TransformFullStatus(err),
                     'SOURCE_LOCATION_ERROR: Invalid location foo.py:9999')

  def testFullStatusWithBadKeyError(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'refersTo': (
                self.debug_messages.StatusMessage.
                RefersToValueValuesEnum.BREAKPOINT_SOURCE_LOCATION
            ),
            'description': {
                'format': 'Bad format string {foo}',
                'parameters': ['foo.py', '9999']
            }
        }
    }
    self.assertEqual(
        transforms.TransformFullStatus(err),
        'SOURCE_LOCATION_ERROR: Malformed status message: {0}'.format(
            err['status']))

  def testFullStatusBadIndexError(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'refersTo': (
                self.debug_messages.StatusMessage.
                RefersToValueValuesEnum.BREAKPOINT_SOURCE_LOCATION
            ),
            'description': {
                'format': 'Invalid location $0:$9999',
                'parameters': ['foo.py', '9999']
            }
        }
    }
    self.assertEqual(
        transforms.TransformFullStatus(err),
        'SOURCE_LOCATION_ERROR: Malformed status message: {0}'.format(
            err['status']))

  def testFullStatusWithUnspecifiedError(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'refersTo': (
                self.debug_messages.StatusMessage.
                RefersToValueValuesEnum.UNSPECIFIED
            ),
            'description': {
                'format': 'Random Error'
            }
        }
    }
    self.assertEqual(transforms.TransformFullStatus(err),
                     'UNSPECIFIED_ERROR: Random Error')

  def testFullStatusWithNoRefersTo(self):
    err = {
        'isFinalState': True,
        'status': {
            'isError': True,
            'description': {
                'format': 'Raw Error'
            }
        }
    }
    self.assertEqual(transforms.TransformFullStatus(err),
                     'UNKNOWN_ERROR: Raw Error')


if __name__ == '__main__':
  sdk_test_base.main()
