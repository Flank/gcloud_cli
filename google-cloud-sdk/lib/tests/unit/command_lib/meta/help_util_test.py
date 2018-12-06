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
"""Tests for help_util."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import shutil
import sys

from googlecloudsdk.calliope import walker_util
from googlecloudsdk.command_lib.meta import help_util
from googlecloudsdk.core.util import files as file_utils
from tests.lib import calliope_test_base
from tests.lib import parameterized
from six.moves import range


class HelpTextUtilTest(calliope_test_base.CalliopeTestBase,
                       parameterized.TestCase):

  def DiffCliHelpText(self, name_1, name_2, diff=None, dot=0):
    cli_1 = self.LoadTestCli(name_1)
    dir_1 = os.path.join(self.temp_path, 'help_1')
    walker_util.HelpTextGenerator(cli_1, dir_1).Walk(hidden=True)
    owners_1 = os.path.join(dir_1, 'OWNERS')
    with io.open(owners_1, 'wt'):
      pass

    cli_2 = self.LoadTestCli(name_2)
    dir_2 = os.path.join(self.temp_path, 'help_2')
    walker_util.HelpTextGenerator(cli_2, dir_2).Walk(hidden=True)

    if not diff:
      ret = None
    elif dot == 1:
      pwd = os.getcwd()
      os.chdir(dir_1)
      ret = help_util.DirDiff('.', dir_2, diff)
      os.chdir(pwd)
    elif dot == 2:
      pwd = os.getcwd()
      os.chdir(dir_2)
      ret = help_util.DirDiff(dir_1, '.', diff)
      os.chdir(pwd)
    else:
      ret = help_util.DirDiff(dir_1, dir_2, diff)

    return ret

  def testDirDiffCount(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

    diff = Accumulator()
    prune = self.DiffCliHelpText('sdk1', 'sdk2', diff)
    self.assertEqual(None, prune)
    self.assertEqual(52, diff.GetChanges())

  def testDirDiffOps(self):

    class Accumulator(help_util.DiffAccumulator):

      def __init__(self):
        self._changes = []

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

      def AddChange(self, op, relative_file, old_contents=None,
                    new_contents=None):
        if op == 'edit':
          self._changes.append('%s %s %s %s' % (op, relative_file,
                                                len(old_contents.splitlines()),
                                                len(new_contents.splitlines())))
        else:
          self._changes.append('%s %s' % (op, relative_file))
        return None

    diff = Accumulator()
    self.DiffCliHelpText('sdk1', 'sdk2', diff)
    sys.stdout.write('\n'.join(sorted(diff.GetChanges())) + '\n')
    expected = """\
