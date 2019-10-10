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

"""Tests for the command_lib.util.completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.command_lib.util import completers
from tests.lib import completer_test_base
from tests.lib import completer_test_completers as test_completers
from tests.lib import completer_test_data
from tests.lib import test_case


class CompletersTest(completer_test_base.CompleterBase):

  def testPseudoCollectionName(self):
    self.assertEqual('cloud.sdk.foo', completers.PseudoCollectionName('foo'))

  def testListCommandCompleter(self):
    completer = self.Completer(
        test_completers.ListCommandCompleter,
        command_resources={
            'compute.instances.list': completer_test_data.INSTANCE_URIS,
        })
    self.assertEqual(
        ['my_c_instance'] * 76,
        completer.Complete('my_c', self.parameter_info))

  def testListCommandCompleterGoodApiVersion(self):
    completer = self.Completer(
        test_completers.ListCommandCompleterGoodApiVersion,
        command_resources={
            'compute.instances.list': completer_test_data.INSTANCE_URIS,
        })
    self.assertEqual(
        ['my_c_instance'] * 76,
        completer.Complete('my_c', self.parameter_info))

  def testListCommandCompleterBadApiVersion(self):
    with self.assertRaises(apis_util.UnknownVersionError):
      self.Completer(
          test_completers.ListCommandCompleterBadApiVersion,
          command_resources={
              'compute.instances.list': completer_test_data.INSTANCE_URIS,
          })

  def testResourceParamCompleter(self):
    completer = self.Completer(test_completers.ResourceParamCompleter)
    self.assertEqual(
        completer_test_data.ZONE_NAMES,
        completer.Complete('', self.parameter_info))

  def testResourceSearchCompleter(self):
    completer = self.Completer(
        test_completers.ResourceSearchCompleter,
        search_resources={
            'compute.instances': completer_test_data.INSTANCE_URIS,
        })
    self.assertEqual(
        ['my_a_instance'] * 76,
        completer.Complete('my_a', self.parameter_info))

  def testMultiResourceCompleter(self):
    completer = self.Completer(test_completers.MultiResourceCompleter)
    self.assertEqual(
        sorted(
            completer_test_data.REGION_NAMES + completer_test_data.ZONE_NAMES),
        completer.Complete('', self.parameter_info))

  def testNoCacheCompleter(self):
    completer = self.Completer(test_completers.NoCacheCompleter, cache=False)
    self.assertEqual(
        ['role/major', 'role/minor'],
        completer.Complete('', self.parameter_info))


if __name__ == '__main__':
  test_case.main()
