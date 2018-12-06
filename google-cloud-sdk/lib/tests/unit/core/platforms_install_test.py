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

"""Unit tests for the platforms_install module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.core import platforms_install
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

from tests.lib import sdk_test_base
from tests.lib import subtests
from tests.lib import test_case


class PlatformsInstallTest(test_case.WithInput,
                           test_case.WithOutputCapture,
                           sdk_test_base.SdkBase):

  def SetUp(self):
    self.sdk_root_path = self.CreateTempDir('cloudsdk')
    self.home_path = self.CreateTempDir('home')
    self.restore_env = {}
    self.StartPatch('googlecloudsdk.core.util.files.GetHomeDir',
                    return_value=self.home_path)
    self.StartEnvPatch(
        {'ENV': '', 'HOME': self.home_path, 'SHELL': '/bin/bash'})
    # Need to mock this because in a test environment it returns False by
    # default.
    self.can_prompt_mock = self.StartObjectPatch(console_io, 'CanPrompt',
                                                 return_value=True)
    self.StartObjectPatch(platforms_install._RcUpdater, '_CompletionExists',
                          return_value=True)

  def TearDown(self):
    properties.VALUES.core.disable_prompts.Set(False)

  def SetAnswers(self, *answers):
    self.WriteInput(*answers)
    return len(answers)

  def testNoPromptWhenRcPathSpecifiedNoUpdate(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrEquals('')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.bash.inc'))
    os_mock.reset_mock()

  def testNoPromptWhenRcPathNotSpecifiedNoUpdate(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path, name='.bashrc',
                         contents='# Empty\n')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=False,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrEquals('')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.bash.inc'))
    os_mock.reset_mock()

  def testPromptWhenRcPathNotSpecifiedWithUpdate(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty ⚡️⚡️⚡\n')
    self.SetAnswers(rc_path)

    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty ⚡️⚡️⚡

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptsDisabled(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputNotContains(rc_path)

  def testPromptsDisabledWithPathAndPathUpdateSpecified(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # Should contain the update PATH line.
    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertFileExistsWithContents(expected_content, rc_path)
    # No prompt.
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputNotContains('The default file will be updated: ')
    self.AssertOutputNotContains('Profile will be modified to update your '
                                 '$PATH and enable shell command completion.')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptsDisabledWithPathSpecifiedAndUpdatesUnspecified(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # Should contain the update PATH line.
    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.bash.inc'))
    self.AssertFileExistsWithContents(expected_content, rc_path)
    # No prompt.
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputContains('Profile will be modified to update your $PATH '
                              'and enable shell command completion.')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptsDisabledWithPathSpecifiedAndOneUpdateUnspecified(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    platforms_install.UpdateRC(
        completion_update=None,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # Should contain the update PATH line.
    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertFileExistsWithContents(expected_content, rc_path)
    # No prompt.
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputNotContains('Profile will be modified to update your '
                                 '$PATH and enable shell command completion.')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptsDisabledWithUpdateSpecifiedAndNoPath(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.StartObjectPatch(platforms_install, '_GetShellRcFileName',
                          return_value=rc_path)
    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # Should contain the update PATH line.
    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    # No prompt.
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputContains('The default file will be updated: ')
    self.AssertOutputNotContains('Profile will be modified to update your '
                                 '$PATH and enable shell command completion.')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptsDisabledWithOneUpdateSpecifiedAndNoPath(self):
    self.can_prompt_mock.return_value = False
    os_mock = self.StartObjectPatch(
        platforms.OperatingSystem, 'Current',
        return_value=platforms.OperatingSystem.LINUX)

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.StartObjectPatch(platforms_install, '_GetShellRcFileName',
                          return_value=rc_path)
    platforms_install.UpdateRC(
        completion_update=True,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # Should contain the update PATH line.
    expected_content = """\
