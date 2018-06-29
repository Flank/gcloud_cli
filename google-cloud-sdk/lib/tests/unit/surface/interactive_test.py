# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Unit tests for the interactive command."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import cli_tree
from googlecloudsdk.command_lib.interactive import application
from googlecloudsdk.core.util import files
from tests.lib import calliope_test_base


class InteractiveTest(calliope_test_base.CalliopeTestBase):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.StartObjectPatch(application, 'main', return_value=None)

  def testInteractiveSplash(self):
    self.Run('interactive')
    self.AssertOutputEquals("""\
Welcome to the gcloud interactive shell environment.

    Tips:

      o start by typing "gcloud " to get auto-suggestions
      o run gcloud alpha interactive --update-cli-trees to enable
        autocompletion for gsutil and kubectl
      o run gcloud alpha interactive --help for more info

    Run $ gcloud feedback to report bugs or request new features.

""")
    self.AssertErrEquals('')

  def testInteractiveSplashQuiet(self):
    self.Run('interactive --quiet')
    self.AssertOutputEquals('')
    self.AssertErrEquals('')

  def testInteractiveSplashUpdateCliTrees(self):
    self.StartObjectPatch(
        files,
        'FindExecutableOnPath',
        return_value=False)
    self.StartObjectPatch(
        cli_tree,
        'CliTreeDir',
        return_value='.')
    self.Run('interactive --update-cli-trees')
    self.AssertOutputEquals("""\
Welcome to the gcloud interactive shell environment.

    Tips:

      o start by typing "gcloud " to get auto-suggestions
      o run gcloud alpha interactive --update-cli-trees to enable
        autocompletion for gsutil and kubectl
      o run gcloud alpha interactive --help for more info

    Run $ gcloud feedback to report bugs or request new features.

""")
    self.AssertErrEquals("""\
Command [bq] not found.
Command [gsutil] not found.
Command [kubectl] not found.
WARNING: No CLI tree generators for [bq, gsutil, kubectl].
""")

  def testInteractiveHelp(self):
    with self.assertRaises(SystemExit):
      self.Run('interactive --help')
    self.AssertOutputContains("""\
         F2:help:STATE
            Toggles the active help section, ON when enabled, OFF when
            disabled.

         F3:EDIT-MODE
            Toggles the command line edit mode, either emacs or vi. The default
            is determined by the bash(1) set -o vi|emacs setting.

         F7:context
            Sets the context for command input, so you won't have to re-type
            common command prefixes at every prompt. The context is the command
            line from just after the prompt up to the cursor.

            For example, if you are about to work with gcloud compute for a
            while, type gcloud compute and hit F7. This will display gcloud
            compute at subsequent prompts until the context is changed.

            Hit ^C and F7 to clear the context, or edit a command line and/or
            move the cursor and hit F7 to set a different context.

         F8:browse
            Opens a web browser tab/window to display the complete man page
            help for the current command. If there is no active web browser
            (running in ssh(1) for example), then command specific help or
            man(1) help is attempted.

         F9:quit
            Exit.
""")
    self.AssertOutputContains("""\
     bottom_bindings_line
        If True, display the bottom key bindings line. The default value is
        true.

     bottom_status_line
        If True, display the bottom status line. The default value is false.

     completion_menu_lines
        Number of lines in the completion menu. The default value is 4.

     context
        Command context string. The default value is "".

     fixed_prompt_position
        If True, display the prompt at the same position. The default value is
        false.

     help_lines
        Maximum number of help snippet lines. The default value is 10.

     hidden
        If True, expose hidden commands/flags. The default value is false.

     justify_bottom_lines
        If True, left- and right-justify bottom toolbar lines. The default
        value is false.

     manpage_generator
        If True, use the manpage CLI tree generator for unsupported commands.
        The default value is true.

     multi_column_completion_menu
        If True, display the completions as a multi-column menu. The default
        value is false.

     prompt
        Command prompt string. The default value is "$ ".

     show_help
        If True, show help as command args are being entered. The default value
        is true.

     suggest
        If True, add command line suggestions based on history. The default
        value is false.
""")


if __name__ == '__main__':
  calliope_test_base.main()
