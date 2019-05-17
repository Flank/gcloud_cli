# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Tests for tests.unit.command_lib.iot.edge.flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.iot.edge import flags

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.edge import base


class FlagsTest(base.CloudIotEdgeBase, parameterized.TestCase):

  @parameterized.named_parameters(
      ('unnamed topic', 'input/topic', '', 'input/topic'),
      ('named topic', 'foo:input/topic', 'foo', 'input/topic'))
  def testTopicType(self, value, expected_id, expected_topic):
    actual_topic = flags.TopicType(value)
    self.assertEqual(expected_id, actual_topic.id)
    self.assertEqual(expected_topic, actual_topic.topic)

  def testTopicTypeFail(self):
    """Topic with colon(:) is not allowed."""
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      flags.TopicType('foo:input/topic:3')

  @parameterized.named_parameters(
      ('single full binding', '/tmp/workdir:/data:rw', '/tmp/workdir', '/data',
       False),
      ('single simple binding', '/tmp/workdir', '/tmp/workdir', '/tmp/workdir',
       False),
      ('readonly binding', '/mnt/sdcard:ro', '/mnt/sdcard', '/mnt/sdcard',
       True),
  )
  def testVolumeBindingType(self, value, expected_source, expected_destination,
                            expected_readonly):
    actual_binding = flags.VolumeBindingType(value)
    self.assertEqual(expected_source, actual_binding.source)
    self.assertEqual(expected_destination, actual_binding.destination)
    self.assertEqual(expected_readonly, actual_binding.readOnly)

  @parameterized.named_parameters(
      ('source is not absolute', 'workdir:/data:rw'),
      ('destination is not absolute', '/tmp/workdir:data:rw'),
      ('invalid readonly value', '/tmp/workdir:/data:rwm'),
      ('colon in path', '/tmp/w:rkdir:/data:rw'),
  )
  def testVolumeBindingTypeFail(self, value):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      flags.VolumeBindingType(value)

  @parameterized.named_parameters(
      ('single full binding', '/dev/video1:/dev/video0:rw', '/dev/video1',
       '/dev/video0', 'rw'),
      ('single simple binding', '/dev/video0', '/dev/video0', '/dev/video0',
       'rwm'),
      ('binding with cgroup', '/dev/video0:r', '/dev/video0', '/dev/video0',
       'r'),
  )
  def testDeviceBindingType(self, value, expected_source, expected_destination,
                            expected_cgroup):
    actual_binding = flags.DeviceBindingType(value)
    self.assertEqual(expected_source, actual_binding.source)
    self.assertEqual(expected_destination, actual_binding.destination)
    self.assertEqual(expected_cgroup, actual_binding.cgroupPermissions)

  @parameterized.named_parameters(
      ('source is not absolute', 'video0:/dev/video0:rw'),
      ('destination is not absolute', '/dev/video0:video0:rw'),
      ('invalid cgroup value', '/dev/video0:rwx'),
      ('colon in path', '/dev/video1:/dev/video0:foo:rw'),
  )
  def testDeviceBindingTypeFail(self, value):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      flags.DeviceBindingType(value)

  @parameterized.named_parameters(
      ('base case', 'MY_ENV_VAR'),
      ('complex case', '_numb3rs'),
  )
  def testEnvVarKeyType(self, key):
    actual_key = flags.EnvVarKeyType(key)
    self.assertEqual(actual_key, key)

  @parameterized.named_parameters(
      ('leading digit', '3hands'),
      ('non-alphanumeric character', 'ENV!VAR'),
      ('starting with X_GOOGLE_', 'X_GOOGLE_MY_VAR')
  )
  def testEnvVarKeyTypeFail(self, key):
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      flags.EnvVarKeyType(key)

if __name__ == '__main__':
  test_case.main()
