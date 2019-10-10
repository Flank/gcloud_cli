# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Unit tests for parallel Google Cloud Storage operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import getpass
import os

from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files as file_utils
from tests.lib import sdk_test_base
from tests.lib import test_case


LOG_NO_CRASH = """\
2016-11-03 19:27:29,982 DEBUG    root            Loaded Command Group: ['gcloud', 'meta']
2016-11-03 19:27:30,014 DEBUG    root            Loaded Command Group: ['gcloud', 'meta', 'debug']
2016-11-03 19:27:30,015 DEBUG    root            Running [gcloud.meta.debug] with arguments: []
2016-11-03 19:28:55,883 INFO     root            Display format "default".
2016-11-03 19:28:55,895 DEBUG    root            Checking for updates...
2016-11-03 19:28:56,125 DEBUG    root            Updating notification cache...
2016-11-03 19:28:56,125 DEBUG    root            Activating notification: [default]
2016-11-03 19:28:56,139 DEBUG    root            Metrics reporting process started...
"""
LOG_CRASH = """\
2016-12-01 13:42:36,250 DEBUG    root            Loaded Command Group: ['gcloud', 'version']
2016-12-01 13:42:36,251 DEBUG    root            Running [gcloud.version] with arguments: []
2016-12-01 13:42:36,251 DEBUG    root            :(
Traceback (most recent call last):
  File "/home/user/googlecloudsdk/calliope/cli.py", line 740, in Execute
    resources = args.calliope_command.Run(cli=self, args=args)
  File "/home/user/googlecloudsdk/calliope/backend.py", line 1648, in Run
    resources = command_instance.Run(args)
  File "/home/user/googlecloudsdk/surface/version.py", line 33, in Run
    raise Exception(':(')
Exception: :(
2016-12-01 13:42:36,252 ERROR    ___FILE_ONLY___ BEGIN CRASH STACKTRACE
Traceback (most recent call last):
  File "/home/user/googlecloudsdk/gcloud_main.py", line 130, in main
    gcloud_cli.Execute()
  File "/home/user/googlecloudsdk/calliope/cli.py", line 762, in Execute
    self._HandleAllErrors(exc, command_path_string, flag_collection)
  File "/home/user/googlecloudsdk/calliope/cli.py", line 740, in Execute
    resources = args.calliope_command.Run(cli=self, args=args)
  File "/home/user/googlecloudsdk/calliope/backend.py", line 1648, in Run
    resources = command_instance.Run(args)
  File "/home/user/googlecloudsdk/surface/version.py", line 33, in Run
    raise Exception(':(')
Exception: :(
2016-12-01 13:42:36,253 ERROR    root            gcloud crashed (Exception): :(
2016-12-01 13:42:36,253 INFO     ___FILE_ONLY___
If you would like to report this issue, please run the following command:

2016-12-01 13:42:36,253 INFO     ___FILE_ONLY___   gcloud feedback

2016-12-01 13:42:36,253 INFO     ___FILE_ONLY___
To check gcloud for common problems, please run the following command:

2016-12-01 13:42:36,253 INFO     ___FILE_ONLY___   gcloud info --run-diagnostics
"""
TRACEBACK_LOG = """\
Traceback (most recent call last):
  File "/home/user/googlecloudsdk/gcloud_main.py", line 130, in main
    gcloud_cli.Execute()
  File "/home/user/googlecloudsdk/calliope/cli.py", line 762, in Execute
    self._HandleAllErrors(exc, command_path_string, flag_collection)
  File "/home/user/googlecloudsdk/calliope/cli.py", line 740, in Execute
    resources = args.calliope_command.Run(cli=self, args=args)
  File "/home/user/googlecloudsdk/calliope/backend.py", line 1648, in Run
    resources = command_instance.Run(args)
  File "/home/user/googlecloudsdk/surface/version.py", line 33, in Run
    raise Exception(':(')
Exception: :(\
"""


