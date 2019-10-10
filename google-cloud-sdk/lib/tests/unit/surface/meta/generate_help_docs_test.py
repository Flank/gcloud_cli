# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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
    self.help_updater = self.StartObjectPatch(
        help_util.HelpUpdater, '__init__', return_value=None)
    self.update = self.StartObjectPatch(
        help_util.HelpUpdater, 'Update', return_value=1)
    self.html_generator = self.StartObjectPatch(
        walker_util, 'HtmlGenerator')
    self.manpage_generator = self.StartObjectPatch(
        walker_util, 'ManPageGenerator')

  def testGenerateHelpDocsNone(self):
    self.Run(['meta', 'generate-help-docs'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsDevSite(self):
    devsite_dir = '/devsite'
    self.Run(['meta', 'generate-help-docs', '--devsite-dir=' + devsite_dir])
    self.devsite_generator.assert_called_once_with(self.cli, devsite_dir)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpText(self):
    help_text_dir = '/help_text'
    self.Run(['meta', 'generate-help-docs', '--help-text-dir=' + help_text_dir])
    self.assertFalse(self.devsite_generator.called)
    self.help_text_generator.assert_called_once_with(self.cli, help_text_dir)
    self.assertFalse(self.help_updater.called)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPage(self):
    manpage_dir = '/manpage'
    self.Run(['meta', 'generate-help-docs', '--manpage-dir=' + manpage_dir])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.assertFalse(self.help_updater.called)
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
    self.assertFalse(self.help_updater.called)
    self.assertFalse(self.html_generator.called)
    self.manpage_generator.assert_called_once_with(self.cli, manpage_dir)

  def testGenerateHelpDocsHelpTextUpdate(self):
    update_help_text_dir = '/doc/help_text'
    self.Run(['meta', 'generate-help-docs',
              '--help-text-dir=' + update_help_text_dir,
              '--update'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_help_text_dir, self.help_text_generator, test=False,
        hidden=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpTextUpdateDeprecated(self):
    update_help_text_dir = '/doc/help_text'
    self.Run(['meta', 'generate-help-docs',
              '--update-help-text-dir=' + update_help_text_dir])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_help_text_dir, self.help_text_generator, test=False,
        hidden=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)
    self.AssertErrContains('[--update-help-text-dir=/doc/help_text] is '
                           'deprecated. Use this instead: --update '
                           '--help-text-dir=/doc/help_text.')

  def testGenerateHelpDocsHelpTextUpdateTestNoChanges(self):
    self.update.return_value = False
    update_help_text_dir = '/doc/help_text'
    self.Run(['meta', 'generate-help-docs',
              '--help-text-dir=' + update_help_text_dir,
              '--update',
              '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_help_text_dir, self.help_text_generator, test=True,
        hidden=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHelpTextUpdateTestChanges(self):
    self.update.return_value = True
    update_help_text_dir = '/doc/help_text'
    with self.assertRaisesRegex(exceptions.Error,
                                'document files must be updated.'):
      self.Run(['meta', 'generate-help-docs',
                '--help-text-dir=' + update_help_text_dir,
                '--update',
                '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_help_text_dir, self.help_text_generator, test=True,
        hidden=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsDevSiteUpdate(self):
    update_devsite_dir = '/doc/devsite'
    self.Run(['meta', 'generate-help-docs',
              '--devsite-dir=' + update_devsite_dir,
              '--update'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_devsite_dir, self.devsite_generator, test=False,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsDevSiteUpdateTestNoChanges(self):
    self.update.return_value = False
    update_devsite_dir = '/doc/devsite'
    self.Run(['meta', 'generate-help-docs',
              '--devsite-dir=' + update_devsite_dir,
              '--update',
              '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_devsite_dir, self.devsite_generator, test=True,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsDevSiteUpdateTestChanges(self):
    self.update.return_value = True
    update_devsite_dir = '/doc/devsite'
    with self.assertRaisesRegex(exceptions.Error,
                                'document files must be updated.'):
      self.Run(['meta', 'generate-help-docs',
                '--devsite-dir=' + update_devsite_dir,
                '--update',
                '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_devsite_dir, self.devsite_generator, test=True,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHtmlUpdate(self):
    update_html_dir = '/doc/www'
    self.Run(['meta', 'generate-help-docs',
              '--html-dir=' + update_html_dir,
              '--update'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_html_dir, self.html_generator, test=False,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHtmlUpdateTestNoChanges(self):
    self.update.return_value = False
    update_html_dir = '/doc/www'
    self.Run(['meta', 'generate-help-docs',
              '--html-dir=' + update_html_dir,
              '--update',
              '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_html_dir, self.html_generator, test=True,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsHtmlUpdateTestChanges(self):
    self.update.return_value = True
    update_html_dir = '/doc/www'
    with self.assertRaisesRegex(exceptions.Error,
                                'document files must be updated.'):
      self.Run(['meta', 'generate-help-docs',
                '--html-dir=' + update_html_dir,
                '--update',
                '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_html_dir, self.html_generator, test=True,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPageUpdate(self):
    update_manpage_dir = '/doc/manpage'
    self.Run(['meta', 'generate-help-docs',
              '--manpage-dir=' + update_manpage_dir,
              '--update'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_manpage_dir, self.manpage_generator, test=False,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPageTestNoChangesHidden(self):
    self.update.return_value = False
    update_manpage_dir = '/doc/manpage'
    self.Run(['meta', 'generate-help-docs',
              '--manpage-dir=' + update_manpage_dir,
              '--update',
              '--test',
              '--hidden'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_manpage_dir, self.manpage_generator, test=True,
        hidden=True)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPageTestNoChanges(self):
    self.update.return_value = False
    update_manpage_dir = '/doc/manpage'
    self.Run(['meta', 'generate-help-docs',
              '--manpage-dir=' + update_manpage_dir,
              '--update',
              '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_manpage_dir, self.manpage_generator, test=True,
        hidden=False)
    self.assertFalse(self.html_generator.called)
    self.assertFalse(self.manpage_generator.called)

  def testGenerateHelpDocsManPageUpdateTestChanges(self):
    self.update.return_value = True
    update_manpage_dir = '/doc/manpage'
    with self.assertRaisesRegex(exceptions.Error,
                                'document files must be updated.'):
      self.Run(['meta', 'generate-help-docs',
                '--manpage-dir=' + update_manpage_dir,
                '--update',
                '--test'])
    self.assertFalse(self.devsite_generator.called)
    self.assertFalse(self.help_text_generator.called)
    self.help_updater.assert_called_once_with(
        self.cli, update_manpage_dir, self.manpage_generator, test=True,
        hidden=False)
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
      self.walk.assert_called_once_with(False, [])

  def testGenerateHelpDocsOneRestriction(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs', '--devsite-dir=' + devsite_dir,
                'foo'])
      self.walk.assert_called_once_with(False, ['foo'])

  def testGenerateHelpDocsTwoRestrictions(self):
    with files.TemporaryDirectory() as devsite_dir:
      self.Run(['meta', 'generate-help-docs',
                '--devsite-dir=' + devsite_dir, 'foo', 'bar'])
      self.walk.assert_called_once_with(False, ['foo', 'bar'])

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
