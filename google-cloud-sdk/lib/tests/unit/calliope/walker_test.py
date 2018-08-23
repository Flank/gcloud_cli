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
"""Tests for the CLI tree walker."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import os

from googlecloudsdk.calliope import cli as calliope
from googlecloudsdk.calliope import walker
from tests.lib import sdk_test_base
from tests.lib import test_case


class WalkerTest(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    test_data_dir = self.Resource('tests', 'unit', 'calliope', 'testdata')
    pkg_root = os.path.join(test_data_dir, 'sdk1')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    self.cli = loader.Generate()

  def testWalkerAll(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli).Walk())
    self.AssertOutputContains("""\
node=test parent=None is_group=True
node=cfg parent=test is_group=True
node=get parent=cfg is_group=False
node=set parent=cfg is_group=False
node=set2 parent=cfg is_group=False
node=command1 parent=test is_group=False
node=compound_group parent=test is_group=True
node=compound_command parent=compound_group is_group=False
node=dict_list parent=test is_group=False
node=exceptioncommand parent=test is_group=False
node=exit2 parent=test is_group=False
node=help parent=test is_group=False
node=implementation_args parent=test is_group=False
node=loggingcommand parent=test is_group=False
node=mutex_command parent=test is_group=False
node=newstylecommand parent=test is_group=False
node=newstylegroup parent=test is_group=True
node=anothergroup parent=newstylegroup is_group=True
node=subcommand parent=anothergroup is_group=False
node=subcommand parent=newstylegroup is_group=False
node=recommand parent=test is_group=False
node=requiredargcommand parent=test is_group=False
node=simple_command parent=test is_group=False
node=unsetprop parent=test is_group=False
top=test
""")

  def testWalkerRestrictMatch(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli).Walk(restrict=['test.cfg']))
    self.AssertOutputContains("""\
node=test parent=None is_group=True
node=cfg parent=test is_group=True
node=get parent=cfg is_group=False
node=set parent=cfg is_group=False
node=set2 parent=cfg is_group=False
top=test
""")

  def testWalkerRestrictTreeLoadMatch(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli, restrict=['test.cfg']).Walk())
    self.AssertOutputContains("""\
node=cfg parent=None is_group=True
node=get parent=cfg is_group=False
node=set parent=cfg is_group=False
node=set2 parent=cfg is_group=False
top=cfg
""")

  def testWalkerRestrictNoMatch(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli).Walk(restrict=['notfound']))
    self.AssertOutputContains("""\
node=test parent=None is_group=True
top=test
""")


class WalkerHiddenTest(sdk_test_base.WithOutputCapture, sdk_test_base.SdkBase):

  def SetUp(self):
    test_data_dir = self.Resource('tests', 'unit', 'calliope', 'testdata')
    pkg_root = os.path.join(test_data_dir, 'sdk4')
    loader = calliope.CLILoader(
        name='test',
        command_root_directory=pkg_root)
    self.cli = loader.Generate()

  def testWalkerHiddenFalse(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli).Walk())
    self.AssertOutputContains("""\
node=test parent=None is_group=True
node=internal parent=test is_group=True
node=internal_command parent=internal is_group=False
node=sdk parent=test is_group=True
node=ordered_choices parent=sdk is_group=False
node=second_level_command_1 parent=sdk is_group=False
node=second_level_command_b parent=sdk is_group=False
node=subgroup parent=sdk is_group=True
node=subgroup_command_2 parent=subgroup is_group=False
node=subgroup_command_a parent=subgroup is_group=False
node=xyzzy parent=sdk is_group=False
node=version parent=test is_group=False
top=test
""")

  def testWalkerHiddenTrue(self):
    class VisitGenerator(walker.Walker):

      def Visit(self, node, parent, is_group):
        print('node=%s parent=%s is_group=%s' % (node.name, parent, is_group))
        return node.name

    print('top=%s' % VisitGenerator(self.cli).Walk(hidden=True))
    self.AssertOutputContains("""\
node=test parent=None is_group=True
node=internal parent=test is_group=True
node=internal_command parent=internal is_group=False
node=sdk parent=test is_group=True
node=hidden_command parent=sdk is_group=False
node=hiddengroup parent=sdk is_group=True
node=hidden_command_2 parent=hiddengroup is_group=False
node=hidden_command_a parent=hiddengroup is_group=False
node=ordered_choices parent=sdk is_group=False
node=second_level_command_1 parent=sdk is_group=False
node=second_level_command_b parent=sdk is_group=False
node=subgroup parent=sdk is_group=True
node=subgroup_command_2 parent=subgroup is_group=False
node=subgroup_command_a parent=subgroup is_group=False
node=xyzzy parent=sdk is_group=False
node=version parent=test is_group=False
top=test
""")


if __name__ == '__main__':
  test_case.main()
