# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Test for coverage tree generation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.flag_coverage import generate
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base


class GenerateTest(calliope_test_base.CalliopeTestBase):

  def testGenerateTree(self):
    cli_dir = os.path.join(self.temp_path, 'data', 'cli')
    files.MakeDir(cli_dir)
    self.WalkTestCli('sdk13')
    with files.FileWriter(os.path.join(cli_dir, 'gcloud_coverage.py')) as f:
      self.root = generate.OutputCoverageTree(cli=self.test_cli, out=f)
    self.assertEqual(
        self.root['sdk'],
        {
            '--yes': True,
            '--no': False,
            'group': self.root['sdk']['group'],
            'require-coverage': self.root['sdk']['require-coverage']
        })
    self.assertTrue(self.root['--help'])
    self.assertEqual(
        self.root['sdk']['require-coverage'],
        {
            '--needs_coverage': True,
            '--also_needs_coverage': True
        })
    self.assertEqual(
        self.root['sdk']['group']['do-not-require-coverage'],
        {
            '--no_include': False,
            '--sort-by': False,
            '--filter': False,
            '--limit': False,
            '--page-size': False,
            '--uri': False,
        })


if __name__ == '__main__':
  calliope_test_base.main()
