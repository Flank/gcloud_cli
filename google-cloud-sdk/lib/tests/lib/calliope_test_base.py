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

"""Helper class for loading test CLIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.core import module_util
from tests.lib import cli_test_base


def _GetPrivateModulePath(module_path):
  """Changes a testing sdk module prefix to normal googlecloudsdk prefix.

  This is a testing mock for module_util._GetPrivateModulePath(). In the test
  environments some modules, especially those in a test sdk[0-9]+, have a
  private module path (starts with '__'), but if they were in the real sdk
  would have a googlecloudsdk relative module path. This mock transforms
  private test module paths to googlecloudsdk relative module paths.

  Args:
    module_path: A private module path in module_util.GetModulePath()

  Returns:
    A googlecloudsdk relative module path for a test private module path.
  """
  prefix = '.gcloud.'  # Currently sufficient, could change with new test env.
  i = module_path.find(prefix)
  if i < 0:
    return None
  i += len(prefix)
  return 'googlecloudsdk.' + module_path[i:]


class CalliopeTestBase(cli_test_base.CliTestBase):
  """A base class for tests that load test CLIs.

  Attributes:
    test_data_dir: The directory that contains the calliope test CLIs.
  """

  def PreSetUp(self):
    self.test_data_dir = self.Resource('tests', 'unit', 'calliope', 'testdata')

  def SetUp(self):
    self.test_cli = None
    self.StartObjectPatch(
        module_util,
        '_GetPrivateModulePath',
        side_effect=_GetPrivateModulePath)

  def LoadTestCli(self, name, modules=None):
    """Loads the named test CLI.

    Args:
      name: The name of the calliope/tests/{name} test CLI.
      modules: [str], A list of additional modules to add to this CLI.

    Returns:
      The name test CLI object.
    """
    pkg_root = os.path.join(self.test_data_dir, name)
    loader = calliope.CLILoader(
        name='gcloud',
        command_root_directory=pkg_root,
        allow_non_existing_modules=True)
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.ALPHA,
                           os.path.join(pkg_root, 'alpha'), component='alpha')
    loader.AddReleaseTrack(calliope_base.ReleaseTrack.BETA,
                           os.path.join(pkg_root, 'beta'), component='beta')
    if modules:
      for m in modules:
        loader.AddModule(m, os.path.join(pkg_root, m))
    return loader.Generate()

  def WalkTestCli(self, name):
    """Loads the named test CLI and mocks the walker to use it.

    Args:
      name: The name of the calliope/tests/{name} test CLI.
    """
    if not self.test_cli:
      self.test_cli = self.LoadTestCli(name)
    self.StartPropertyPatch(
        calliope_base.Command, '_cli_power_users_only',
        return_value=self.test_cli)


def main():
  return cli_test_base.main()