class LogDataTest(test_case.Base):

  _DATE = datetime.datetime(2016, 11, 3, 19, 28, 56)
  # Note: if this changes, be very careful that this LogData class can handle
  # old log filename formats.
  _DIR_NAME = '2016.11.03'
  _LOG_FILE_NAME = '19.28.56.000000.log'
  _RELATIVE_PATH = os.path.join(_DIR_NAME, _LOG_FILE_NAME)

  def SetUp(self):
    temp_dir = file_utils.TemporaryDirectory()
    self.addCleanup(temp_dir.Close)
    self.temp_path = temp_dir.path
    self.paths_mock = self.StartObjectPatch(config, 'Paths').return_value
    self.paths_mock.logs_dir = self.temp_path

  def _WriteLogFile(self, contents=LOG_NO_CRASH, dir_name=None, path=None):
    """Write a log file.

    Args:
      contents: str, the contents of the file to write. Defaults to the
        LOG_NO_CRASH hardcoded string.
      dir_name: str or None, the name of the directory for the log file to go
        into (within the test temp directory). By default, uses the log module
        date format.
      path: str or None, the name of the path within dir_name for the log file
        to be written to. By default, uses the log module time format.

    Returns:
      str, the full path of the file that was written
    """
    dir_name = dir_name or self._DATE.strftime(log.DAY_DIR_FORMAT)
    path = path or (self._DATE.strftime(log.FILENAME_FORMAT) +
                    log.LOG_FILE_EXTENSION)

    return self.Touch(os.path.join(self.temp_path, dir_name), path,
                      contents=contents, makedirs=True)

  def _AssertLogData(self, log_data, filename, relative_path=None, date=None,
                     command='gcloud meta debug', contents=LOG_NO_CRASH,
                     traceback=None):
    relative_path = relative_path or self._RELATIVE_PATH

    self.assertEqual(log_data.filename, filename)
    self.assertEqual(log_data.relative_path, relative_path)
    self.assertEqual(log_data.date, date)
    self.assertEqual(log_data.command, command)
    self.assertEqual(log_data.contents, contents)
    self.assertEqual(log_data.traceback, traceback)

  def testFromFile_NoCrash(self):
    log_path = self._WriteLogFile()

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(log_data, filename=log_path, date=self._DATE)
    self.assertEqual(str(log_data),
                     '[{}]: [gcloud meta debug]'.format(self._RELATIVE_PATH))

  def testFromFile_HyphenCommand(self):
    modified_log_contents = LOG_NO_CRASH.replace('meta', 'm-e-t-a')
    log_path = self._WriteLogFile(modified_log_contents)

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(
        log_data, filename=log_path, date=self._DATE,
        command='gcloud m-e-t-a debug', contents=modified_log_contents)
    self.assertEqual(
        str(log_data),
        '[{}]: [gcloud m-e-t-a debug]'.format(self._RELATIVE_PATH))

  def testFromFile_BadDirName(self):
    """Test case where a log directory name is not in YYYY.MM.DD format."""
    log_path = self._WriteLogFile(dir_name='bad-dir')

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(
        log_data, filename=log_path,
        relative_path=os.path.join('bad-dir', self._LOG_FILE_NAME), date=None)

  def testFromFile_BadFilename(self):
    """Test case where a log file name is not in HH.MM.SS.FFFFFF.log format."""
    log_path = self._WriteLogFile(path='bad-file')

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(
        log_data, filename=log_path,
        relative_path=os.path.join(self._DIR_NAME, 'bad-file'), date=None)

  def testFromFile_NotInLogsDir(self):
    self.paths_mock.logs_dir = 'imaginary-path'
    log_path = self._WriteLogFile()

    log_data = info_holder.LogData.FromFile(log_path)

    # When filename isn't in config.Paths().logs_dir, expected behavior is to
    # return the full filename for relative_path
    self._AssertLogData(log_data, filename=log_path, relative_path=log_path)

  def testFromFile_NotInLogsDirNone(self):
    self.paths_mock.logs_dir = None
    log_path = self._WriteLogFile()

    log_data = info_holder.LogData.FromFile(log_path)

    # When filename isn't in config.Paths().logs_dir, expected behavior is to
    # return the full filename
    self._AssertLogData(log_data, filename=log_path, relative_path=log_path)

  def testFromFile_NotInLogsDirTricky(self):
    """Tests case where the filename *starts* with logs_dir but isn't *in* it.

    Previous versions had a bug with this.

    Example:
      logs_dir: '/tmp/f'
      filename: '/tmp/foo/bar'
    """
    # os.path.normpath removes file separator, if present.
    norm_path = os.path.normpath(self.temp_path)
    # Check that the basename of temp_path has length >1; not technically
    # assured by the API but I think pretty reasonable.
    self.assertGreater(
        len(os.path.basename(norm_path)), 1,
        ('ERROR: For this test to work, self.temp_path must have a basename of '
         'length >1.'))
    # We want to lop off 1 char from the temp path to get the tricky prefix
    # This makes logs_dir a prefix of log_path, but *not* a parent.
    self.paths_mock.logs_dir = norm_path[:-1]
    log_path = self._WriteLogFile()

    log_data = info_holder.LogData.FromFile(log_path)

    # When filename isn't in config.Paths().logs_dir, expected behavior is to
    # return the full filename for relative_path
    self._AssertLogData(log_data, filename=log_path, relative_path=log_path)

  def testFromFile_Crash(self):
    log_path = self._WriteLogFile(contents=LOG_CRASH)

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(log_data, filename=log_path, date=self._DATE,
                        command='gcloud version', contents=LOG_CRASH,
                        traceback=TRACEBACK_LOG)
    self.assertEqual(
        str(log_data),
        '[{}]: [gcloud version] (crash detected)'.format(self._RELATIVE_PATH))

  def testFromFile_Empty(self):
    log_path = self._WriteLogFile(contents='')

    log_data = info_holder.LogData.FromFile(log_path)

    self._AssertLogData(log_data, filename=log_path, date=self._DATE,
                        command=None, contents='')
    self.assertEqual(str(log_data),
                     '[{}]: [None]'.format(self._RELATIVE_PATH))


