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

"""Tests for the scenario test_base."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import unittest

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from tests.lib import e2e_utils
from tests.lib import parameterized
from tests.lib.scenario import assertions
from tests.lib.scenario import session
from tests.lib.scenario import test_base

import six


class TestBaseTests(test_base.ScenarioTestBase, parameterized.TestCase):

  def SetUp(self):
    self.run_mock = self.StartObjectPatch(self.cli, 'Execute')
    def FakeNameGenerator(*args, **kwargs):
      del args
      yield kwargs['prefix'] + '-FAKE'
    self.StartObjectPatch(e2e_utils, 'GetResourceNameGenerator',
                          side_effect=FakeNameGenerator)
    data = """\
title: my scenario
release_tracks: [ALPHA, BETA]
actions:
  - set_property:
      core/project: myproj
  - write_file:
      path: foo/bar/baz.txt
      contents: asdf
  - write_file:
      path: a/b/c.txt
      binary_contents: qwerty
  - load_resource:
      path: tests/unit/tests_lib/scenario/test_data/data.txt
  - load_resource:
      path: tests/unit/tests_lib/scenario/test_data/subdir
  - generate_resource_id:
      reference: my-registry
      prefix: iot-registry
  - execute_command:
      command: iot registries create $$my-registry$$ --region us-central1
      events:
      - expect_exit:
          code: 0
  - generate_resource_id:
      reference: my-device
      prefix: iot-device
  - execute_command:
      command: iot devices create $$my-device$$ --registry $$my-registry$$ --region us-central1
      events:
      - expect_exit:
          code: 0
  - execute_command:
      command: iot devices delete $$my-device$$ --registry $$my-registry$$ --region us-central1
      cleanup_for: my-device
      events:
      - expect_exit:
          code: 0
  - set_property:
      core/project: otherproj
  - execute_command:
      command: iot registries describe $$my-registry$$ --region us-central1
      events:
      - expect_exit:
          code: 0
  - set_property:
      core/project: otherotherproj
  - execute_command:
      command: iot registries delete $$my-registry$$ --region us-central1
      cleanup_for: my-registry
      events:
      - expect_exit:
          code: 0
    """
    self.spec_path = self.Touch(self.temp_path, contents=data)

  def _Check(self, data):
    def _Inner(command):
      expected_command, props, error = data.pop(0)
      self.assertEqual(expected_command, command)
      for p, v in six.iteritems(props):
        self.assertEqual(v, properties.FromString(p).Get())
      if error:
        calliope_exceptions._Exit(error)
    return _Inner

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', calliope_base.ReleaseTrack.BETA),
  )
  def testScenario(self, track):
    check_data = [
        ([track.prefix, 'iot', 'registries', 'create', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'devices', 'create', 'iot-device-FAKE',
          '--registry', 'iot-registry-FAKE', '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'devices', 'delete', 'iot-device-FAKE',
          '--registry', 'iot-registry-FAKE', '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'registries', 'describe', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'otherproj'},
         None),

        ([track.prefix, 'iot', 'registries', 'delete', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'otherotherproj'},
         None),
    ]
    self.run_mock.side_effect = self._Check(check_data)
    self.RunScenario(self.spec_path, track, session.ExecutionMode.LOCAL, [])
    self.assertEquals(5, len(self.run_mock.mock_calls))
    self.AssertFileEquals('asdf', 'foo/bar/baz.txt')
    self.AssertBinaryFileEquals(b'qwerty', 'a/b/c.txt')
    self.AssertFileEquals('This is some data.\n', 'data.txt')
    self.AssertFileEquals('This is some nested data.\n',
                          'subdir/another/data.txt')
    self.assertEquals('otherotherproj', properties.VALUES.core.project.Get())

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', calliope_base.ReleaseTrack.BETA),
  )
  def testScenarioWithError(self, track):
    check_data = [
        ([track.prefix, 'iot', 'registries', 'create', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'myproj'},
         exceptions.Error()),
    ]
    self.run_mock.side_effect = self._Check(check_data)
    with self.assertRaises(assertions.Error):
      self.RunScenario(self.spec_path, track, session.ExecutionMode.LOCAL, [])
    # In local mode, when something fails, we just stop. No more actions are
    # executed.
    self.assertEquals(1, len(self.run_mock.mock_calls))
    self.assertEquals('myproj', properties.VALUES.core.project.Get())

  @parameterized.named_parameters(
      ('Alpha', calliope_base.ReleaseTrack.ALPHA),
      ('Beta', calliope_base.ReleaseTrack.BETA),
  )
  def testScenarioWithErrorAndCleanup(self, track):
    check_data = [
        ([track.prefix, 'iot', 'registries', 'create', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'devices', 'create', 'iot-device-FAKE',
          '--registry', 'iot-registry-FAKE', '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'devices', 'delete', 'iot-device-FAKE',
          '--registry', 'iot-registry-FAKE', '--region', 'us-central1'],
         {'core/project': 'myproj'},
         None),

        ([track.prefix, 'iot', 'registries', 'describe', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'otherproj'},
         exceptions.Error()),

        ([track.prefix, 'iot', 'registries', 'delete', 'iot-registry-FAKE',
          '--region', 'us-central1'],
         {'core/project': 'otherproj'},
         None),
    ]
    self.run_mock.side_effect = self._Check(check_data)
    with self.assertRaises(assertions.Error):
      self.RunScenario(self.spec_path, track, session.ExecutionMode.REMOTE, [])
    # In remote mode, when something fails, we continue but only execute actions
    # associated with the cleanup of resources that have not yet been deleted.
    self.assertEquals(5, len(self.run_mock.mock_calls))
    # We didn't run the rest of the set property actions.
    self.assertEquals('otherproj', properties.VALUES.core.project.Get())


class TestBaseSkipTests(test_base.ScenarioTestBase):

  def testSkip(self):
    data = """\
title: my scenario
release_tracks: [ALPHA, BETA]
skip:
  reason: skip this
  bug: b/12345
actions: []
"""
    spec_path = self.Touch(self.temp_path, contents=data)
    with self.assertRaisesRegex(unittest.SkipTest, r'skip this \(b/12345\)'):
      self.RunScenario(spec_path, calliope_base.ReleaseTrack.GA,
                       session.ExecutionMode.LOCAL, [])


if __name__ == '__main__':
  test_base.main()