add arg-groups
add bool-mutex
add combinations
add command2
add common-flags
add common-other-flags
add deprecated-args
add dynamic-args
add extra-args
add hidden
add list-command-flags
add lotsofargs/GROUP
add lotsofargs/test
add lotsofargs/test-flags
add lotsofargs/test-flags-args
add modal-group
add multiple-positional
add nested-groups
add ordered-choices
add other-flags
add remainder
add remainder-with-flags
add required-common-flags
add required-common-other-flags
add required-flags
add required-other-flags
add required-vs-optional
add suppressed-positional
delete cfg/GROUP
delete cfg/get
delete cfg/set
delete cfg/set2
delete command1
delete compound-group/GROUP
delete compound-group/compound-command
delete dict-list
delete exceptioncommand
delete exit2
delete help
delete implementation-args
delete loggingcommand
delete mutex-command
delete newstylecommand
delete newstylegroup/GROUP
delete newstylegroup/anothergroup/GROUP
delete newstylegroup/anothergroup/subcommand
delete newstylegroup/subcommand
delete recommand
delete simple-command
delete unsetprop
edit GROUP 105 143
edit requiredargcommand 15 18
"""
    self.AssertOutputEquals(expected.replace('/', os.path.sep))

  def testDirDiffSame(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

    diff = Accumulator()
    self.DiffCliHelpText('sdk1', 'sdk1', diff)
    self.assertEqual(0, diff.GetChanges())

  def testDirDiffSameDot1(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

      def AddChange(self, unused_op, unused_relative_file, old_contents=None,
                    new_contents=None):
        self._changes += 1
        return None

      def GetChanges(self):
        return self._changes

    diff = Accumulator()
    self.DiffCliHelpText('sdk1', 'sdk1', diff, dot=1)
    self.assertEqual(0, diff.GetChanges())

  def testDirDiffSameDot2(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

    diff = Accumulator()
    self.DiffCliHelpText('sdk1', 'sdk1', diff, dot=2)
    self.assertEqual(0, diff.GetChanges())

  def testDirDiffCountPrune(self):

    class Accumulator(help_util.DiffAccumulator):

      PRUNE = 10

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

      def AddChange(self, unused_op, unused_relative_file, old_contents=None,
                    new_contents=None):
        self._changes += 1
        return self._changes if self._changes >= self.PRUNE else None

    diff = Accumulator()
    prune = self.DiffCliHelpText('sdk1', 'sdk2', diff)
    self.assertEqual(diff.PRUNE, prune)
    self.assertEqual(diff.PRUNE, diff.GetChanges())

  def testDirDiffAddPrune(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

      def AddChange(self, op, unused_relative_file, old_contents=None,
                    new_contents=None):
        return True if op == 'add' else None

    diff = Accumulator()
    prune = self.DiffCliHelpText('sdk1', 'sdk2', diff)
    self.assertTrue(prune)

  def testDirDiffDeletePrune(self):

    class Accumulator(help_util.DiffAccumulator):

      def Ignore(self, relative_file):
        return help_util.Whitelisted(relative_file)

      def AddChange(self, op, unused_relative_file, old_contents=None,
                    new_contents=None):
        return True if op == 'delete' else None

    diff = Accumulator()
    prune = self.DiffCliHelpText('sdk1', 'sdk2', diff)
    self.assertTrue(prune)

  def testHelpTextValidate(self):

    bad_contents = [
        'This contains an invalid brand GCE abbreviation.\n',
        'This contains an invalid brand\tGCE abbreviation.\n',
        'This contains an invalid brand GCE\tabbreviation.\n',
        'This contains an invalid brand\tGCE\tabbreviation.\n',
        'This contains an invalid brand\nGCE abbreviation.\n',
        'This contains an invalid brand GCE\nabbreviation.\n',
        'This contains an invalid brand\nGCE\nabbreviation.\n',
        'This contains an invalid brand.GCE abbreviation.\n',
        'This contains an invalid brand GCE.abbreviation.\n',
        'This contains an invalid brand.GCE.abbreviation.\n',
    ]
    ok_contents = [
        'This does not contain an invalid brand_GCE abbreviation.\n',
        'This does not contain an invalid brand GCE_abbreviation.\n',
        'This does not contain an invalid brand_GCE_abbreviation.\n',
    ]

    class Accumulator(help_util.HelpAccumulator):

      def __init__(self):
        super(Accumulator, self).__init__()
        self._invalid_files = []
        self.contents = bad_contents + ok_contents

      def Validate(self, relative_file, contents):
        contents = self.contents.pop()
        if self._invalid_abbreviations.search(contents):
          self._invalid_files.append(relative_file)

      @property
      def invalid_files(self):
        return sorted(self._invalid_files)

    diff = Accumulator()
    for _ in range(len(bad_contents) + len(ok_contents)):
      diff.Validate('foo', 'This line has no abbreviations.')
    # Verify all contents consumed.
    self.assertEqual(0, len(diff.contents))
    self.assertEqual(len(bad_contents), len(diff.invalid_files))

  @parameterized.parameters(
      ('b', True),
      (os.path.join('b', 'c'), True),
      ('c', False),
      (os.path.join('c', 'd'), True),
      (os.path.join('c', 'd', 'e'), True),
      ('d', False),
      (os.path.join('d', 'e'), False),
  )
  def testIgnore(self, value, is_included):
    diff = help_util.HelpAccumulator(restrict=['a.b', 'a.c.d'])
    self.assertEqual(diff.Ignore(value), not is_included)


class ManPageUpdaterTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):

    self.cli = self.LoadTestCli('sdk4')
    self.help_dir = os.path.join(self.temp_path, 'help')
    shutil.rmtree(self.help_dir, ignore_errors=True)
    file_utils.MakeDir(self.help_dir)
    with io.open(os.path.join(self.help_dir, 'second-level-command-1.1'),
                 'wt') as f:
      f.write('This is old content that should be edited.\n')
    with io.open(os.path.join(self.help_dir, 'second-level-command-0.1'),
                 'wt') as f:
      f.write('This is old content that should be deleted.\n')

  def testUpdateManPage(self):

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.ManPageGenerator).Update()
    expected = """\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