class AnonymizerTest(sdk_test_base.SdkBase):

  def SetUp(self):
    self.anonymizer = info_holder.Anonymizer()

  def testProcessConfigPath(self):
    cfg_paths = config.Paths()
    self.assertEqual(
        os.path.join('${CLOUDSDK_CONFIG}', 'some', 'dir', 'in', 'config'),
        self.anonymizer.ProcessPath(
            os.path.join(cfg_paths.global_config_dir,
                         'some', 'dir', 'in', 'config')))

  def testProcessFakeHomePath(self):
    home_path = file_utils.GetHomeDir() + '_other'
    self.assertEqual('${HOME}_other', self.anonymizer.ProcessPath(home_path))

  def testProcessHomePath(self):
    self.assertEqual(
        '${HOME}',
        self.anonymizer.ProcessPath(file_utils.GetHomeDir()))

  def testProcessHomePath_NonNormalized(self):
    self.assertEqual(
        '${HOME}',
        self.anonymizer.ProcessPath(
            os.path.join(file_utils.GetHomeDir(), 'tmp', '..')))

  def testProcessPathWithUser(self):
    self.assertEqual(
        os.path.join('path', 'to', '${USER}'),
        self.anonymizer.ProcessPath(
            os.path.join('path', 'to', getpass.getuser())))

  def testProcessNullPath(self):
    self.assertIsNone(self.anonymizer.ProcessPath(None))

  def testNonMatchingPath(self):
    path = os.path.join('path', 'to', 'nowhere')
    self.assertEqual(path, self.anonymizer.ProcessPath(path))

  def testProcessFakeHomeFileURI(self):
    home_uri = 'file://' + file_utils.GetHomeDir() + '_other'
    self.assertEqual(
        'file://${HOME}_other',
        self.anonymizer.ProcessURL(home_uri))

  def testProcessHomeFileURI(self):
    self.assertEqual(
        'file://${HOME}',
        self.anonymizer.ProcessURL('file://' + file_utils.GetHomeDir()))

  def testProcessHomeFileURI_NonNormalized(self):
    self.assertEqual(
        'file://${HOME}',
        self.anonymizer.ProcessURL(
            os.path.join('file://' + file_utils.GetHomeDir(), 'tmp', '..')))

  def testProcessFileURIWithUser(self):
    self.assertEqual(
        os.path.join('file://path', 'to', '${USER}'),
        self.anonymizer.ProcessURL(
            os.path.join('file://path', 'to', getpass.getuser())))

  def testProcessNullURL(self):
    self.assertIsNone(self.anonymizer.ProcessURL(None))

  def testNonMatchingFileURI(self):
    uri = os.path.join('file://path', 'to', 'nowhere')
    self.assertEqual(uri, self.anonymizer.ProcessURL(uri))

  def testProcessRegularURL(self):
    url = 'http://www.test.com/'
    self.assertEqual(url, self.anonymizer.ProcessURL(url))

if __name__ == '__main__':
  test_case.main()
