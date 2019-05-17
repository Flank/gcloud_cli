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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import command_loading
from tests.lib import sdk_test_base
from tests.lib import test_case


def _FromModule(mod_file, module_attributes, release_track, is_command):
  implementations = command_loading._ImplementationsFromModule(
      mod_file, module_attributes, is_command)
  return command_loading._ExtractReleaseTrackImplementation(
      mod_file, release_track, implementations)()


def _FromYaml(impl_file, path, data, release_track,
              yaml_command_translator):
  implementations = command_loading._ImplementationsFromYaml(
      path, data, yaml_command_translator)
  return command_loading._ExtractReleaseTrackImplementation(
      impl_file, release_track, implementations)()


class BaseTest(sdk_test_base.SdkBase):
  """Test the command and group blase class in calliope."""

  FORMAT_ALPHA = 'alpha'
  FORMAT_BETA = 'beta'
  FORMAT = 'ga'

  class NoTracks(calliope_base.Group):
    pass

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
  class GA(calliope_base.Group):
    pass

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
  class GACommand(calliope_base.Command):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
  class Alpha(calliope_base.Group):
    pass

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
  class AlphaCommand(calliope_base.Command):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.BETA)
  class Beta(calliope_base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA,
                               calliope_base.ReleaseTrack.BETA)
  class AlphaBeta(calliope_base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  @calliope_base.ReleaseTracks(*calliope_base.ReleaseTrack.AllValues())
  class All(calliope_base.Group):

    def __init__(self):
      pass

    def Run(self):
      return self.GetTrackedAttribute(BaseTest, 'FORMAT')

  def testEmpty(self):
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'No commands defined in file: \[file\]'):
      _FromModule('file', [], calliope_base.ReleaseTrack.GA, is_command=True)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'No command groups defined in file: \[file\]'):
      _FromModule('file', [], calliope_base.ReleaseTrack.GA, is_command=False)

  def testMultipleDefs(self):
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[ALPHA\] for element: '
        r'\[file\]'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.AlphaBeta],
          calliope_base.ReleaseTrack.GA, is_command=False)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[.+, .+\] for element: '
        r'\[file\]'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.Beta, BaseTest.AlphaBeta],
          calliope_base.ReleaseTrack.GA, is_command=False)
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple implementations defined for element: \[file\]. Each must '
        r'explicitly declare valid release tracks.'):
      _FromModule(
          'file', [BaseTest.Alpha, BaseTest.NoTracks],
          calliope_base.ReleaseTrack.GA, is_command=False)

  def testGroup(self):
    items = [calliope_base.Group]
    # A single group can be found.
    self.assertEqual(
        calliope_base.Group,
        _FromModule(
            'file', items, calliope_base.ReleaseTrack.GA, is_command=False))
    # Allow a group to not define tracks and still work.
    self.assertEqual(
        calliope_base.Group,
        _FromModule(
            'file', items, calliope_base.ReleaseTrack.ALPHA, is_command=False))
    # A group is registered but there should be a command.
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'You cannot define groups \[Group\] in a command file: \[file\]'):
      _FromModule(
          'file', items, calliope_base.ReleaseTrack.GA, is_command=True)
    # No matches for the release track.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GA],
          calliope_base.ReleaseTrack.ALPHA,
          is_command=False)
    # Explicitly tracked group can be found.
    self.assertEqual(
        BaseTest.GA,
        _FromModule(
            'file', [BaseTest.GA],
            calliope_base.ReleaseTrack.GA,
            is_command=False))
    # Make sure we pick the right one.
    self.assertEqual(
        BaseTest.GA,
        _FromModule(
            'file', [BaseTest.GA, BaseTest.Alpha],
            calliope_base.ReleaseTrack.GA,
            is_command=False))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GA, BaseTest.Alpha],
          calliope_base.ReleaseTrack.BETA,
          is_command=False)

  def testCommand(self):
    items = [calliope_base.Command]
    # A single command can be found.
    self.assertEqual(
        calliope_base.Command,
        _FromModule(
            'file', items, calliope_base.ReleaseTrack.GA, is_command=True))
    # Allow a command to not define tracks and still work.
    self.assertEqual(
        calliope_base.Command,
        _FromModule(
            'file', items, calliope_base.ReleaseTrack.ALPHA, is_command=True))
    # A command is registered but there should be a group.
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'You cannot define commands \[Command\] in a command group file: '
        r'\[file\]'):
      _FromModule(
          'file', items, calliope_base.ReleaseTrack.GA, is_command=False)
    # No matches for the release track.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand], calliope_base.ReleaseTrack.ALPHA,
          is_command=True)
    # Explicitly tracked command can be found.
    self.assertEqual(
        BaseTest.GACommand,
        _FromModule('file', [BaseTest.GACommand], calliope_base.ReleaseTrack.GA,
                    is_command=True))
    # Make sure we pick the right one.
    self.assertEqual(
        BaseTest.GACommand,
        _FromModule(
            'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
            calliope_base.ReleaseTrack.GA, is_command=True))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
          calliope_base.ReleaseTrack.BETA, is_command=True)

  def testGetTrackedAttribute(self):
    self.assertEqual(BaseTest.FORMAT, BaseTest.GACommand().Run())
    self.assertEqual(BaseTest.FORMAT_ALPHA, BaseTest.AlphaCommand().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.Beta().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.AlphaBeta().Run())
    self.assertEqual(BaseTest.FORMAT_BETA, BaseTest.All().Run())