add man1/gcloud.1
add man1/gcloud_alpha.1
add man1/gcloud_alpha_internal.1
add man1/gcloud_alpha_internal_internal-command.1
add man1/gcloud_alpha_sdk.1
add man1/gcloud_alpha_sdk_alphagroup.1
add man1/gcloud_alpha_sdk_hidden-command.1
add man1/gcloud_alpha_sdk_hiddengroup.1
add man1/gcloud_alpha_sdk_hiddengroup_hidden-command-2.1
add man1/gcloud_alpha_sdk_hiddengroup_hidden-command-a.1
add man1/gcloud_alpha_sdk_ordered-choices.1
add man1/gcloud_alpha_sdk_second-level-command-1.1
add man1/gcloud_alpha_sdk_second-level-command-b.1
add man1/gcloud_alpha_sdk_subgroup.1
add man1/gcloud_alpha_sdk_subgroup_subgroup-command-2.1
add man1/gcloud_alpha_sdk_subgroup_subgroup-command-a.1
add man1/gcloud_alpha_sdk_xyzzy.1
add man1/gcloud_alpha_version.1
add man1/gcloud_beta.1
add man1/gcloud_beta_internal.1
add man1/gcloud_beta_internal_internal-command.1
add man1/gcloud_beta_sdk.1
add man1/gcloud_beta_sdk_betagroup.1
add man1/gcloud_beta_sdk_betagroup_beta-command.1
add man1/gcloud_beta_sdk_betagroup_sub-command-2.1
add man1/gcloud_beta_sdk_betagroup_sub-command-a.1
add man1/gcloud_beta_sdk_hidden-command.1
add man1/gcloud_beta_sdk_hiddengroup.1
add man1/gcloud_beta_sdk_hiddengroup_hidden-command-2.1
add man1/gcloud_beta_sdk_hiddengroup_hidden-command-a.1
add man1/gcloud_beta_sdk_ordered-choices.1
add man1/gcloud_beta_sdk_second-level-command-1.1
add man1/gcloud_beta_sdk_second-level-command-b.1
add man1/gcloud_beta_sdk_subgroup.1
add man1/gcloud_beta_sdk_subgroup_subgroup-command-2.1
add man1/gcloud_beta_sdk_subgroup_subgroup-command-a.1
add man1/gcloud_beta_sdk_xyzzy.1
add man1/gcloud_beta_version.1
add man1/gcloud_internal.1
add man1/gcloud_internal_internal-command.1
add man1/gcloud_sdk.1
add man1/gcloud_sdk_hidden-command.1
add man1/gcloud_sdk_hiddengroup.1
add man1/gcloud_sdk_hiddengroup_hidden-command-2.1
add man1/gcloud_sdk_hiddengroup_hidden-command-a.1
add man1/gcloud_sdk_ordered-choices.1
add man1/gcloud_sdk_second-level-command-1.1
add man1/gcloud_sdk_second-level-command-b.1
add man1/gcloud_sdk_subgroup.1
add man1/gcloud_sdk_subgroup_subgroup-command-2.1
add man1/gcloud_sdk_subgroup_subgroup-command-a.1
add man1/gcloud_sdk_xyzzy.1
add man1/gcloud_version.1
delete second-level-command-0.1
delete second-level-command-1.1
"""
    self.assertEqual(55, changes)
    self.AssertErrEquals(expected.replace('/', os.path.sep))
    self.ClearErr()

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.ManPageGenerator).Update()
    self.assertEqual(0, changes)
    self.AssertErrEquals("""\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
