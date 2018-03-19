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
"""Tests for [gcloud feedback] command."""

import datetime
import ntpath
import os
import posixpath
import re
import textwrap
import unittest
import urlparse


from googlecloudsdk.command_lib import feedback_util
from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import config
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from tests.lib import cli_test_base
from tests.lib import test_case
import mock


STACKOVERFLOW_URL = 'http://stackoverflow.com/questions/tagged/gcloud'
GROUPS_PAGE_URL = ('https://groups.google.com/forum/?fromgroups#!forum/'
                   'google-cloud-dev')
GROUPS_EMAIL = 'google-cloud-dev@googlegroups.com'
IRC_CHANNEL = '#gcloud'
ISSUE_TRACKER_URL = ('https://issuetracker.google.com/issues'
                     '?q=componentid:187143%2B')


EXAMPLE_LOGS = """\
1970-01-01 00:00:00,000 DEBUG    root            Some debug message
1970-01-01 00:00:00,001 DEBUG    root            Some debug message, part 2
1970-01-01 00:00:00,002 DEBUG    root            Running [gcloud.auth.list] with arguments: []

*** We only want to process exceptions that we've marked during a crash,
*** so we make sure ones like this aren't used found.
Traceback (most recent call last):
  File "/path/to/googlecloudsdk/lib/test.py", line 3, in <module>
    main()
  File "/path/to/googlecloudsdk/lib/test.py", line 2, in main
    example.method()
  File "/path/to/googlecloudsdk/lib/bread/toast.py", line 1, in method
    raise Exception('incidental exception')
Exception: incidental exception
"""

EXAMPLE_TRACEBACK = """\
BEGIN CRASH STACKTRACE
Traceback (most recent call last):
  File "/path/to/googlecloudsdk/lib/test.py", line 3, in <module>
    main()
  File "/path/to/googlecloudsdk/lib/test.py", line 2, in main
    example.method()
  File "/path/to/googlecloudsdk/lib/bread/toast.py", line 1, in method
    raise Exception('really really really long message')
Exception: really really long message
"""

EXAMPLE_TRACEBACK_WINDOWS = """\
BEGIN CRASH STACKTRACE
Traceback (most recent call last):
  File "C:\\Program Files (x86)\\googlecloudsdk\\lib\\test.py", line 3, in <module>
    main()
  File "C:\\Program Files (x86)\\googlecloudsdk\\lib\\test.py", line 2, in main
    example.method()
  File "C:\\Program Files (x86)\\googlecloudsdk\\lib\\bread\\toast.py", line 1, in method
    raise Exception('really really long message')
Exception: really really long message
"""

EXAMPLE_TRACEBACK_EPILOGUE = """\
1970-01-01 00:00:00,003 INFO    ___FILE_ONLY___ \

If you would like to report this issue, please run the following command:


1970-01-01 00:00:00,004 INFO    ___FILE_ONLY___   gcloud feedback
"""


def _GetExampleTraceback():
  """Get the appropriate example traceback based on the current platform."""
  if platforms.OperatingSystem.Current() is platforms.OperatingSystem.WINDOWS:
    return EXAMPLE_TRACEBACK_WINDOWS
  else:
    return EXAMPLE_TRACEBACK


# This is necessary because you can't mock.patch builtins like datetime.datetime
class _FakeDatetime(datetime.datetime):

  # This should be set in order for now() to be useful.
  _TIME = None

  @classmethod
  def now(cls):  # pylint: disable=invalid-name
    return cls._TIME

  @classmethod
  def SetCurrentTime(cls, time):
    cls._TIME = time


