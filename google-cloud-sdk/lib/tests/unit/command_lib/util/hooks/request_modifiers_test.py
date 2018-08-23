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

"""Tests for the request_modifiers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages as _messages
from googlecloudsdk.command_lib.util.hooks import request_modifiers
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base


class RequestModifiersTest(sdk_test_base.SdkBase):
  """Tests for request modifier Python hooks."""

  def testSetFieldFromArg(self):
    class FakeMessage(_messages.Message):
      string1 = _messages.StringField(1)

    class Args(object):
      foo = 'bar'

    message = FakeMessage()
    message = request_modifiers.SetFieldFromArg('string1', 'foo')(
        None, Args(), message)
    self.assertEqual('bar', message.string1)

  def testSetFieldFromRelativeName(self):
    class FakeMessage(_messages.Message):
      string1 = _messages.StringField(1)

    ref = resources.REGISTRY.Create(
        'compute.instances', project='p', zone='z', instance='i')
    message = FakeMessage()
    message = request_modifiers.SetFieldFromRelativeName('string1')(
        ref, None, message)
    self.assertEqual('projects/p/zones/z/instances/i', message.string1)


if __name__ == '__main__':
  sdk_test_base.main()