""")


class HtmlUpdaterTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):

    self.cli = self.LoadTestCli('sdk4')
    self.help_dir = os.path.join(self.temp_path, 'help')
    shutil.rmtree(self.help_dir, ignore_errors=True)
    file_utils.MakeDir(self.help_dir)
    with io.open(os.path.join(self.help_dir, 'second-level-command-1.html'),
                 'wt') as f:
      f.write('This is old content that should be edited.\n')
    with io.open(os.path.join(self.help_dir, 'second-level-command-0.html'),
                 'wt') as f:
      f.write('This is old content that should be deleted.\n')

  def testUpdateHtml(self):

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.HtmlGenerator).Update()
    expected = """\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
add _menu_.css
add _menu_.html
add _menu_.js
add _title_.html
add favicon.ico
add gcloud.html
add gcloud_alpha.html
add gcloud_alpha_internal.html
add gcloud_alpha_internal_internal-command.html
add gcloud_alpha_sdk.html
add gcloud_alpha_sdk_alphagroup.html
add gcloud_alpha_sdk_hidden-command.html
add gcloud_alpha_sdk_hiddengroup.html
add gcloud_alpha_sdk_hiddengroup_hidden-command-2.html
add gcloud_alpha_sdk_hiddengroup_hidden-command-a.html
add gcloud_alpha_sdk_ordered-choices.html
add gcloud_alpha_sdk_second-level-command-1.html
add gcloud_alpha_sdk_second-level-command-b.html
add gcloud_alpha_sdk_subgroup.html
add gcloud_alpha_sdk_subgroup_subgroup-command-2.html
add gcloud_alpha_sdk_subgroup_subgroup-command-a.html
add gcloud_alpha_sdk_xyzzy.html
add gcloud_alpha_version.html
add gcloud_beta.html
add gcloud_beta_internal.html
add gcloud_beta_internal_internal-command.html
add gcloud_beta_sdk.html
add gcloud_beta_sdk_betagroup.html
add gcloud_beta_sdk_betagroup_beta-command.html
add gcloud_beta_sdk_betagroup_sub-command-2.html
add gcloud_beta_sdk_betagroup_sub-command-a.html
add gcloud_beta_sdk_hidden-command.html
add gcloud_beta_sdk_hiddengroup.html
add gcloud_beta_sdk_hiddengroup_hidden-command-2.html
add gcloud_beta_sdk_hiddengroup_hidden-command-a.html
add gcloud_beta_sdk_ordered-choices.html
add gcloud_beta_sdk_second-level-command-1.html
add gcloud_beta_sdk_second-level-command-b.html
add gcloud_beta_sdk_subgroup.html
add gcloud_beta_sdk_subgroup_subgroup-command-2.html
add gcloud_beta_sdk_subgroup_subgroup-command-a.html
add gcloud_beta_sdk_xyzzy.html
add gcloud_beta_version.html
add gcloud_internal.html
add gcloud_internal_internal-command.html
add gcloud_sdk.html
add gcloud_sdk_hidden-command.html
add gcloud_sdk_hiddengroup.html
add gcloud_sdk_hiddengroup_hidden-command-2.html
add gcloud_sdk_hiddengroup_hidden-command-a.html
add gcloud_sdk_ordered-choices.html
add gcloud_sdk_second-level-command-1.html
add gcloud_sdk_second-level-command-b.html
add gcloud_sdk_subgroup.html
add gcloud_sdk_subgroup_subgroup-command-2.html
add gcloud_sdk_subgroup_subgroup-command-a.html
add gcloud_sdk_xyzzy.html
add gcloud_version.html
add index.html
delete second-level-command-0.html
delete second-level-command-1.html
"""
    self.assertEqual(61, changes)
    self.AssertErrEquals(expected.replace('/', os.path.sep))
    self.ClearErr()

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.HtmlGenerator).Update()
    self.assertEqual(0, changes)
    self.AssertErrEquals("""\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
