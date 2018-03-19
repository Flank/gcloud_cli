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
"""Tests for gcloud meta generatehelp-docs."""

import os

from googlecloudsdk.calliope import walker
from googlecloudsdk.calliope import walker_util
from googlecloudsdk.command_lib.meta import help_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base
from tests.lib import cli_test_base
from tests.lib import test_case


class GenerateHelpDocsDirTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.devsite_generator = self.StartObjectPatch(
        walker_util, 'DevSiteGenerator')
    self.help_text_generator = self.StartObjectPatch(
        walker_util, 'HelpTextGenerator')
    self.help_text_updater = self.StartObjectPatch(
        help_util.HelpTextUpdater, '__init__', return_value=None)
    self.update = self.StartObjectPatch(
        help_util.HelpTextUpdater, 'Update', return_value=1)
    self.html_generator = self.StartObjectPatch(
        walker_util, 'HtmlGenerator')
    self.manpage_generator = self.StartObjectPatch(
        walker_util, 'ManPageGenerator')

  def testGenerateHelpDocsNone(self):
    self.Run(['meta', 'generate-help-docs'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_text_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsDevSite(self):
    devsite_dir = '/devsite'
    self.Run(['meta', 'generate-help-docs', '--devsite-dir=' + devsite_dir])
    self.devsite_generator.assert_called_once_with(self.cli, devsite_dir)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_text_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpText(self):
    help_text_dir = '/help_text'
    self.Run(['meta', 'generate-help-docs', '--help-text-dir=' + help_text_dir])
    self.assertFalse(self.devsite_generator.called)
    self.help_text_generator.assert_called_once_with(self.cli, help_text_dir)
    self.assertFalse(self.help_text_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPage(self):
    manpage_dir = '/manpage'
    self.Run(['meta', 'generate-help-docs', '--manpage-dir=' + manpage_dir])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_text_updater.called)
    self.assertFalse(self.html_generator.called)
    self.manpage_generator.assert_called_once_with(self.cli, manpage_dir)

  def testGenerateHelpDocsDevSiteManPage(self):
    devsite_dir = '/devsite'
    manpage_dir = '/manpage'
    self.Run(['meta', 'generate-help-docs',
              '--devsite-dir=' + devsite_dir,
              '--manpage-dir=' + manpage_dir])
    self.devsite_generator.assert_called_once_with(self.cli, devsite_dir)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_text_updater.called)
    self.assertFalse(self.html_generator.called)
    self.manpage_generator.assert_called_once_with(self.cli, manpage_dir)

  def testGenerateHelpDocsHelpTextUpdate(self):
    update_help_text_dir = '/doc/help_text'
    self.Run(['meta', 'generate-help-docs',
              '--update-help-text-dir=' + update_help_text_dir])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_text_updater.assert_called_once_with(
        self.cli, update_help_text_dir, test=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpTextUpdateTestNoChanges(self):
    self.update.return_value = False
    update_help_text_dir = '/doc/help_text'
    self.Run(['meta', 'generate-help-docs',
              '--update-help-text-dir=' + update_help_text_dir,
              '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_text_updater.assert_called_once_with(
        self.cli, update_help_text_dir, test=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpTextUpdateTestChanges(self):
    self.update.return_value = True
    update_help_text_dir = '/doc/help_text'
    with self.assertRaisesRegexp(exceptions.Error,
                                 'Help text files must be updated.'):
      self.Run(['meta', 'generate-help-docs',
                '--update-help-text-dir=' + update_help_text_dir,
                '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_text_updater.assert_called_once_with(
        self.cli, update_help_text_dir, test=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)


class GenerateHelpDocsRestrictTest(calliope_test_base.CalliopeTestBase,
                                   test_case.WithOutputCapture):

  def SetUp(self):
    self.WalkTestCli('sdk3')
    def MockWalk(unused_hidden, unused_restrict):
      return None

    self.walk = self.StartObjectPatch(walker.Walker, 'Walk')
    self.walk.side_effect = MockWalk

  def testGenerateHelpDocsNoRestrictions(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--devsite-dir=' + devsite_dir])
      self.walk.assert_called_once_with(None, [])

  def testGenerateHelpDocsOneRestriction(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--devsite-dir=' + devsite_dir,
                'foo'])
      self.walk.assert_called_once_with(None, ['foo'])

  def testGenerateHelpDocsTwoRestrictions(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs',
                '--devsite-dir=' + devsite_dir, 'foo', 'bar'])
      self.walk.assert_called_once_with(None, ['foo', 'bar'])

  def testGenerateHelpDocsHiddenNoRestrictions(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--hidden',
                '--devsite-dir=' + devsite_dir])
      self.walk.assert_called_once_with(True, [])

  def testGenerateHelpDocsHiddenOneRestriction(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--hidden',
                '--devsite-dir=' + devsite_dir, 'foo'])
      self.walk.assert_called_once_with(True, ['foo'])

  def testGenerateHelpDocsHiddenTwoRestrictions(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--hidden',
                '--devsite-dir=' + devsite_dir, 'foo', 'bar'])
      self.walk.assert_called_once_with(True, ['foo', 'bar'])

  def testGenerateHelpDocsBadFlag(self):
    with self.AssertRaisesArgumentErrorMatches(
        'unrecognized arguments: --No-SuCh-FlAg'):
      self.Run(['meta', 'generate-help-docs', '--No-SuCh-FlAg'])


class GenerateHelpDocsHtmlDirTest(calliope_test_base.CalliopeTestBase,
                                  test_case.WithOutputCapture):

  def SetUp(self):
    self.WalkTestCli('sdk3')

  def testGenerateHelpDocsHtmlDir(self):
    with files.TemporaryDirectory() as temp_dir:
      html_dir = os.path.join(temp_dir, 'www')
      files.MakeDir(html_dir)
      self.Run(['meta', 'generate-help-docs', '--html-dir=' + html_dir])
      self.AssertDirectoryIsGolden(html_dir, __file__, 'html.dir')
      menu_html = os.path.join(html_dir, '_menu_.html')
      self.AssertFileIsGolden(menu_html, __file__, '_menu_.html')


if __name__ == '__main__':
  cli_test_base.main()