class FeedbackTestBase(cli_test_base.CliTestBase):

  _TIMESTAMP_DIR_FORMAT = ('{timestamp.year}.'
                           '{timestamp.month:02}.'
                           '{timestamp.day:02}')
  _TIMESTAMP_LOG_NAME_FORMAT = ('{timestamp.hour:02}.'
                                '{timestamp.minute:02}.'
                                '{timestamp.second:02}.'
                                '{timestamp.microsecond:06}.'
                                'log')
  _TOTAL_NUM_LOG_FILES = 10  # this is arbitrary

  def _MakeLogFile(self, timestamp, traceback=False):
    """Creates a fake log file, with optional crash data.

    Goes in the configured log directory.

    Args:
      timestamp: datetime.datetime, The date/time of the fake run.
      traceback: bool, whether to include a stack trace

    Returns:
      str, the path to the created log file
    """
    date_dir = os.path.join(
        config.Paths().logs_dir,
        self._TIMESTAMP_DIR_FORMAT.format(timestamp=timestamp))
    files.MakeDir(date_dir)
    contents = EXAMPLE_LOGS
    if traceback:
      contents += _GetExampleTraceback()
      contents += EXAMPLE_TRACEBACK_EPILOGUE
    return self.Touch(
        directory=date_dir,
        contents=contents,
        name=self._TIMESTAMP_LOG_NAME_FORMAT.format(timestamp=timestamp))

  def SetUp(self):
    self.StartPatch('datetime.datetime', _FakeDatetime)
    # Artisinally chosen value: This is 2 hours after the most recent log file
    # that we generate in the FeedbackTest. It lets us just check that we print
    # out "2 hours ago", "3 hours ago", etc.
    #
    # Why start at 2 hours instead of 1? It saves having to re-implement
    # pluralizing logic.
    #
    # We can set another datetime within a specific test to test the prompting
    # more thoroughly.
    _FakeDatetime.SetCurrentTime(datetime.datetime(1970, 1, 2, 11))
    def _ShouldIndexHaveTraceback(idx):
      """Returns whether the log file at the given index should be a crash log.

      This is arbitrary, but should fulfil the following requirements:
      * last index is False
      * at least one of the last NUM_RECENT_LOG_FILES should be a crash log

      Args:
        idx: int, the index of the log file in question

      Returns:
        bool, whether the log file should be a crash log
      """
      return idx != self._TOTAL_NUM_LOG_FILES - 1

    self.webbrowser_open = self.StartPatch('webbrowser.open')

    # List of all log files generated (except the "current" one)
    self.log_files = []
    # List of log file names that contain tracebacks
    self.log_files_traceback = []
    # Mapping of log file name to prompt choice,
    self.prompt_choices = {}

    for idx in range(self._TOTAL_NUM_LOG_FILES):
      traceback = _ShouldIndexHaveTraceback(idx)
      log_file = self._MakeLogFile(datetime.datetime(1970, 1, 2, idx),
                                   traceback=traceback)
      self.log_files.append(log_file)
      if traceback:
        self.log_files_traceback.append(log_file)

      if idx >= (self._TOTAL_NUM_LOG_FILES -
                 info_holder.LogsInfo.NUM_RECENT_LOG_FILES):
        item_number = self._TOTAL_NUM_LOG_FILES - idx
        self.prompt_choices[log_file] = item_number

    self.log_file_last = self.log_files[-1]
    assert self.log_file_last in self.prompt_choices
    assert self.log_file_last not in self.log_files_traceback
    self.log_file_traceback = self.log_files_traceback[-1]
    assert self.log_file_traceback in self.prompt_choices

    # The "current" log file (i.e. the one from the current run, which will be
    # the most recent).
    self.log_file_current = self._MakeLogFile(datetime.datetime(1970, 1, 3))
    self.nonexistent_file = self.RandomFileName()