# Empty

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(completion=os.path.join(self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    # No prompt.
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputContains('The default file will be updated: ')
    self.AssertOutputNotContains('Profile will be modified to update your '
                                 '$PATH and enable shell command completion.')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYes(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.SetAnswers('y', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYesRepeatedLines(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    original_content = """\
# head

# The next line updates PATH for the Google Cloud SDK.
source '/some/dir/path.bash.inc'

# The next line updates PATH for the Google Cloud SDK.
source '/other/dir/path.bash.inc'

# The next line enables shell command completion for gcloud.
source '/some/dir/completion.bash.inc'

# The next line enables shell command completion for gcloud.
source '/other/dir/completion.bash.inc'

# The next line updates PATH for the Google Cloud SDK.
source '/another/dir/path.bash.inc'

# tail
"""
    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents=original_content)
    self.SetAnswers('y', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# head

# tail

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdatePathWithYes(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=None,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to update your $PATH')
    self.AssertErrNotContains(
        'Modify profile to enable shell command completion')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdateBashCompletionWithYes(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line enables shell command completion for gcloud.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'completion.bash.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to enable shell command')
    self.AssertErrNotContains('Modify profile to update your $PATH')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testRcPathSpecifiedWithNewDir(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = os.path.join(self.temp_path, 'temp_subdir', '.bashrc')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    self.AssertFileExistsWithContents("""\

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc')), rc_path)
    os_mock.reset_mock()

  def testFailWhenRcPathIsDir(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    rc_path = os.path.join(self.temp_path, 'temp_subdir')
    os.mkdir(rc_path)
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)
    self.AssertOutputContains('[{rc_path}] exists and is not a file, so it '
                              'cannot be updated.'.format(
                                  rc_path=rc_path))
    os_mock.reset_mock()

  def testFailWhenRcPathCannotBeCreated(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    makedirs_mock = self.StartObjectPatch(files, 'MakeDir',
                                          side_effect=files.Error)
    rc_path = os.path.join(self.temp_path, 'temp_subdir', '.bashrc')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)
    self.AssertOutputContains('Could not create directories for [{rc_path}], '
                              'so it cannot be updated.'.format(
                                  rc_path=rc_path))
    os_mock.reset_mock()
    makedirs_mock.reset_mock()

  def testFailWhenRcPathCannotBeWritten(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    open_mock = self.StartObjectPatch(io,
                                      'open',
                                      side_effect=IOError)
    rc_path = os.path.join(self.temp_path, 'temp_subdir', '.bashrc')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=True,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)
    self.AssertOutputContains(
        'Could not update [{rc_path}]. Ensure you have write access to this '
        'location.'.format(rc_path=rc_path))
    os_mock.reset_mock()
    open_mock.reset_mock()

  def testPromptWithNo(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')
    self.SetAnswers('n', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrContains('update your $PATH and enable shell command')
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.bash.inc'))
    os_mock.reset_mock()

  def testNoPromptWhenRcPathNotSpecifiedNoUpdateWithKshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/ksh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.kshrc', contents='# Empty\n')

    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    expected_err = (
        '{"ux": "PROMPT_RESPONSE", "message": "The Google Cloud SDK installer '
        'will now prompt you to update an rc file to bring the Google Cloud '
        'CLIs into your environment.\\n\\nEnter a path to an rc file to '
        'update, or leave blank to use [%s]: "}' % os.path.join(
            self.home_path, '.kshrc').replace('\\', '\\\\'))
    self.AssertErrEquals(expected_err, normalize_space=True)
    self.AssertOutputContains(os.path.join(self.home_path, '.kshrc'))
    os_mock.reset_mock()

  def testPromptWithYesSpecifiedWithKshEnvWithEnvFile(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.sh.env', contents='# Empty\n')
    self.StartEnvPatch({'SHELL': '/bin/ksh', 'ENV': rc_path})

    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.bash.inc'),
           completion=os.path.join(self.sdk_root_path, 'completion.bash.inc'))
    self.AssertFileExistsWithContents(expected_content, rc_path)
    expected_err = (
        '{"ux": "PROMPT_RESPONSE", "message": "The Google Cloud SDK installer '
        'will now prompt you to update an rc file to bring the Google Cloud '
        'CLIs into your environment.\\n\\nEnter a path to an rc file to '
        'update, or leave blank to use [%s]: "}' % os.path.join(
            rc_path.replace('\\', '\\\\')))
    self.AssertErrEquals(expected_err, normalize_space=True)
    expected_out = """\
Backing up [{0}] to [{0}.backup].
[{0}] has been updated.

==> Start a new shell for the changes to take effect.

""".format(rc_path)
    self.AssertOutputContains(expected_out, normalize_space=True)
    os_mock.reset_mock()

  def testNoPromptWhenRcPathSpecifiedNoUpdateWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.bashrc', contents='# Empty\n')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrEquals('')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.zsh.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.zsh.inc'))
    os_mock.reset_mock()

  def testNoPromptWhenRcPathNotSpecifiedNoUpdateWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=False,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrEquals('')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.zsh.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.zsh.inc'))
    os_mock.reset_mock()

  def testPromptWhenRcPathNotSpecifiedWithUpdateWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers(rc_path)

    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYesWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'),
           completion=os.path.join(self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdatePathWithYesWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=None,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to update your $PATH')
    self.AssertErrNotContains(
        'Modify profile to enable shell command completion')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdateBashCompletionWithYesWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line enables shell command completion for gcloud.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to enable shell command')
    self.AssertErrNotContains('Modify profile to update your $PATH')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithNoWithZshEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/zsh'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('n', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrContains('update your $PATH and enable shell command')
    self.AssertErrNotContains('Enter a path to an rc file to update')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.zsh.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.zsh.inc'))
    os_mock.reset_mock()

  def testNoPromptWhenRcPathSpecifiedNoUpdateWithZshRc(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    platforms_install.UpdateRC(
        completion_update=False,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    # File is unchanged
    self.AssertFileExistsWithContents('# Empty\n', rc_path)
    self.AssertErrEquals('')
    self.AssertOutputContains(os.path.join(self.sdk_root_path, 'path.bash.inc'))
    self.AssertOutputContains(os.path.join(self.sdk_root_path,
                                           'completion.bash.inc'))
    os_mock.reset_mock()

  def testPromptWhenRcPathNotSpecifiedWithUpdateWithZshRc(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers(rc_path)

    platforms_install.UpdateRC(
        completion_update=True,
        path_update=True,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'),
           completion=os.path.join(
               self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYesWithZshRc(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y', rc_path)

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi

# The next line enables shell command completion for gcloud.
if [ -f '{completion}' ]; then . '{completion}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'),
           completion=os.path.join(self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdatePathWithYesWithZshRc(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=False,
        path_update=None,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'path.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to update your $PATH')
    self.AssertErrNotContains(
        'Modify profile to enable shell command completion')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptOnlyUpdateBashCompletionWithYesWithZshRc(self):
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX

    rc_path = self.Touch(directory=self.temp_path,
                         name='.zshrc', contents='# Empty\n')
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=False,
        rc_path=rc_path,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line enables shell command completion for gcloud.
if [ -f '{path}' ]; then . '{path}'; fi
""".format(path=os.path.join(self.sdk_root_path, 'completion.zsh.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Modify profile to enable shell command')
    self.AssertErrNotContains('Modify profile to update your $PATH')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYesWithFishEnv(self):
    self.StartEnvPatch({'SHELL': '/bin/fish'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    self.StartObjectPatch(platforms_install._RcUpdater, '_CompletionExists',
                          return_value=False)

    rc_path = self.Touch(
        directory=os.path.join(self.home_path, '.config', 'fish'),
        name='config.fish', contents='# Empty\n', makedirs=True)
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; . '{path}'; end
""".format(path=os.path.join(self.sdk_root_path, 'path.fish.inc'))

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()

  def testPromptWithYesWithFishEnvExistingSourceInConfigFish(self):
    self.StartEnvPatch({'SHELL': '/bin/fish'})
    os_mock = self.StartObjectPatch(platforms.OperatingSystem, 'Current')
    os_mock.return_value = platforms.OperatingSystem.LINUX
    self.StartObjectPatch(platforms_install._RcUpdater, '_CompletionExists',
                          return_value=False)

    expected_content = """\
# Empty

# The next line updates PATH for the Google Cloud SDK.
if [ -f '{path}' ]; . '{path}'; end
""".format(path=os.path.join(self.sdk_root_path, 'path.fish.inc'))

    rc_path = self.Touch(
        directory=os.path.join(self.home_path, '.config', 'fish'),
        name='config.fish', contents=expected_content, makedirs=True)
    self.SetAnswers('y')

    platforms_install.UpdateRC(
        completion_update=None,
        path_update=None,
        rc_path=None,
        bin_path=None,
        sdk_root=self.sdk_root_path)

    self.AssertFileExistsWithContents(expected_content, rc_path)
    self.AssertErrContains('Enter a path to an rc file to update')
    self.AssertOutputContains(rc_path)
    os_mock.reset_mock()


class RcUpdaterTest(subtests.Base, sdk_test_base.SdkBase):
  """Tests _RcUpdater."""

  def SetUp(self):
    self.home_dir = self.CreateTempDir('home')
    self.StartObjectPatch(platforms_install, '_TraceAction')
    self.StartObjectPatch(platforms_install._RcUpdater, '_CompletionExists',
                          return_value=True)

  def RunSubTest(self, actual):
    return actual

  def GetTestContents(self, multiline_if, old_completion_in_rc, old_path_in_rc,
                      add_completion_to_rc, add_path_to_rc):
    sdk_root = '/local/cloudsdk'
    updater = platforms_install._RcUpdater(
        completion_update=add_completion_to_rc,
        path_update=add_path_to_rc,
        shell='bash',
        rc_path=os.path.join(self.home_dir, '.bashrc'),
        sdk_root=sdk_root,
    )
    if multiline_if:
      old_sep_then, old_sep_fi = '\n  ', '\n'
    else:
      old_sep_then, old_sep_fi = ' ', '; '

    # Generate the old contents.
    old_rc_lines = [
        '# RC file with unicode ⚡️️️⚡️⚡️.\n',
        '\n',
        'precious user top\n',
    ]
    if old_path_in_rc:
      old_rc_lines.extend([
          '\n',
          '# The next line updates PATH for the Google Cloud SDK.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'old-path.bash.inc')),
          old_sep_then,
          "source '{path}'".format(
              path=os.path.join(sdk_root, 'old-path.bash.inc')),
          old_sep_fi,
          'fi\n',
      ])
    if old_completion_in_rc:
      old_rc_lines.extend([
          '\n',
          '# The next line enables shell command completion for gcloud.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'old-completion.bash.inc')),
          old_sep_then,
          "source '{path}'".format(
              path=os.path.join(sdk_root, 'old-completion.bash.inc')),
          old_sep_fi,
          'fi\n',
      ])
    old_rc_lines.extend([
        '\n',
        'precious user extra\n',
    ])
    files.WriteFileContents(updater.rc_path, ''.join(old_rc_lines))

    # Generate the expected contents.
    add_then, add_fi = ' ', '; '
    add_rc_lines = [
        '# RC file with unicode ⚡️️️⚡️⚡️.\n',
        '\n',
        'precious user top\n',
    ]
    if old_path_in_rc and not add_path_to_rc:
      add_rc_lines.extend([
          '\n',
          '# The next line updates PATH for the Google Cloud SDK.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'old-path.bash.inc')),
          old_sep_then,
          "source '{path}'".format(
              path=os.path.join(sdk_root, 'old-path.bash.inc')),
          old_sep_fi,
          'fi\n',
      ])
    if old_completion_in_rc and not add_completion_to_rc:
      add_rc_lines.extend([
          '\n',
          '# The next line enables shell command completion for gcloud.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'old-completion.bash.inc')),
          old_sep_then,
          "source '{path}'".format(
              path=os.path.join(sdk_root, 'old-completion.bash.inc')),
          old_sep_fi,
          'fi\n',
      ])
    add_rc_lines.extend([
        '\n',
        'precious user extra\n',
    ])
    if add_path_to_rc:
      add_rc_lines.extend([
          '\n',
          '# The next line updates PATH for the Google Cloud SDK.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'path.bash.inc')),
          add_then,
          ". '{path}'".format(
              path=os.path.join(sdk_root, 'path.bash.inc')),
          add_fi,
          'fi\n',
      ])
    if add_completion_to_rc:
      add_rc_lines.extend([
          '\n',
          '# The next line enables shell command completion for gcloud.\n',
          "if [ -f '{path}' ]; then".format(
              path=os.path.join(sdk_root, 'completion.bash.inc')),
          add_then,
          ". '{path}'".format(
              path=os.path.join(sdk_root, 'completion.bash.inc')),
          add_fi,
          'fi\n',
      ])
    expected = ''.join(add_rc_lines)

    # Get the actual contents.
    updater.Update()
    actual = files.ReadFileContents(updater.rc_path)
    return expected, actual

  def testRcUpdater(self):

    def T(multiline_if, old_completion_in_rc, old_path_in_rc,
          add_completion_to_rc, add_path_to_rc):
      """One RC file update test.

      Args:
        multiline_if: bool, if...fi on 3 lines instead of 1.
        old_completion_in_rc: bool, rc file has old completion lines.
        old_path_in_rc: bool, rc file has old PATH lines.
        add_completion_to_rc: bool, Add new completion lines to rc.
        add_path_to_rc: bool, Add new PATH lines to rc.
      """
      expected, actual = self.GetTestContents(
          multiline_if, old_completion_in_rc, old_path_in_rc,
          add_completion_to_rc, add_path_to_rc)
      self.Run(expected, actual, depth=2)

    # This paranoid test goes through all 32 combinations.

    T(False, False, False, False, False)
    T(False, False, False, False, True)
    T(False, False, False, True, False)
    T(False, False, False, True, True)
    T(False, False, True, False, False)
    T(False, False, True, False, True)
    T(False, False, True, True, False)
    T(False, False, True, True, True)
    T(False, True, False, False, False)
    T(False, True, False, False, True)
    T(False, True, False, True, False)
    T(False, True, False, True, True)
    T(False, True, True, False, False)
    T(False, True, True, False, True)
    T(False, True, True, True, False)
    T(False, True, True, True, True)
    T(True, False, False, False, False)
    T(True, False, False, False, True)
    T(True, False, False, True, False)
    T(True, False, False, True, True)
    T(True, False, True, False, False)
    T(True, False, True, False, True)
    T(True, False, True, True, False)
    T(True, False, True, True, True)
    T(True, True, False, False, False)
    T(True, True, False, False, True)
    T(True, True, False, True, False)
    T(True, True, False, True, True)
    T(True, True, True, False, False)
    T(True, True, True, False, True)
    T(True, True, True, True, False)
    T(True, True, True, True, True)


if __name__ == '__main__':
  test_case.main()
