# -*- coding: utf-8 -*- #
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
"""Tests for googlecloudsdk.api_lib.emulators.config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import tempfile

from googlecloudsdk.command_lib.emulators import config
from googlecloudsdk.command_lib.emulators import util
from tests.lib import test_case


class TestEmulatorA(util.Emulator):

  def Start(self, port):
    pass

  @property
  def prefixes(self):
    return [
        'google.a.v1.Kick',
        'google.a.v1.Punch',
        'google.a.v1.Its',
        'google.a.v1.All',
    ]

  @property
  def service_name(self):
    return 'test1'

  @property
  def emulator_title(self):
    return 'test1'

  @property
  def emulator_component(self):
    return 'test1-emulator'


class TestEmulatorB(util.Emulator):

  def Start(self, port):
    pass

  @property
  def prefixes(self):
    return [
        'google.b.v1.In',
        'google.b.v1.The',
        'google.b.v1.Mind',
    ]

  @property
  def service_name(self):
    return 'test2'

  @property
  def emulator_title(self):
    return 'test2'

  @property
  def emulator_component(self):
    return 'test2-emulator'


class ConfigTest(test_case.TestCase):

  def testWriteRoutesConfig(self):
    emulator_a = TestEmulatorA()
    emulator_b = TestEmulatorB()
    emulators = {}
    for e in [emulator_a, emulator_b]:
      emulators[e.service_name] = e

    _, tmp = tempfile.mkstemp()

    config.WriteRoutesConfig(emulators, tmp)

    with open(tmp) as f:
      data = json.load(f)

    self.assertEqual(emulator_a.prefixes, data.get(emulator_a.service_name))
    self.assertEqual(emulator_b.prefixes, data.get(emulator_b.service_name))

  def testWriteJsonToFile(self):
    for conf in [config.ProxyConfiguration({'ni': 1, 'hao': 2}, True, 1234),
                 config.ProxyConfiguration({'ma': 3}, False, 2345)]:
      _, tmp = tempfile.mkstemp()
      conf.WriteJsonToFile(tmp)
      with open(tmp) as f:
        data = json.load(f)
      self.assertEqual(conf._local_emulators, data.get('localEmulators'))
      self.assertEqual(conf._proxy_port, data.get('proxyPort'))
      self.assertEqual(conf._should_proxy_to_gcp, data.get('shouldProxyToGcp'))


if __name__ == '__main__':
  test_case.main()