""")


class DevSiteUpdaterTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):

    self.cli = self.LoadTestCli('sdk4')
    self.help_dir = os.path.join(self.temp_path, 'help')
    shutil.rmtree(self.help_dir, ignore_errors=True)
    file_utils.MakeDir(self.help_dir)
    subdir = os.path.join(self.help_dir, 'sdk')
    file_utils.MakeDir(subdir)
    with io.open(os.path.join(subdir, 'second-level-command-1.html'),
                 'wt') as f:
      f.write('This is old content that should be edited.\n')
    subdir = os.path.join(subdir, 'subgroup')
    file_utils.MakeDir(subdir)
    with io.open(os.path.join(subdir, 'second-level-command-0.html'),
                 'wt') as f:
      f.write('This is old content that should be deleted.\n')

  def testUpdateDevSite(self):

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.DevSiteGenerator).Update()
    expected = """\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
add _toc.yaml
add alpha/_toc.yaml
add alpha/index.html
add alpha/internal/index.html
add alpha/internal/internal-command.html
add alpha/sdk/alphagroup/index.html
add alpha/sdk/hidden-command.html
add alpha/sdk/hiddengroup/hidden-command-2.html
add alpha/sdk/hiddengroup/hidden-command-a.html
add alpha/sdk/hiddengroup/index.html
add alpha/sdk/index.html
add alpha/sdk/ordered-choices.html
add alpha/sdk/second-level-command-1.html
add alpha/sdk/second-level-command-b.html
add alpha/sdk/subgroup/index.html
add alpha/sdk/subgroup/subgroup-command-2.html
add alpha/sdk/subgroup/subgroup-command-a.html
add alpha/sdk/xyzzy.html
add alpha/version.html
add beta/_toc.yaml
add beta/index.html
add beta/internal/index.html
add beta/internal/internal-command.html
add beta/sdk/betagroup/beta-command.html
add beta/sdk/betagroup/index.html
add beta/sdk/betagroup/sub-command-2.html
add beta/sdk/betagroup/sub-command-a.html
add beta/sdk/hidden-command.html
add beta/sdk/hiddengroup/hidden-command-2.html
add beta/sdk/hiddengroup/hidden-command-a.html
add beta/sdk/hiddengroup/index.html
add beta/sdk/index.html
add beta/sdk/ordered-choices.html
add beta/sdk/second-level-command-1.html
add beta/sdk/second-level-command-b.html
add beta/sdk/subgroup/index.html
add beta/sdk/subgroup/subgroup-command-2.html
add beta/sdk/subgroup/subgroup-command-a.html
add beta/sdk/xyzzy.html
add beta/version.html
add index.html
add internal/_toc.yaml
add internal/index.html
add internal/internal-command.html
add sdk/_toc.yaml
add sdk/hidden-command.html
add sdk/hiddengroup/hidden-command-2.html
add sdk/hiddengroup/hidden-command-a.html
add sdk/hiddengroup/index.html
add sdk/index.html
add sdk/ordered-choices.html
add sdk/second-level-command-b.html
add sdk/subgroup/index.html
add sdk/subgroup/subgroup-command-2.html
add sdk/subgroup/subgroup-command-a.html
add sdk/xyzzy.html
add version.html
delete sdk/subgroup/second-level-command-0.html
edit sdk/second-level-command-1.html
"""
    self.assertEqual(59, changes)
    self.AssertErrEquals(expected.replace('/', os.path.sep))
    self.ClearErr()

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.DevSiteGenerator).Update()
    self.assertEqual(0, changes)
    self.AssertErrEquals("""\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