class FeedbackTest(FeedbackTestBase):

  def _ExtractUrlParams(self):
    """Validate URL (from webbrowser.open call) and return its parameters."""
    self.assertTrue(self.webbrowser_open.called)
    (url, _), _ = self.webbrowser_open.call_args_list[0]
    self.assertLessEqual(len(url), feedback_util.MAX_URL_LENGTH)
    return urlparse.parse_qs(urlparse.urlsplit(url).query)

  def _AssertParamsCorrect(self, params, command=True, traceback=True):
    """Assert that the URL parameters contain the correct elements.

    The URL should contain the following parameters:
    * 'status': should always be 'New'
    * 'summary': should always be ''
    * 'comment': see below

    Comments are composed of the following:
    * Command information (optional)
    * Comment template (e.g. "What steps will reproduce"
    * Traceback information (optional)
    * Installation information

    This method is a utility for asserting that the comment does or does not
    contain each component as appropriate.

    Args:
      params: dict, return value of urlparse.parse_qs
      command: bool, whether the message about the command run should be
        included
      traceback: bool, whether the traceback should be included
    """
    self.assertEqual(params.get('component'), ['187143'])
    # urlparse.parse_qs with parse 'title=' to {} rather than {'title': ''}
    self.assertIsNone(params.get('title'))

    comment = params.get('description', [''])[0]

    self.assertRegexpMatches(comment,
                             r'WARNING: This is a PUBLIC issue tracker')
    self.assertRegexpMatches(comment, r'What steps will reproduce the problem?')
    self.assertRegexpMatches(comment, r'What is the expected output?')
    self.assertRegexpMatches(comment, r'What do you see instead?')
    self.assertRegexpMatches(comment,
                             r'Please provide any additional information below')

    def _GetAssertMethod(should_match):
      """Get the positive or negative form of assertRegexpMatches."""
      if should_match:
        return self.assertRegexpMatches
      else:
        return self.assertNotRegexpMatches

    command_assert = _GetAssertMethod(command)
    command_assert(comment, r'Issue running command \[gcloud auth list\]')

    traceback_assert = _GetAssertMethod(traceback)
    traceback_assert(comment, r'Trace:')
    # Make sure that these file paths have their common prefixes stripped
    traceback_assert(comment, r'\btest.py')
    traceback_assert(comment,
                     r'\b{0}'.format(
                         re.escape(os.path.join('bread', 'toast.py'))))
    traceback_assert(comment, r'Exception: really really long message')

    self.assertRegexpMatches(comment, r'Google Cloud SDK \[')
    self.assertRegexpMatches(comment, r'Platform: \[')
    # Check that anonymizer was on.
    self.assertRegexpMatches(comment, r'\$\{CLOUDSDK_CONFIG\}')

  def _AssertPromptDisplayed(self):
    """Assert that the "select log file" prompt displays the correct choices.

    * Should include suggestion of the NUM_RECENT_LOG_FILES most recent log
      files in reverse chronological order.
    * Should *not* include the most recent log file
    * Should include "(crash detected)" for each log file that includes a
      traceback
    * The final option should be "None of these"

    Example:

      Which recent gcloud invocation would you like to provide feedback
      about?
       [1] [gcloud auth list]: 1 hour ago
       [2] [gcloud auth list] (crash detected): 2 hours ago
       [3] [gcloud auth list] (crash detected): 3 hours ago
       [4] [gcloud auth list] (crash detected): 4 hours ago
       [5] [gcloud auth list] (crash detected): 5 hours ago
       [6] None of these
      Please enter your numeric choice (1):
    """
    self.AssertErrContains('Which recent gcloud invocation would you like')
    for log_file in self.log_files:
      item_number = self.prompt_choices.get(log_file)
      if item_number:  # log_file is displayed as a prompt choice
        # Have to escape {crash} because we're formatting in two rounds
        prompt_item_base = ('[gcloud auth list]{{crash}}: '
                            '{hours} hours ago').format(hours=item_number+1)

        if log_file in self.log_files_traceback:
          self.AssertErrContains(
              prompt_item_base.format(crash=' (crash detected)'))
        else:
          self.AssertErrContains(prompt_item_base.format(crash=''))
          self.AssertErrNotContains(prompt_item_base.format(
              crash=' (crash detected)'))
      else:
        self.AssertErrNotContains(os.path.basename(log_file))
    self.AssertErrNotContains(os.path.basename(self.log_file_current))

    # This constant indicates the number of recent log files to show. We want
    # one more, as that will be the "None of these" choice.
    none_choice = info_holder.LogsInfo.NUM_RECENT_LOG_FILES + 1
    self.AssertErrContains('[{0}] None of these'.format(none_choice))

  def _AssertPromptNotDisplayed(self):
    """Assert that the "select log file" prompt is not displayed."""
    self.AssertErrNotContains('Which recent gcloud invocation would you like')

  def testFeedbackNoLogFile(self):
    """Test behavior with 'None of these' option chosen.

    Key points:
    1. Prompt displayed
    2. Browser opened
    3. Pre-populated issue contains `gcloud info`, but not traceback or command
       run
    """
    # This is the return value of the "Which recent gcloud run" prompt
    # associated with the option "None of these [log files]".
    none_choice = info_holder.LogsInfo.NUM_RECENT_LOG_FILES
    self.StartPatch('googlecloudsdk.core.console.'
                    'console_io.PromptChoice').return_value = none_choice
    self.Run('feedback')

    self.AssertErrContains('Opening your browser to')
    self.AssertErrContains('No invocation selected. Would you still like to')

    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params, command=False, traceback=False)

  def testFeedbackMostRecent(self):
    """Test behavior with most recent log file chosen.

    Key points:
    1. Prompt displayed
    2. Browser opened
    3. Pre-populated issue contains `gcloud info` and command run, but not
       traceback
    """
    # The default prompt choice will be the most recent log file
    self.Run('feedback')

    self._AssertPromptDisplayed()
    self.AssertErrContains('Opening your browser to')

    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params, traceback=False)

  def testFeedbackMostRecentSpecifiedCommandLine(self):
    """Test behavior with most recent log file specified via command line.

    Key points:
    1. Prompt not displayed
    2. Browser opened
    3. Pre-populated issue contains `gcloud info` and command run, but not
       traceback
    """
    self.Run('feedback --log-file {0}'.format(self.log_file_last))

    self._AssertPromptNotDisplayed()
    self.AssertErrContains('Opening your browser to')

    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params, traceback=False)

  def testFeedbackLogFileTraceback(self):
    """Test behavior with log of crashed run chosen.

    Key points:
    1. Browser opened
    2. Pre-populated issue contains `gcloud info`, command run, and traceback

    (The prompt should normally be displayed, but here we mock it out.)
    """
    prompt_mock = self.StartPatch('googlecloudsdk.core.console.'
                                  'console_io.PromptChoice')
    prompt_mock.return_value = self.prompt_choices[self.log_file_traceback]
    self.Run('feedback')

    self.AssertErrContains('Opening your browser to')

    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params)

  def testFeedbackLogFileTracebackSpecifiedCommandLine(self):
    """Test behavior with log of crashed run specified via command line.

    Key points:
    1. Prompt not displayed
    2. Browser opened
    3. Pre-populated issue contains `gcloud info`, command run, and traceback

    (The prompt should normally be displayed, but here we mock it out.)
    """
    self.Run('feedback --log-file {0}'.format(self.log_file_traceback))

    self._AssertPromptNotDisplayed()
    self.AssertErrContains('Opening your browser to')

    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params)

  def testFeedbackBadLogFile(self):
    """Test behavior with non-existent log file specified.

    Key points:
    1. Warning message displayed
    2. Prompt displayed
    3. Browser opened
    4. Pre-populated issue contains `gcloud info` and command run, but not
       traceback
    """
    self.Run('feedback --log-file {0}'.format(self.nonexistent_file))

    self.AssertErrContains('Error reading the specified file')
    self.AssertErrContains(self.nonexistent_file)

    self._AssertPromptDisplayed()
    self.AssertErrContains('Opening your browser to')
    params = self._ExtractUrlParams()
    self._AssertParamsCorrect(params, traceback=False)

  def testFeedbackLongUrl(self):
    """Test behavior when `gcloud info` is too long to fit in the URL.

    Key points:
    1. Prompt displayed
    2. Message about issue pre-populating the form
    3. (Only the) truncated output included in STDOUT
    4. Browser opened (URL length less than max)
    5. Pre-populated issue contains the beginning (but not end) of the info.
    """
    self.StartObjectPatch(info_holder.InfoHolder, '__str__').return_value = (
        'Google Cloud SDK [test]\nPlatform: [test]\n'
        'User Config Directory: [${CLOUDSDK_CONFIG}]' +
        'This is a test line. This is a test line.\n' * 1000 +
        'end')

    self.Run('feedback')

    self._AssertPromptDisplayed()
    self.AssertErrContains('Opening your browser to')

    self.AssertErrContains('The output of gcloud info is too long to '
                           'pre-populate the new issue form.')
    self.AssertErrContains('Truncating included information.')
    self.AssertErrContains('Please consider including the remainder:')
    self.AssertErrContains('end')
    self.AssertErrContains('This is a test line.')
    self.AssertErrNotContains('Google Cloud SDK [test]')
    self.AssertErrNotContains('Platform: [test]')

    params = self._ExtractUrlParams()  # this also checks the URL length
    self._AssertParamsCorrect(params, traceback=False)
    description = params.get('description', [''])[0]
    self.assertRegexpMatches(description, r'This is a test line.')
    self.assertRegexpMatches(description, r'\[output truncated\]')
    self.assertNotRegexpMatches(description, r'end')

  def testFeedbackPromptFormat(self):
    # Set up some fake log files so we can exercise the prompt format more
    # thoroughly.
    log_files = [
        mock.Mock(),
        mock.Mock(),
        mock.Mock()
    ]
    # See https://docs.python.org/3/library/unittest.mock.html section on
    # unittest.mock.PropertyMock:
    type(log_files[0]).command = mock.PropertyMock(return_value='gcloud foo')
    type(log_files[1]).command = mock.PropertyMock(return_value='gcloud bar')
    type(log_files[2]).command = mock.PropertyMock(return_value='gcloud baz')
    log_files[0].traceback = 'traceback'
    log_files[1].traceback = None
    log_files[2].traceback = None
    # Set the fake current time so that we can inspect it closer
    _FakeDatetime.SetCurrentTime(datetime.datetime(1970, 1, 1, 2))
    # See https://docs.python.org/3/library/unittest.mock.html section on
    # unittest.mock.PropertyMock:
    type(log_files[0]).date = mock.PropertyMock(
        return_value=datetime.datetime(1970, 1, 1, 1, 59, 30))
    type(log_files[1]).date = mock.PropertyMock(
        return_value=datetime.datetime(1970, 1, 1, 1, 30))
    # Test the unparseable filename scenario
    type(log_files[2]).date = mock.PropertyMock(return_value=None)

    self.StartObjectPatch(info_holder.LogsInfo, 'GetRecentRuns',
                          return_value=log_files)

    self.Run('feedback')
    self.AssertErrContains('[gcloud foo] (crash detected): 30 seconds ago')
    self.AssertErrContains('[gcloud bar]: 30 minutes ago')
    self.AssertErrContains('[gcloud baz]: Unknown time')


