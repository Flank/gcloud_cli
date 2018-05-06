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
"""Test of --configuration handling in nested command invocations."""

from __future__ import absolute_import
from __future__ import unicode_literals
import os

from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


class ConfigFlagTest(sdk_test_base.WithOutputCapture,
                     sdk_test_base.SdkBase):

  def SetUp(self):
    # Set up calliope to load the sdk5 test cli
    test_data_dir = self.Resource('tests', 'unit', 'calliope', 'testdata')
    pkg_root = os.path.join(test_data_dir, 'sdk5')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    self.cli = loader.Generate()

    self.named_config_dir = os.path.join(self.global_config_path,
                                         'configurations')

  def WriteTraceEmailToConfig(self, config_name, trace_email):
    files.MakeDir(self.named_config_dir)
    fname = os.path.join(self.named_config_dir,
                         'config_{0}'.format(config_name))

    with open(fname, 'w') as f:
      f.write('[core]\n'
              'trace_email = {0}\n'.format(trace_email))

  def testNestedFlagInterpretation(self):
    self.WriteTraceEmailToConfig('foo', 'foo-email')
    self.WriteTraceEmailToConfig('bar', 'bar-email')
    self.WriteTraceEmailToConfig('baz', 'baz-email')

    self.cli.Execute(['command', '--recurse',
                      '--print-trace-email-during-parse', '--configuration',
                      'foo'])
    self.AssertErrMatches(r'.*trace_email = foo-email\n'
                          r'.*trace_email = bar-email\n'
                          r'.*trace_email = None\n'
                          r'.*trace_email = baz-email')

  def testMultipleFlagInterpretation(self):
    self.WriteTraceEmailToConfig('foo', 'foo-email')
    self.WriteTraceEmailToConfig('bar', 'bar-email')
    self.cli.Execute(['command', '--print-trace-email-during-parse',
                      '--configuration', 'foo',
                      '--configuration', 'bar'])
    self.AssertErrMatches(r'.*trace_email = bar-email\n')
    self.AssertErrNotContains('foo-email')

  def testFlagInterpretationAsTwoArgs(self):
    self.WriteTraceEmailToConfig('foo', 'foo-email')
    self.cli.Execute(['command', '--print-trace-email-during-parse',
                      '--configuration', 'foo'])
    self.AssertErrContains('foo-email')

  def testFlagInterpretationWithEqualSign(self):
    self.WriteTraceEmailToConfig('foo', 'foo-email')
    self.cli.Execute(['command', '--print-trace-email-during-parse',
                      '--configuration=foo'])
    self.AssertErrContains('foo-email')


if __name__ == '__main__':
  test_case.main()