""")


class HelpTextUpdaterTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):

    self.cli = self.LoadTestCli('sdk4')
    self.help_dir = os.path.join(self.temp_path, 'help')
    shutil.rmtree(self.help_dir, ignore_errors=True)
    file_utils.MakeDir(self.help_dir)
    subdir = os.path.join(self.help_dir, 'sdk')
    file_utils.MakeDir(subdir)
    with io.open(os.path.join(subdir, 'second-level-command-1'), 'wt') as f:
      f.write('This is old content that should be edited.\n')
    subdir = os.path.join(subdir, 'subgroup')
    file_utils.MakeDir(subdir)
    with io.open(os.path.join(subdir, 'second-level-command-0'), 'wt') as f:
      f.write('This is old content that should be deleted.\n')

  def testUpdateHelpTextNotAbsolute(self):
    with self.AssertRaisesExceptionMatches(
        help_util.HelpUpdateError,
        'Destination directory [help_text] must be absolute.'):
      help_util.HelpUpdater(
          self.cli, 'help_text', walker_util.HelpTextGenerator).Update()

  def testUpdateHelpTextDirectoryNotFound(self):
    with self.AssertRaisesExceptionMatches(
        help_util.HelpUpdateError,
        'Destination directory [/NoT/uNdEr/BoZoS/bIgToP/help] '
        'must exist and be searchable.'):
      help_util.HelpUpdater(
          self.cli, '/NoT/uNdEr/BoZoS/bIgToP/help',
          walker_util.HelpTextGenerator).Update()

  def testUpdateHelpText(self):

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.HelpTextGenerator).Update()
    expected = """\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
add GROUP
add alpha/GROUP
add alpha/internal/GROUP
add alpha/internal/internal-command
add alpha/sdk/GROUP
add alpha/sdk/alphagroup/GROUP
add alpha/sdk/hidden-command
add alpha/sdk/hiddengroup/GROUP
add alpha/sdk/hiddengroup/hidden-command-2
add alpha/sdk/hiddengroup/hidden-command-a
add alpha/sdk/ordered-choices
add alpha/sdk/second-level-command-1
add alpha/sdk/second-level-command-b
add alpha/sdk/subgroup/GROUP
add alpha/sdk/subgroup/subgroup-command-2
add alpha/sdk/subgroup/subgroup-command-a
add alpha/sdk/xyzzy
add alpha/version
add beta/GROUP
add beta/internal/GROUP
add beta/internal/internal-command
add beta/sdk/GROUP
add beta/sdk/betagroup/GROUP
add beta/sdk/betagroup/beta-command
add beta/sdk/betagroup/sub-command-2
add beta/sdk/betagroup/sub-command-a
add beta/sdk/hidden-command
add beta/sdk/hiddengroup/GROUP
add beta/sdk/hiddengroup/hidden-command-2
add beta/sdk/hiddengroup/hidden-command-a
add beta/sdk/ordered-choices
add beta/sdk/second-level-command-1
add beta/sdk/second-level-command-b
add beta/sdk/subgroup/GROUP
add beta/sdk/subgroup/subgroup-command-2
add beta/sdk/subgroup/subgroup-command-a
add beta/sdk/xyzzy
add beta/version
add internal/GROUP
add internal/internal-command
add sdk/GROUP
add sdk/hidden-command
add sdk/hiddengroup/GROUP
add sdk/hiddengroup/hidden-command-2
add sdk/hiddengroup/hidden-command-a
add sdk/ordered-choices
add sdk/second-level-command-b
add sdk/subgroup/GROUP
add sdk/subgroup/subgroup-command-2
add sdk/subgroup/subgroup-command-a
add sdk/xyzzy
add version
delete sdk/subgroup/second-level-command-0
edit sdk/second-level-command-1
"""
    self.assertEqual(54, changes)
    self.AssertErrEquals(expected.replace('/', os.path.sep))
    self.ClearErr()

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.HelpTextGenerator).Update()
    self.assertEqual(0, changes)
    self.AssertErrEquals("""\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