class FeedbackQuietTest(FeedbackTestBase):

  def testFeedbackQuiet(self):
    self.Run('feedback --quiet')
    self.AssertOutputContains('Stack Overflow')
    self.AssertOutputContains(STACKOVERFLOW_URL)

    self.AssertOutputContains('groups page')
    self.AssertOutputContains(GROUPS_PAGE_URL)
    self.AssertOutputContains(GROUPS_EMAIL)
    self.AssertOutputContains('IRC')
    self.AssertOutputContains(IRC_CHANNEL)

    self.AssertOutputContains('issue tracker')
    self.AssertOutputContains(ISSUE_TRACKER_URL)

    self.AssertOutputContains('Please include the following information when '
                              'filing a bug report')
    self.AssertOutputContains('Google Cloud SDK [')
    self.AssertOutputContains('Platform: [')
    self.AssertOutputContains('Last Log File:')
    # Check that anonymizer was on.
    self.assertRegexpMatches(self.GetOutput(), r'\$\{CLOUDSDK_CONFIG\}')

  def testFeedbackQuietBadLogFile(self):
    self.Run('feedback --quiet --log-file {0}'.format(self.nonexistent_file))

    self.AssertErrContains('Error reading the specified file')
    self.AssertErrContains(self.nonexistent_file)

    self.AssertOutputContains('issue tracker')
    self.AssertOutputContains('Please include the following information when '
                              'filing a bug report')
    self.AssertOutputContains('Google Cloud SDK [')

  def testFeedbackQuietLogFile(self):
    self.Run('feedback --quiet --log-file {0}'.format(self.log_file_last))

    self.AssertOutputContains(self.log_file_last)
    self.AssertOutputContains('issue tracker')
    self.AssertOutputContains('Please include the following information when '
                              'filing a bug report')
    self.AssertOutputContains('Google Cloud SDK [')

  def testFeedbackQuietLogFileTraceback(self):
    self.Run('feedback --quiet --log-file {0}'.format(self.log_file_traceback))

    self.AssertOutputNotContains(EXAMPLE_LOGS)
    self.AssertOutputContains(
        _GetExampleTraceback().replace('BEGIN CRASH STACKTRACE\n', ''))
    self.AssertOutputNotContains('BEGIN CRASH STACKTRACE')
    self.AssertErrNotContains(EXAMPLE_TRACEBACK_EPILOGUE)
    self.AssertOutputContains('issue tracker')
    self.AssertOutputContains('Please include the following information when '
                              'filing a bug report')
    self.AssertOutputContains('Google Cloud SDK [')
    self.AssertOutputContains('Platform: [')