class YamlTests(sdk_test_base.SdkBase):

  def testNoTranslator(self):
    with self.assertRaisesRegex(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: No yaml command translator has been '
        r'registered.'):
      _FromYaml(
          'file', ['foo', 'bar'], [], calliope_base.ReleaseTrack.GA, None)

  def testNoGroups(self):
    with self.assertRaisesRegex(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: Command groups cannot be implemented in '
        r'yaml.'):
      command_loading.LoadCommonType(
          ['dir/foo/bar.yaml'], ['foo', 'bar'], calliope_base.ReleaseTrack.GA,
          'id', is_command=False)
    with self.assertRaisesRegex(
        command_loading.CommandLoadFailure,
        r'Problem loading foo.bar: Command groups cannot be implemented in '
        r'yaml.'):
      command_loading.FindSubElements(
          ['dir/foo/bar.py', 'dir/foo/bar.yaml'],
          ['foo', 'bar'])

  def testNoMatchingTrack(self):
    with self.assertRaisesRegex(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'], [], calliope_base.ReleaseTrack.GA, object())
    with self.assertRaisesRegex(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'], [{'release_tracks': ['ALPHA']}],
          calliope_base.ReleaseTrack.GA, object())
    with self.assertRaisesRegex(
        command_loading.ReleaseTrackNotImplementedException,
        r'No implementation for release track \[GA\] for element: \[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['BETA']}],
          calliope_base.ReleaseTrack.GA, object())

  def testMultipleDefs(self):
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[ALPHA\] for element: '
        r'\[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['ALPHA']}],
          calliope_base.ReleaseTrack.ALPHA, object())
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple definitions for release tracks \[.+] for element: '
        r'\[file\]'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {'release_tracks': ['BETA']},
           {'release_tracks': ['ALPHA', 'BETA']}],
          calliope_base.ReleaseTrack.ALPHA, object())
    with self.assertRaisesRegex(
        command_loading.LayoutException,
        r'Multiple implementations defined for element: \[file\]. Each must '
        r'explicitly declare valid release tracks.'):
      _FromYaml(
          'file', ['foo', 'bar'],
          [{'release_tracks': ['ALPHA']}, {},],
          calliope_base.ReleaseTrack.ALPHA, object())

  def testCommand(self):
    # A stub translator.
    sentinel = object()

    class Translator(command_loading.YamlCommandTranslator):

      def Translate(self, path, command_data):
        return sentinel, command_data.get('release_tracks')

    t = Translator()

    # A single command can be found.
    self.assertEqual(
        (sentinel, None),
        _FromYaml(
            'file', ['foo', 'bar'], [{}], calliope_base.ReleaseTrack.GA, t))
    # Explicitly tracked command can be found.
    self.assertEqual(
        (sentinel, ['GA']),
        _FromYaml(
            'file', ['foo', 'bar'], [{'release_tracks': ['GA']}],
            calliope_base.ReleaseTrack.GA, t))
    # Make sure we pick the right one.
    self.assertEqual(
        (sentinel, ['GA']),
        _FromYaml(
            'file', ['foo', 'bar'],
            [{'release_tracks': ['GA']}, {'release_tracks': ['ALPHA']}],
            calliope_base.ReleaseTrack.GA, t))
    # No matches with multiple choices.
    with self.assertRaises(command_loading.ReleaseTrackNotImplementedException):
      _FromModule(
          'file', [BaseTest.GACommand, BaseTest.AlphaCommand],
          calliope_base.ReleaseTrack.BETA, is_command=True)

    # Check loading from file.
    self.Touch(self.temp_path, 'bar.yaml', """
- release_tracks: [GA, BETA]
- release_tracks: [ALPHA]""")
    self.assertEqual(
        (sentinel, ['GA']),
        command_loading.LoadCommonType(
            [os.path.join(self.temp_path, 'bar.yaml')], ['bar'],
            calliope_base.ReleaseTrack.GA, 'id', is_command=True,
            yaml_command_translator=t))


if __name__ == '__main__':
  test_case.main()
