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
"""Various test utilities for calliope."""

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import log
from tests.lib import sdk_test_base

import mock


class Base(sdk_test_base.WithOutputCapture,
           sdk_test_base.SdkBase):
  """Base class for calliope tests."""

  def SetUp(self):
    self.calliope_test_home = self.Resource(
        'tests', 'unit', 'calliope', 'testdata')
    self.logs_dir = self.CreateTempDir()

  def GetCLI(self, force_init=True):
    """Loads the test commands with a temporary logging directory.

    Args:
      force_init: bool, True to completely reset the logger, False to add a new
        handler.

    Returns:
      calliope.CLI, The CLI object.
    """
    log.Reset()
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'),
        logs_dir=self.logs_dir)
    loader.AddModule('sdk2', os.path.join(self.calliope_test_home, 'sdk2'))
    return loader.Generate()

  def InitLogging(self, logs_dir=None):
    """Initialize the logger for testing.

    Args:
      logs_dir: str, The root directory to write logs to.  If None, use the
        standard one.
    """
    log.Reset()
    log.AddFileLogging(logs_dir or self.logs_dir)

  def GetLogFileContents(self, logs_dir=None):
    """Makes sure a single log file was created and gets its contents.

    Args:
      logs_dir: str, The path to the root log directory.  If None, use the
        standard one.

    Raises:
      ValueError: If more than one log directory or file is found.

    Returns:
      str, The contents of the log file.
    """
    logs_dir = logs_dir or self.logs_dir
    sub_dirs = os.listdir(logs_dir)
    if len(sub_dirs) != 1:
      raise ValueError('Found more than one log directory')
    sub_dir = os.path.join(logs_dir, sub_dirs[0])
    log_files = os.listdir(sub_dir)
    if len(log_files) != 1:
      raise ValueError('Found more than one log file')
    contents = open(os.path.join(sub_dir, log_files[0])).read()
    return contents


class WithTestTool(Base):
  """A base test class for calliope with the command loader set up."""

  def SetUp(self):
    self.known_error_handler = mock.MagicMock()
    self._loader = calliope.CLILoader(
        name='test',
        command_root_directory=os.path.join(self.calliope_test_home, 'sdk1'),
        allow_non_existing_modules=True,
        known_error_handler=self.known_error_handler)
    self._loader.AddModule('sdk2', os.path.join(self.calliope_test_home,
                                                'sdk2'))
    self._loader.AddModule('sdk3', os.path.join(self.calliope_test_home,
                                                'nested_sdk', 'sdk1'))
    self._loader.AddModule('sdk7', os.path.join(self.calliope_test_home,
                                                'sdk7'))
    self._loader.AddModule('sdk11', os.path.join(self.calliope_test_home,
                                                 'sdk11'))
    self._loader.AddModule('broken_sdk', os.path.join(self.calliope_test_home,
                                                      'broken_sdk'))
    self._loader.AddModule(
        'does-not-exist',
        os.path.join(self.calliope_test_home, 'does_not_exist'),
        component='does_not_exist')
    self._loader.AddReleaseTrack(
        calliope_base.ReleaseTrack.ALPHA,
        os.path.join(self.calliope_test_home, 'track_does_not_exist'))

    # This breaks a lot and is obviously wrong. I don't understand
    # tracks/modules enough to handle this better.
    self._loader.AddReleaseTrack(
        calliope_base.ReleaseTrack.BETA,
        # sdk2 is an arbitrary valid subdirectory. Binding BETA to the root
        # caused flag collisions.
        os.path.join(self.calliope_test_home, 'sdk2'))

    self.cli = self._loader.Generate()

  def HelpFunc(self, command):
    return '.'.join(command)


class MockCliGenerator(object):

  def ComponentsForMissingCommand(self, command_path):
    del command_path
    return []

  def ReplicateCommandPathForAllOtherTracks(self, command_path):
    del command_path
    return []


class MockCommand(object):
  """A mock base.Command that enables add_argument() and parse_args().

  Attributes:
    ai: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor, the parser
      for the command. Can be used to create a custom parser for the command in
      the calling test.
  """

  def __init__(self, name):
    """Initializes the mock command.

    Args:
      name: str, the name of the command.
    """
    self._name = name
    self.ai = None
    self._cli_generator = MockCliGenerator()

  def GetAllAvailableFlags(self):
    return self.ai.flag_args + self.ai.ancestor_flag_args

  def GetPath(self):
    return [self._name]

  def GetUsage(self):
    return 'Usage: ...'


def ArgumentParser(cli_name='test'):
  """Gets a calliope argument parser with all intercepts in place."""
  command = MockCommand(cli_name)
  wrapped_parser = parser_extensions.ArgumentParser(calliope_command=command)
  parser = parser_arguments.ArgumentInterceptor(
      parser=wrapped_parser,
      cli_generator=None,
      allow_positional=True)
  command.ai = parser
  parser.parse_args = wrapped_parser.parse_args  # For test use only.
  return parser