class CommonPrefixTest(unittest.TestCase):

  def testCommonPrefixEmpty(self):
    self.assertEqual(feedback_util._CommonPrefix([
        ]), '')

  @test_case.Filters.DoNotRunOnWindows
  def testCommonPrefixSameDir(self):
    self.assertEqual(feedback_util._CommonPrefix([
        '/path/to/test.py',
        '/path/to/test2.py',
        ]), '/path/to/')

  @test_case.Filters.DoNotRunOnWindows
  def testCommonPrefixDifferentDirs(self):
    self.assertEqual(feedback_util._CommonPrefix([
        '/path/to/test.py',
        '/path/test2.py',
        ]), '/path/')

  @test_case.Filters.DoNotRunOnWindows
  def testCommonPrefixSameFile(self):
    self.assertEqual(feedback_util._CommonPrefix([
        '/path/to/test.py',
        '/path/to/test.py',
        ]), '/path/to/')

  @test_case.Filters.RunOnlyOnWindows
  def testCommonPrefixSameDirWindows(self):
    self.assertEqual(feedback_util._CommonPrefix([
        'C:\\path\\to\\test.py',
        'C:\\path\\to\\test2.py',
        ]), 'C:\\path\\to\\')

  @test_case.Filters.RunOnlyOnWindows
  def testCommonPrefixDifferentDirsWindows(self):
    self.assertEqual(feedback_util._CommonPrefix([
        'C:\\path\\to\\test.py',
        'C:\\path\\test2.py',
        ]), 'C:\\path\\')

  @test_case.Filters.RunOnlyOnWindows
  def testCommonPrefixSameFileWindows(self):
    self.assertEqual(feedback_util._CommonPrefix([
        'C:\\path\\to\\test.py',
        'C:\\path\\to\\test.py',
        ]), 'C:\\path\\to\\')