""")

  def testUpdateHelpTextTest(self):

    changes = help_util.HelpUpdater(
        self.cli, self.help_dir, walker_util.HelpTextGenerator,
        test=True).Update()
    expected = """\
{"ux": "PROGRESS_BAR", "message": "Generating Help Document Files"}
add GROUP
add alpha/GROUP
add alpha/internal/GROUP
add alpha/internal/internal-command
add alpha/sdk/GROUP
add alpha/sdk/alphagroup/GROUP
add alpha/sdk/hidden-command
add alpha/sdk/hiddengroup/GROUP
add alpha/sdk/hiddengroup/hidden-command-2
add alpha/sdk/hiddengroup/hidden-command-a
add alpha/sdk/ordered-choices
add alpha/sdk/second-level-command-1
add alpha/sdk/second-level-command-b
add alpha/sdk/subgroup/GROUP
add alpha/sdk/subgroup/subgroup-command-2
add alpha/sdk/subgroup/subgroup-command-a
add alpha/sdk/xyzzy
add alpha/version
add beta/GROUP
add beta/internal/GROUP
add beta/internal/internal-command
add beta/sdk/GROUP
add beta/sdk/betagroup/GROUP
add beta/sdk/betagroup/beta-command
add beta/sdk/betagroup/sub-command-2
add beta/sdk/betagroup/sub-command-a
add beta/sdk/hidden-command
add beta/sdk/hiddengroup/GROUP
add beta/sdk/hiddengroup/hidden-command-2
add beta/sdk/hiddengroup/hidden-command-a
add beta/sdk/ordered-choices
...
54 help test files changed
"""
    self.assertEqual(54, changes)
    self.AssertErrEquals(expected.replace('/', os.path.sep))

  def testUpdateHelpTextInvalidBrandAbbreviationTest(self):

    # Challenge: do this with self.StartObjectPatch().
    try:
      invalid_brand_abbreviations = help_util.INVALID_BRAND_ABBREVIATIONS
      help_util.INVALID_BRAND_ABBREVIATIONS = ['error', 'image']
      with self.AssertRaisesExceptionMatches(
          help_util.HelpUpdateError,
          '6 help document files with invalid content must be fixed.'):
        help_util.HelpUpdater(
            self.cli, self.help_dir, walker_util.HelpTextGenerator,
            test=True).Update()
    finally:
      help_util.INVALID_BRAND_ABBREVIATIONS = invalid_brand_abbreviations
    expected = """\
ERROR: [sdk/subgroup/subgroup-command-a] Help document cannot contain these abbreviations: [error,image].
"""
    self.AssertErrContains(expected.replace('/', os.path.sep))

  def testUpdateHelpTextBadUpdate(self):
    mock_copyfile = self.StartObjectPatch(shutil, 'copyfile')

    mock_copyfile.side_effect = IOError('File copy error.')
    with self.AssertRaisesExceptionMatches(
        help_util.HelpUpdateError,
        'Update failed: File copy error.'):
      help_util.HelpUpdater(
          self.cli, self.help_dir, walker_util.HelpTextGenerator).Update()

    mock_copyfile.side_effect = OSError('Access denied.')
    with self.AssertRaisesExceptionMatches(
        help_util.HelpUpdateError,
        'Update failed: Access denied.'):
      help_util.HelpUpdater(
          self.cli, self.help_dir, walker_util.HelpTextGenerator).Update()


if __name__ == '__main__':
  calliope_test_base.main()