class FormatTracebackTest(test_case.TestCase):

  _EXAMPLE_TRACEBACK_UNIX = textwrap.dedent("""\
  Traceback (most recent call last):
    File "/path/to/cloudsdk/test.py", line 3, in <module>
      main()
    File "/path/to/cloudsdk/./test.py", line 2, in main
      example.method()
    File "/path/to/cloudsdk/lib/example.py", line 70, in method
      a = b + foo.Bar()
    File "/path/to/cloudsdk/lib/googlecloudsdk/foo.py", line 700, in bar
      c.function()
    File "/path/to/cloudsdk/lib/third_party/bread/toast.py", line 1, in function
      raise Exception('really quite a fantastically, exceptionally, particularly long message')
  Exception: really quite a fantastically, exceptionally, particularly long message\
""")

  _EXAMPLE_TRACEBACK_WINDOWS = textwrap.dedent("""\
  Traceback (most recent call last):
    File "C:\\Program Files (x86)\\cloudsdk\\test.py", line 3, in <module>
      main()
    File "C:\\Program Files (x86)\\cloudsdk\\.\\test.py", line 2, in main
      example.method()
    File "C:\\Program Files (x86)\\cloudsdk\\lib\\example.py", line 70, in method
      a = b + foo.Bar()
    File "C:\\Program Files (x86)\\cloudsdk\\lib\\googlecloudsdk\\foo.py", line 700, in bar
      c.function()
    File "C:\\Program Files (x86)\\cloudsdk\\lib\\third_party\\bread\\toast.py", line 1, in function
      raise Exception('really quite a fantastically, exceptionally, particularly long message')
  Exception: really quite a fantastically, exceptionally, particularly long message\
""")

  def testFormatTraceback_UnixPathSep(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    expected_formatted_stacktrace = textwrap.dedent("""\
        test.py:3
         main()
        test.py:2
         example.method()
        lib/example.py:70
         a = b + foo.Bar()
        foo.py:700
         c.function()
        bread/toast.py:1
         raise Exception('really quite a fantastically, exceptionally, particularly long ...
         """)
    self.assertEqual(
        (expected_formatted_stacktrace,
         'Exception: really quite a fantastically, exceptionally, '
         'particularly long message'),
        feedback_util._FormatTraceback(self._EXAMPLE_TRACEBACK_UNIX))

  def testFormatTraceback_WindowsPathSep(self):
    self.StartObjectPatch(os.path, 'sep', ntpath.sep)
    self.StartObjectPatch(os.path, 'dirname', ntpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', ntpath.commonprefix)
    expected_formatted_stacktrace = textwrap.dedent("""\
        test.py:3
         main()
        test.py:2
         example.method()
        lib\\example.py:70
         a = b + foo.Bar()
        foo.py:700
         c.function()
        bread\\toast.py:1
         raise Exception('really quite a fantastically, exceptionally, particularly long ...
         """)
    self.assertEqual(
        (expected_formatted_stacktrace,
         'Exception: really quite a fantastically, exceptionally, '
         'particularly long message'),
        feedback_util._FormatTraceback(self._EXAMPLE_TRACEBACK_WINDOWS))

  def testFormatTraceback_DontMessWithUnderscoreLib(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    traceback = textwrap.dedent("""\
        Traceback (most recent call last):
          File "/foo/api_lib/third_party/example.py", line 14, in Foo
            method()
          File "/path/to/cloudsdk/core/api_lib/third_party/example.py", line 70, in method
            a = b + foo.Bar()
          File "/path/to/cloudsdk/lib/third_party/foo.py", line 100, in Bar
            raise Exception('really quite a fantastically, exceptionally, particularly long message')
        Exception: really quite a fantastically, exceptionally, particularly long message\
""")
    expected_formatted_stacktrace = textwrap.dedent("""\
        /foo/api_lib/third_party/example.py:14
         method()
        /path/to/cloudsdk/core/api_lib/third_party/example.py:70
         a = b + foo.Bar()
        /path/to/cloudsdk/foo.py:100
         raise Exception('really quite a fantastically, exceptionally, particularly long ...
         """)
    self.assertEqual(
        (expected_formatted_stacktrace,
         'Exception: really quite a fantastically, exceptionally, '
         'particularly long message'),
        feedback_util._FormatTraceback(traceback))

  def testFormatTraceback_DontMessWithUnderscoreLib_CommonPrefix(self):
    self.StartObjectPatch(os.path, 'sep', posixpath.sep)
    self.StartObjectPatch(os.path, 'dirname', posixpath.dirname)
    self.StartObjectPatch(os.path, 'commonprefix', posixpath.commonprefix)
    traceback = textwrap.dedent("""\
        Traceback (most recent call last):
          File "/path/to/cloudsdk/core/api_lib/third_party/example.py", line 70, in method
            a = b + foo.Bar()
          File "/path/to/cloudsdk/lib/third_party/foo.py", line 100, in Bar
            raise Exception('really quite a fantastically, exceptionally, particularly long message')
        Exception: really quite a fantastically, exceptionally, particularly long message
""")
    expected_formatted_stacktrace = textwrap.dedent("""\
        core/api_lib/third_party/example.py:70
         a = b + foo.Bar()
        foo.py:100
         raise Exception('really quite a fantastically, exceptionally, particularly long ...
        """)
    self.assertEqual(
        (expected_formatted_stacktrace,
         'Exception: really quite a fantastically, exceptionally, '
         'particularly long message'),
        feedback_util._FormatTraceback(traceback))


class ShortenStacktraceTest(unittest.TestCase):

  STACKTRACE = '  ' + textwrap.dedent("""\
          File "a.py", line 1, in run
              result = b.run()
            File "b.py", line 2, in run
              result = c.run()
            File "c.py", line 3, in run
              result = d.run()
            File "d.py", line 4, in run
              raise Exception(':(')
          """)

  def testMaxLengthVeryShort(self):
    self.assertEqual(
        feedback_util._ShortenStacktrace(self.STACKTRACE, 1),
        '  ' + textwrap.dedent("""\
          File "a.py", line 1, in run
              result = b.run()
            [...]
            File "d.py", line 4, in run
              raise Exception(':(')
          """))

  def testMaxLengthMiddle(self):
    self.assertEqual(
        feedback_util._ShortenStacktrace(self.STACKTRACE, 250),
        '  ' + textwrap.dedent("""\
          File "a.py", line 1, in run
              result = b.run()
            [...]
            File "c.py", line 3, in run
              result = d.run()
            File "d.py", line 4, in run
              raise Exception(':(')
          """))

  def testMaxLengthLongEnough(self):
    self.assertEqual(
        feedback_util._ShortenStacktrace(self.STACKTRACE, 1000),
        '  ' + textwrap.dedent("""\
          File "a.py", line 1, in run
              result = b.run()
            File "b.py", line 2, in run
              result = c.run()
            File "c.py", line 3, in run
              result = d.run()
            File "d.py", line 4, in run
              raise Exception(':(')
           """))


class ShortenIssueBodyTest(unittest.TestCase):

  FORMATTED_STACKTRACE = textwrap.dedent("""\
      gcloud_main.py:169
       gcloud_cli.Execute()
      a.py:1
       import b; b.run()
      b.py:1
       import c; c.run()
      c.py:1
       import d; d.run()
      d.py:28
       raise Exception(':(')
      """)

  EXCEPTION = 'Exception: :('

  ISSUE_BODY = textwrap.dedent("""\
      WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
      information in the report you file. In order to help diagnose the issue,
      we've included some installation information in this report. Please look
      through and redact any information you consider personal or sensitive
      before submitting this issue.

      Issue running command [gcloud error].

      What steps will reproduce the problem?


      What is the expected output? What do you see instead?


      Please provide any additional information below.


      Trace:
      gcloud_main.py:169
       gcloud_cli.Execute()
      a.py:1
       import b; b.run()
      b.py:1
       import c; c.run()
      c.py:1
       import d; d.run()
      d.py:28
       raise Exception(':(')
      Exception: :(

      Installation information:

      Google Cloud SDK [93.0.0]

      Platform: [Linux, x86_64]
      Python Version: [2.7.6 (default, Jun 22 2015, 17:58:13)  [GCC 4.8.2]]
      Python Location: [None]
      Site Packages: [Enabled]

      Installation Root: [/tmp/google-cloud-sdk]
      System PATH: [/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin]
      Cloud SDK on PATH: [False]

      Installation Properties: [None]
      User Config Directory: [/home/user/.config/gcloud]
      User Properties: [/home/user/.config/gcloud/properties]
      Current Workspace: [None]
      Workspace Config Directory: [None]
      Workspace Properties: [None]
      """)

  PRE_STACKTRACE = textwrap.dedent("""\
      WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
      information in the report you file. In order to help diagnose the issue,
      we've included some installation information in this report. Please look
      through and redact any information you consider personal or sensitive
      before submitting this issue.

      Issue running command [gcloud error].

      What steps will reproduce the problem?


      What is the expected output? What do you see instead?


      Please provide any additional information below.


      """)

  COMMENT = feedback_util.CommentHolder(ISSUE_BODY, PRE_STACKTRACE,
                                        FORMATTED_STACKTRACE, EXCEPTION)

  def testFitFullBody(self):
    self.assertEqual(feedback_util._ShortenIssueBody(self.COMMENT, 10000),
                     (self.ISSUE_BODY, ''))

  def testFitFullStacktrace(self):
    self.assertEqual(
        feedback_util._ShortenIssueBody(self.COMMENT, 1350),
        (textwrap.dedent("""\
             WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
             information in the report you file. In order to help diagnose the issue,
             we've included some installation information in this report. Please look
             through and redact any information you consider personal or sensitive
             before submitting this issue.

             Issue running command [gcloud error].

             What steps will reproduce the problem?


             What is the expected output? What do you see instead?


             Please provide any additional information below.


             Trace:
             gcloud_main.py:169
              gcloud_cli.Execute()
             a.py:1
              import b; b.run()
             b.py:1
              import c; c.run()
             c.py:1
              import d; d.run()
             d.py:28
              raise Exception(':(')
             Exception: :(

             Installation information:

             Google Cloud SDK [93.0.0]

             Platform: [Linux, x86_64]
             Python Version: [2.7.6 (default, Jun 22 2015, 17:58:13)  [GCC 4.8.2]]
             Python Location: [None]
             Site Packages: [Enabled]

             Installation Root: [/tmp/google-cloud-sdk]
             System PATH: [/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin]
             Cloud SDK on PATH: [False]

             [output truncated]"""),
         textwrap.dedent("""\
             Installation Properties: [None]
             User Config Directory: [/home/user/.config/gcloud]
             User Properties: [/home/user/.config/gcloud/properties]
             Current Workspace: [None]
             Workspace Config Directory: [None]
             Workspace Properties: [None]
             """)))

  def testCannotFitFullStacktrace(self):
    self.assertEqual(
        feedback_util._ShortenIssueBody(self.COMMENT, 800),
        (textwrap.dedent("""\
             WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
             information in the report you file. In order to help diagnose the issue,
             we've included some installation information in this report. Please look
             through and redact any information you consider personal or sensitive
             before submitting this issue.

             Issue running command [gcloud error].

             What steps will reproduce the problem?


             What is the expected output? What do you see instead?


             Please provide any additional information below.


             Trace:
             gcloud_main.py:169
              gcloud_cli.Execute()
               [...]
             c.py:1
              import d; d.run()
             d.py:28
              raise Exception(':(')
             Exception: :(
             [output truncated]"""),
         textwrap.dedent("""\
             Full stack trace (formatted):
             gcloud_main.py:169
              gcloud_cli.Execute()
             a.py:1
              import b; b.run()
             b.py:1
              import c; c.run()
             c.py:1
              import d; d.run()
             d.py:28
              raise Exception(':(')
             Exception: :(

             Installation information:

             Google Cloud SDK [93.0.0]

             Platform: [Linux, x86_64]
             Python Version: [2.7.6 (default, Jun 22 2015, 17:58:13)  [GCC 4.8.2]]
             Python Location: [None]
             Site Packages: [Enabled]

             Installation Root: [/tmp/google-cloud-sdk]
             System PATH: [/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin]
             Cloud SDK on PATH: [False]

             Installation Properties: [None]
             User Config Directory: [/home/user/.config/gcloud]
             User Properties: [/home/user/.config/gcloud/properties]
             Current Workspace: [None]
             Workspace Config Directory: [None]
             Workspace Properties: [None]
             """)))

  def testCannotFitEvenShortenedStacktrace(self):
    self.assertEqual(
        feedback_util._ShortenIssueBody(self.COMMENT, 685),
        (textwrap.dedent("""\
             WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
             information in the report you file. In order to help diagnose the issue,
             we've included some installation information in this report. Please look
             through and redact any information you consider personal or sensitive
             before submitting this issue.

             Issue running command [gcloud error].

             What steps will reproduce the problem?


             What is the expected output? What do you see instead?


             Please provide any additional information below.


             Trace:
             gcloud_main.py:169
              gcloud_cli.Execute()
             a.py:1
             [output truncated]"""),
         textwrap.dedent("""\
             Full stack trace (formatted):
             gcloud_main.py:169
              gcloud_cli.Execute()
             a.py:1
              import b; b.run()
             b.py:1
              import c; c.run()
             c.py:1
              import d; d.run()
             d.py:28
              raise Exception(':(')
             Exception: :(

             Installation information:

             Google Cloud SDK [93.0.0]

             Platform: [Linux, x86_64]
             Python Version: [2.7.6 (default, Jun 22 2015, 17:58:13)  [GCC 4.8.2]]
             Python Location: [None]
             Site Packages: [Enabled]

             Installation Root: [/tmp/google-cloud-sdk]
             System PATH: [/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin]
             Cloud SDK on PATH: [False]

             Installation Properties: [None]
             User Config Directory: [/home/user/.config/gcloud]
             User Properties: [/home/user/.config/gcloud/properties]
             Current Workspace: [None]
             Workspace Config Directory: [None]
             Workspace Properties: [None]
             """)))


if __name__ == '__main__':
  test_case.main()
