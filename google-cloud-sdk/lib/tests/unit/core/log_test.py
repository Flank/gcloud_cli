# -*- coding: utf-8 -*-

# Copyright 2013 Google Inc. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import unicode_literals
import datetime
import io
import logging
import os
import time

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import times
from tests.lib import sdk_test_base
from tests.lib import test_case

import mock
import six


class LoggingConfigTest(sdk_test_base.WithOutputCapture):
  """Tests basic configuration of core logger."""

  def SetUp(self):
    self.logs_dir = self.temp_path

  def TearDown(self):
    log.Reset()

  def GetLogFileContents(self):
    """Makes sure a single log file was created and gets its contents.

    Raises:
      ValueError: If more than one log directory or file is found.

    Returns:
      str, The contents of the log file.
    """
    sub_dirs = os.listdir(self.logs_dir)
    if len(sub_dirs) != 1:
      raise ValueError('Found more than one log directory')
    sub_dir = os.path.join(self.logs_dir, sub_dirs[0])
    log_files = os.listdir(sub_dir)
    if len(log_files) != 1:
      raise ValueError('Found more than one log file')
    contents = io.open(os.path.join(sub_dir, log_files[0]),
                       encoding='utf8').read()
    return contents

  def testBasicSetupInit(self):
    """Tests that all basic logging and logging levels work."""
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    log.AddFileLogging(self.logs_dir)

    log.debug('c1')
    log.info('c2')
    log.error('c3')

    log.file_only_logger.debug('f1')
    log.file_only_logger.info('f2')
    log.file_only_logger.error('f3')

    log.out.write('o1')
    log.out.writelines(['o2', 'o3'])
    log.out.flush()

    log.err.write('e1')
    log.err.writelines(['e2', 'e3'])
    log.err.flush()

    log.SetUserOutputEnabled(False)
    log.out.write('o-1')
    log.out.flush()
    log.err.write('e-1')
    log.err.flush()

    self.AssertOutputNotContains('c1')
    self.AssertOutputNotContains('c2')
    self.AssertOutputNotContains('c3')
    self.AssertOutputNotContains('f1')
    self.AssertOutputNotContains('f2')
    self.AssertOutputNotContains('f3')
    self.AssertOutputContains('o1')
    self.AssertOutputContains('o2')
    self.AssertOutputContains('o3')
    self.AssertOutputNotContains('e1')
    self.AssertOutputNotContains('e2')
    self.AssertOutputNotContains('e3')
    self.AssertOutputNotContains('o-1')
    self.AssertOutputNotContains('e-1')

    self.AssertErrNotContains('c1')
    self.AssertErrContains('INFO: c2')
    self.AssertErrContains('ERROR: c3')
    self.AssertErrNotContains('f1')
    self.AssertErrNotContains('f2')
    self.AssertErrNotContains('f3')
    self.AssertErrNotContains('o1')
    self.AssertErrNotContains('o2')
    self.AssertErrNotContains('o3')
    self.AssertErrContains('e1')
    self.AssertErrContains('e2')
    self.AssertErrContains('e3')
    self.AssertErrNotContains('o-1')
    self.AssertErrNotContains('e-1')

    file_contents = self.GetLogFileContents()
    self.assertIn('DEBUG    root            c1', file_contents)
    self.assertIn('INFO     root            c2', file_contents)
    self.assertIn('ERROR    root            c3', file_contents)
    self.assertIn('DEBUG    ___FILE_ONLY___ f1', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ f2', file_contents)
    self.assertIn('ERROR    ___FILE_ONLY___ f3', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ o1', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ o2', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ o3', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ e1', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ e2', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ e3', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ o-1', file_contents)
    self.assertIn('INFO     ___FILE_ONLY___ e-1', file_contents)

  def testStderr(self):
    """Tests that the stderr writer works."""
    log.SetUserOutputEnabled(True)
    log.out.write('o1')
    log.err.write('e1')

    self.AssertOutputContains('o1')
    self.AssertOutputNotContains('e1')
    self.AssertErrNotContains('o1')
    self.AssertErrContains('e1')

  def testWrappers(self):
    """Tests that the logging convenience wrappers work."""
    log.SetVerbosity(verbosity=logging.DEBUG)
    log.log(logging.DEBUG, '-%s-', '1')
    log.debug('-%s-', '2')
    log.info('-%s-', '3')
    log.warning('-%s-', '4')
    log.error('-%s-', '6')
    log.critical('-%s-', '7')
    log.fatal('-%s-', '8')
    log.exception(ValueError('test exception'))

    self.AssertOutputNotContains('-1-')
    self.AssertOutputNotContains('-2-')
    self.AssertOutputNotContains('-3-')
    self.AssertOutputNotContains('WARNING: -4-')
    self.AssertOutputNotContains('ERROR: -6-')
    self.AssertOutputNotContains('CRITICAL: -7-')
    self.AssertOutputNotContains('CRITICAL: -8-')
    self.AssertOutputNotContains('test exception')

    self.AssertErrContains('-1-')
    self.AssertErrContains('-2-')
    self.AssertErrContains('-3-')
    self.AssertErrContains('WARNING: -4-')
    self.AssertErrContains('ERROR: -6-')
    self.AssertErrContains('CRITICAL: -7-')
    self.AssertErrContains('CRITICAL: -8-')
    self.AssertErrContains('test exception')

  def testUnicodeUtf8FileAndSystemLogger(self):
    """Tests all log targets can handle bytes and str with utf-8 console."""
    self.maxDiff = None
    log.AddFileLogging(self.logs_dir)
    self.SetEncoding('utf-8')
    log_date = datetime.datetime(2017, 1, 1, 0, 0)
    log_time = times.GetTimeStampFromDateTime(log_date)
    self.StartObjectPatch(time, 'time').return_value = log_time

    log.out.write('Ṳᾔḯ¢◎ⅾℯ')
    log.out.write('XṲᾔḯ¢◎ⅾℯ\n'.encode('utf8'))
    log.out.writelines(['ღυłтḯ℘ʟℯ', 'ʟḯᾔεṧ'])
    log.out.writelines(['Xღυłтḯ℘ʟℯ'.encode('utf8'), 'Xʟḯᾔεṧ'.encode('utf8')])
    log.Print()
    log.Print('Ṳᾔḯ¢◎ⅾℯ', 'ṧʊ¢кṧ')
    log.Print('XṲᾔḯ¢◎ⅾℯ'.encode('utf8'), 'Xṧʊ¢кṧ'.encode('utf8'))
    log.out.flush()
    self.AssertOutputEquals("""\
Ṳᾔḯ¢◎ⅾℯXṲᾔḯ¢◎ⅾℯ
ღυłтḯ℘ʟℯʟḯᾔεṧXღυłтḯ℘ʟℯXʟḯᾔεṧ
Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ
XṲᾔḯ¢◎ⅾℯ Xṧʊ¢кṧ
""")

    log.err.write('Ф')
    log.err.write('XФ'.encode('utf8'))
    log.warning('ღ')
    # Python 3 expects only text strings to be written to the logger. For
    # log.err, we decode the byte strings for you and then reencode them again
    # so the behavior matches. For the root logger, if you give it bytes on
    # Python 3, it prints the repr() of the bytes object.
    log.warning('Xღ'.encode('utf8'))
    self.AssertErrEquals('ФXФWARNING: ღ\nWARNING: Xღ\n')
    file_contents = self.GetLogFileContents()
    self.assertEqual(file_contents, """\
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ṳᾔḯ¢◎ⅾℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XṲᾔḯ¢◎ⅾℯ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ ღυłтḯ℘ʟℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ ʟḯᾔεṧ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Xღυłтḯ℘ʟℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Xʟḯᾔεṧ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ \


2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XṲᾔḯ¢◎ⅾℯ Xṧʊ¢кṧ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ф
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XФ
2017-01-01 00:00:00,000 WARNING  root            ღ
2017-01-01 00:00:00,000 WARNING  root            Xღ
""")

  def testUnicodeAsciiFileAndSystemLogger(self):
    """Tests all log targets can handle bytes and str with ascii console."""
    self.maxDiff = None
    log.AddFileLogging(self.logs_dir)
    self.SetEncoding('ascii')
    log_date = datetime.datetime(2017, 1, 1, 0, 0)
    log_time = times.GetTimeStampFromDateTime(log_date)
    self.StartObjectPatch(time, 'time').return_value = log_time

    log.out.write('Ṳᾔḯ¢◎ⅾℯ')
    log.out.write('XṲᾔḯ¢◎ⅾℯ\n'.encode('utf8'))
    log.out.writelines(['ღυłтḯ℘ʟℯ', 'ʟḯᾔεṧ'])
    log.out.writelines(['Xღυłтḯ℘ʟℯ'.encode('utf8'), 'Xʟḯᾔεṧ'.encode('utf8')])
    log.Print()
    log.Print('Ṳᾔḯ¢◎ⅾℯ', 'ṧʊ¢кṧ')
    log.Print('XṲᾔḯ¢◎ⅾℯ'.encode('utf8'), 'Xṧʊ¢кṧ'.encode('utf8'))
    log.out.flush()
    # String is safely rendered even for unsupported characters.
    self.AssertOutputEquals("""\
???????X???????
?????????????X????????X?????
??????? ?????
X??????? X?????
""")

    log.err.write('Ф')
    log.err.write('XФ'.encode('utf8'))
    log.warning('ღ')
    # Python 3 expects only text strings to be written to the logger. For
    # log.err, we decode the byte strings for you and then reencode them again
    # so the behavior matches. For the root logger, if you give it bytes on
    # Python 3, it prints the repr() of the bytes object.
    log.warning('Xღ'.encode('utf8'))
    self.AssertErrEquals('?X?WARNING: ?\nWARNING: X?\n')
    file_contents = self.GetLogFileContents()
    # Log file contents are always utf-8 so all information is retained.
    self.assertEqual(file_contents, """\
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ṳᾔḯ¢◎ⅾℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XṲᾔḯ¢◎ⅾℯ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ ღυłтḯ℘ʟℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ ʟḯᾔεṧ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Xღυłтḯ℘ʟℯ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Xʟḯᾔεṧ
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ \


2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ṳᾔḯ¢◎ⅾℯ ṧʊ¢кṧ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XṲᾔḯ¢◎ⅾℯ Xṧʊ¢кṧ

2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ Ф
2017-01-01 00:00:00,000 INFO     ___FILE_ONLY___ XФ
2017-01-01 00:00:00,000 WARNING  root            ღ
2017-01-01 00:00:00,000 WARNING  root            Xღ
""")

  def testBadUnicodeUtf8Stream(self):
    self.SetEncoding('utf-8')
    log.Print('\xb8')
    self.AssertOutputContains('\xb8')

  def testUnicodeAsciiStream(self):
    # This SetEncoding is required to force log.out to have the same encoding.
    self.SetEncoding('ascii')
    log.out.Print('[some ASCII]')
    log.out.Print('[Фёдор Миха́йлович Достое́вский]')
    log.out.Print('[mañana]')
    self.AssertOutputContains('[some ASCII]\n')
    self.AssertOutputContains('[????? ??????????? ????????????]\n')
    self.AssertOutputContains('[ma?ana]\n')

  def testBadUnicodeAsciiStream(self):
    # This SetEncoding is required to force log.out to have the same encoding.
    self.SetEncoding('ascii')
    log.Print('\xb8')
    self.AssertOutputContains('?')

  def testUnicodeLatin1Stream(self):
    self.SetEncoding('latin-1')
    log.out.Print('[Fußgängerübergänge]')
    log.out.Print('[老子]')
    log.out.Print('[Motörhead]'.encode('latin-1'))  # test pre-encoded str
    self.AssertOutputContains('[Fußgängerübergänge]')
    self.AssertOutputContains('[??]\n')
    self.AssertOutputContains('[Motörhead]')

  def testRegularLogger(self):
    """Tests that the root logger has the correct behavior."""
    log.SetVerbosity(logging.INFO)
    logging.debug('1')
    logging.info('2')
    logging.error('3')

    self.AssertOutputNotContains('1')
    self.AssertOutputNotContains('2')
    self.AssertOutputNotContains('3')

    self.AssertErrNotContains('1')
    self.AssertErrContains('2')
    self.AssertErrContains('3')

  def testVerbosity(self):
    log.SetVerbosity(logging.INFO)
    self.assertEqual(log.GetVerbosity(), logging.INFO)
    self.assertEqual(log.GetVerbosityName(), 'info')
    log.SetVerbosity(1000)
    self.assertEqual(log.GetVerbosityName(), None)

  def testVerbosityNames(self):
    names = log.OrderedVerbosityNames()
    self.assertTrue(isinstance(names, list))
    self.assertTrue('debug' in names)

  def testLogDir(self):
    # Save this before we patch over datetime.datetime
    old_datetime_epoch = datetime.datetime(1970, 1, 1)
    datetime_mock = self.StartObjectPatch(datetime, 'datetime')
    datetime_mock.now.return_value = old_datetime_epoch

    self.assertEqual(None, log.GetLogDir())
    self.assertEqual(None, log.GetLogFileName('.log'))
    self.assertEqual(None, log.GetLogFilePath())

    log.AddFileLogging(self.logs_dir)

    self.assertEqual(log.GetLogDir(), os.path.join(self.logs_dir, '1970.01.01'))
    self.assertEqual(log.GetLogFileName('.foo'), '00.00.00.000000.foo')

    self.assertEqual(log.GetLogFilePath(),
                     os.path.join(self.logs_dir, '1970.01.01',
                                  '00.00.00.000000.log'))

  def testGetVerbosityNamesArg(self):
    self.assertEqual(log.GetVerbosityName(logging.DEBUG), 'debug')
    self.assertEqual(log.GetVerbosityName(logging.INFO), 'info')
    self.assertEqual(log.GetVerbosityName(logging.WARNING), 'warning')
    self.assertEqual(log.GetVerbosityName(logging.ERROR), 'error')
    self.assertEqual(log.GetVerbosityName(logging.CRITICAL), 'critical')

  def testGetLogFileVerbosity(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    log.AddFileLogging(self.logs_dir)
    default_log_file_verbosity = log.GetLogFileVerbosity()
    self.assertEqual(default_log_file_verbosity, logging.NOTSET)

  def testBadLogDirectory(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    logs_dir = self.Touch(directory=self.logs_dir)
    log.AddFileLogging(logs_dir)
    log.info('Logged at info level')
    self.AssertErrContains('WARNING: Could not setup log file in {0}'
                           .format(logs_dir))
    self.AssertErrContains('Logged at info level')

  def testLogDirectoryPermissionDeniedWithUnicodePath(self):
    self.SetEncoding('utf-8')
    def _MockMakeDir(unused_dir_path):
      raise OSError('Permission denied.')

    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    logs_dir = '/tmp/Ṳᾔḯ¢◎ⅾℯ'
    self.StartObjectPatch(file_utils, 'MakeDir', side_effect=_MockMakeDir)
    log.AddFileLogging(logs_dir)
    log.info('Logged at info level')
    self.AssertErrContains('WARNING: Could not setup log file in {0}'
                           .format(logs_dir))
    self.AssertErrContains('Logged at info level')

  @test_case.Filters.DoNotRunOnWindows
  def testReadOnlyDirectory(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    os.chmod(self.logs_dir, 0o100)
    try:
      log.AddFileLogging(self.logs_dir)
    finally:
      os.chmod(self.logs_dir, 0o700)
    log.info('Logged at info level')
    self.AssertErrContains('WARNING: Could not setup log file in {0}, (Error:'
                           .format(self.logs_dir))
    self.AssertErrContains('Logged at info level')

  @test_case.Filters.DoNotRunOnWindows
  def testReadOnlyFile(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    original_setup_logs_dir = log._LogManager._SetupLogsDir
    filenames = []
    def _SetupLogsDir(self, logs_dir):
      # Intercept file and make it readonly.
      log_filename = original_setup_logs_dir(self, logs_dir)
      with open(log_filename, 'w') as f:
        f.write('Test Message')
      filenames.append(log_filename)
      os.chmod(log_filename, 0o100)
      return log_filename
    self.StartObjectPatch(log._LogManager, '_SetupLogsDir', autospec=True,
                          side_effect=_SetupLogsDir)
    try:
      log.AddFileLogging(self.logs_dir)
    finally:
      os.chmod(filenames[0], 0o600)
    log.info('Logged at info level')
    self.AssertErrMatches(r'WARNING: Could not setup log file in {0}, \(.*:'
                          .format(self.logs_dir))
    self.AssertErrContains('Logged at info level')

  def testSetLogFileVerbosity(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    log.AddFileLogging(self.logs_dir)

    log.out.write('1 public\n')
    log_file_verbosity = log.SetLogFileVerbosity(logging.ERROR)
    log.out.write('2 private\n')
    log.SetLogFileVerbosity(log_file_verbosity)
    log.out.write('3 public\n')
    self.AssertOutputEquals('1 public\n2 private\n3 public\n')

    log_file_contents = self.GetLogFileContents()
    self.assertIn('1 public', log_file_contents)
    self.assertNotIn('2 private', log_file_contents)
    self.assertIn('3 public', log_file_contents)

  def testSetLogFileVerbosityContext(self):
    log.SetVerbosity(logging.INFO)
    log.SetUserOutputEnabled(True)
    log.AddFileLogging(self.logs_dir)

    original_log_file_verbosity = log.GetLogFileVerbosity()
    log.out.write('1 public\n')
    with log.LogFileVerbosity(logging.ERROR) as log_file_verbosity:
      log.out.write('2 private\n')
    log.out.write('3 public\n')
    self.AssertOutputEquals('1 public\n2 private\n3 public\n')

    log_file_contents = self.GetLogFileContents()
    self.assertIn('1 public', log_file_contents)
    self.assertNotIn('2 private', log_file_contents)
    self.assertIn('3 public', log_file_contents)

    self.assertEqual(log_file_verbosity, original_log_file_verbosity)
    current_log_file_verbosity = log.GetLogFileVerbosity()
    self.assertEqual(log_file_verbosity, current_log_file_verbosity)

  def testGetMaxLogDays(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    self.assertEqual(log_manager_instance._GetMaxLogDays(), 10)

  def testGetMaxLogDaysNotSetReturnsDefaultValue(self):
    log_manager_instance = log._LogManager()
    self.assertEqual(log_manager_instance._GetMaxLogDays(), 30)

  def testGetMaxLogDaysReturnsFalse(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(0)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    self.assertFalse(log_manager_instance._GetMaxLogDays())

  def testGetMaxLogDaysReturnsTrue(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    self.assertTrue(log_manager_instance._GetMaxLogDays())

  def testGetMaxAge(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    days_in_seconds = 60 * 60 * 24 * 10
    self.assertEqual(log_manager_instance._GetMaxAge(), days_in_seconds)

  def testGetMaxAgeTimeDelta(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    self.assertEqual(log_manager_instance._GetMaxAgeTimeDelta(),
                     datetime.timedelta(10))

  def testShouldDeleteDirDirDoesNotExist(self):
    log_manager_instance = log._LogManager()
    self.StartObjectPatch(os.path, 'isdir').return_value = False
    now = time.time()
    self.assertFalse(log_manager_instance._ShouldDeleteDir(now, self.temp_path))

  def testShouldDeleteDir_DirNotOldEnough(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    old_datetime = datetime.datetime(2016, 2, 14)
    file_datetime_mock = self.StartObjectPatch(
        log._LogManager, '_GetFileDatetime')
    file_datetime_mock.return_value = old_datetime
    now = datetime.datetime(2016, 2, 20)
    # Don't use StartObjectPatch because it adds ~10 seconds if it's patched
    # during the early stages of TearDown
    with mock.patch.object(os.path, 'isdir', return_value=True):
      self.assertFalse(log_manager_instance._ShouldDeleteDir(
          now, self.temp_path))

  def testShouldDeleteDirTrue(self):
    log_manager_instance = log._LogManager()
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    old_datetime = datetime.datetime(2016, 7, 5)
    self.StartObjectPatch(log._LogManager, '_GetFileDatetime',
                          return_value=old_datetime)
    now = datetime.datetime(2016, 7, 20)
    # Don't use StartObjectPatch because it adds ~10 seconds if it's patched
    # during the early stages of TearDown
    with mock.patch.object(os.path, 'isdir', return_value=True):
      self.assertTrue(log_manager_instance._ShouldDeleteDir(
          now, self.temp_path))

  def testShouldDeleteFileUnknownFile(self):
    log_manager_instance = log._LogManager()
    known_path_mock = self.StartObjectPatch(os.path, 'splitext')
    known_path_mock.return_value = ['filename', '.txt']
    now = time.time()
    self.assertFalse(log_manager_instance._ShouldDeleteFile(
        now, self.temp_path))


class LoggingConfigNoOutCaptureTest(sdk_test_base.WithOutputCapture,
                                    sdk_test_base.SdkBase):
  """Tests basic configuration of the python logger under calliope."""

  def SetUp(self):
    dir_age_mock = self.StartObjectPatch(
        log._LogManager, '_ShouldDeleteDir', autospec=True)
    self.dir_paths = {}
    def ShouldDeleteDirMock(unused_self, _, path):
      return self.dir_paths[path]
    dir_age_mock.side_effect = ShouldDeleteDirMock

    self.file_paths = {}
    file_age_mock = self.StartObjectPatch(
        log._LogManager, '_ShouldDeleteFile', autospec=True)
    def ShouldDeleteFileMock(unused_self, _, path):
      return self.file_paths[path]
    file_age_mock.side_effect = ShouldDeleteFileMock
    self.logs = self.CreateTempDir('logs')

  def _SetUpDir(self, dirname, *filenames):
    dir_path = os.path.join(self.logs, dirname)
    file_utils.MakeDir(dir_path)

    file_paths = []
    for f in filenames:
      file_path = os.path.join(dir_path, f + '.log')
      file_paths.append(file_path)
      with open(file_path, 'w'):
        pass

    return dir_path, file_paths

  def testNoDirs(self):
    self.assertEqual(0, len(os.listdir(self.logs)))
    log._log_manager._CleanLogsDir(self.logs)

  def testNewDir(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = False
    self.file_paths[files1[0]] = False
    log._log_manager._CleanLogsDir(self.logs)

    # Don't delete, it's not old enough.
    self.assertEqual(1, len(os.listdir(self.logs)))
    self.assertTrue(os.path.exists(dir1))
    self.assertTrue(os.path.exists(files1[0]))

  def testNewAndOld(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = False
    self.file_paths[files1[0]] = False
    dir2, files2 = self._SetUpDir('dir2', 'file2')
    self.dir_paths[dir2] = True
    self.file_paths[files2[0]] = True
    log._log_manager._CleanLogsDir(self.logs)

    self.assertEqual(1, len(os.listdir(self.logs)))
    self.assertTrue(os.path.exists(dir1))
    self.assertTrue(os.path.exists(files1[0]))
    self.assertFalse(os.path.exists(dir2))
    self.assertFalse(os.path.exists(files2[0]))

  def testOldDirNewFile(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1', 'file2')
    self.dir_paths[dir1] = True
    self.file_paths[files1[0]] = True
    self.file_paths[files1[1]] = False
    log._log_manager._CleanLogsDir(self.logs)

    # Dir stays around, old file1 gets removed.
    self.assertEqual(1, len(os.listdir(self.logs)))
    self.assertTrue(os.path.exists(dir1))
    self.assertFalse(os.path.exists(files1[0]))
    self.assertTrue(os.path.exists(files1[1]))

  def testNewDirOldFile(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = False
    self.file_paths[files1[0]] = True
    log._log_manager._CleanLogsDir(self.logs)

    # Dir stays around, and files don't get processed.
    self.assertEqual(1, len(os.listdir(self.logs)))
    self.assertTrue(os.path.exists(dir1))
    self.assertTrue(os.path.exists(files1[0]))

  def testCleanUpLogsDefaultMaxLogDaysFilesDeleted(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = True
    self.file_paths[files1[0]] = True
    log._log_manager._CleanUpLogs(self.logs)

    self.assertFalse(os.path.exists(dir1))
    self.assertFalse(os.path.exists(files1[0]))

  def testCleanUpLogsCleanupDisabledFilesNotDeleted(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = True
    self.file_paths[files1[0]] = True
    properties.VALUES.core.max_log_days.Set(0)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    log._log_manager._CleanUpLogs(self.logs)

    # Directory and files are not deleted
    self.assertTrue(os.path.exists(dir1))
    self.assertTrue(os.path.exists(files1[0]))

  def testCleanUpLogsCleanupEnabledFilesDeleted(self):
    dir1, files1 = self._SetUpDir('dir1', 'file1')
    self.dir_paths[dir1] = True
    self.file_paths[files1[0]] = True
    properties.VALUES.core.max_log_days.Set(10)
    self.addCleanup(properties.VALUES.core.max_log_days.Set, None)
    log._log_manager._CleanUpLogs(self.logs)

    self.assertFalse(os.path.exists(dir1))
    self.assertFalse(os.path.exists(files1[0]))


class LogResourceChangeTest(sdk_test_base.WithOutputCapture):

  def testCreated(self):
    log.CreatedResource('my-cluster')
    self.AssertErrEquals('Created [my-cluster].\n')

  def testCreatedNoResource(self):
    log.CreatedResource(None)
    self.AssertErrEquals('Created.\n')

  def testCreatedNoResourceKind(self):
    log.CreatedResource(None)
    self.AssertErrEquals('Created.\n')

  def testCreatedKind(self):
    log.CreatedResource(None, kind='cluster')
    self.AssertErrEquals('Created cluster.\n')

  def testCreatedKindDetails(self):
    log.CreatedResource('my-cluster', kind='cluster',
                        details='in region [us-east1]')
    self.AssertErrEquals('Created cluster [my-cluster] in region [us-east1].\n')

  def testCreatedKindDetailsFailed(self):
    log.CreatedResource('my-cluster', kind='cluster',
                        details='in region [us-east1]',
                        failed='Permission denied')
    self.AssertErrEquals('ERROR: Failed to create cluster [my-cluster] in '
                         'region [us-east1]: Permission denied.\n')

  def testCreatedKindDetailsFailedPeriod(self):
    log.CreatedResource('my-cluster', kind='cluster',
                        details='in region [us-east1]',
                        failed='Permission denied.')
    self.AssertErrEquals('ERROR: Failed to create cluster [my-cluster] in '
                         'region [us-east1]: Permission denied.\n')

  def testCreatedAsync(self):
    log.CreatedResource('my-cluster', is_async=True)
    self.AssertErrEquals('Create in progress for [my-cluster].\n')

  def testCreatedKindAsync(self):
    log.CreatedResource('my-cluster', kind='cluster', is_async=True)
    self.AssertErrEquals('Create in progress for cluster [my-cluster].\n')

  def testCreatedKindDetailsAsync(self):
    log.CreatedResource('my-cluster', kind='cluster',
                        details='in region [us-east1]', is_async=True)
    self.AssertErrEquals(
        'Create in progress for cluster [my-cluster] in region [us-east1].\n')

  def testDeleted(self):
    log.DeletedResource('my-cluster')
    self.AssertErrEquals('Deleted [my-cluster].\n')

  def testDeletedAsync(self):
    log.DeletedResource('my-cluster', is_async=True)
    self.AssertErrEquals('Delete in progress for [my-cluster].\n')

  def testRestored(self):
    log.RestoredResource('my-cluster')
    self.AssertErrEquals('Restored [my-cluster].\n')

  def testRestoredAsync(self):
    log.RestoredResource('my-cluster', is_async=True)
    self.AssertErrEquals('Restore in progress for [my-cluster].\n')

  def testUpdated(self):
    log.UpdatedResource('my-cluster')
    self.AssertErrEquals('Updated [my-cluster].\n')

  def testUpdatedAsync(self):
    log.UpdatedResource('my-cluster', is_async=True)
    self.AssertErrEquals('Update in progress for [my-cluster].\n')

  def testReset(self):
    log.ResetResource('mytpu')
    self.AssertErrEquals('Reset [mytpu].\n')

  def testResetAsync(self):
    log.ResetResource('mytpu', is_async=True)
    self.AssertErrEquals('Reset in progress for [mytpu].\n')


class StructuredLoggingTest(sdk_test_base.WithLogCapture):

  def SetUp(self):
    log_date = datetime.datetime(2017, 1, 1, 0, 0)
    log_time = times.GetTimeStampFromDateTime(log_date, tzinfo=times.UTC)
    self.StartObjectPatch(time, 'time').return_value = log_time
    properties.VALUES.core.show_structured_logs.Set(None)
    self.no_stacktrace_string = 'None' if six.PY2 else 'NoneType: None'

  def TearDown(self):
    log.Reset()

  def testExceptionsTerminalOnly(self):
    """Test that structured errors and exceptions go to terminal only."""
    properties.VALUES.core.show_structured_logs.Set('terminal')
    log.SetVerbosity(logging.ERROR)
    log.SetUserOutputEnabled(True)

    log.error('-%s-', '1')
    log.critical('-%s-', '2')
    log.fatal('-%s-', '3')
    log.exception(ValueError('test exception - 4'))
    self.AssertErrEquals("""\
    ERROR: -1-
    CRITICAL: -2-
    CRITICAL: -3-
    ERROR: test exception - 4
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.ERROR)
    log.error('-%s-', '5')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-5-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-6-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-7-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 8", "error": {"type": "ValueError", '
         '"details": "test exception - 8", "stacktrace": null}}'),
        normalize_space=True)

  def testMessagesTerminalOnly(self):
    """Test that all structured messages go to terminal only."""
    log.SetVerbosity(logging.DEBUG)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('terminal')

    log.debug('-%s-', '1')
    log.info('-%s-', '2')
    log.warning('-%s-', '3')
    log.error('-5-')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))
    self.AssertErrEquals("""\
    DEBUG: -1-
    INFO: -2-
    WARNING: -3-
    ERROR: -5-
    CRITICAL: -6-
    CRITICAL: -7-
    ERROR: test exception - 8
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.DEBUG)
    log.debug('-%s-', '9')
    log.info('-%s-', '10')
    log.warning('-%s-', '11')
    log.error('-%s-', '13')
    log.critical('-%s-', '14')
    log.fatal('-%s-', '15')
    log.exception(ValueError('test exception - 16'))
    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "DEBUG", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-9-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "INFO", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-10-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "WARNING", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-11-"}'), normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-13-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-14-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-15-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 16", "error": {"type": "ValueError", '
         '"details": "test exception - 16", "stacktrace": null}}'),
        normalize_space=True)

  def testExceptionsLogOnly(self):
    """Test that structured errors and exceptions go to stderr log only."""
    log.SetVerbosity(logging.ERROR)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('log')

    log.error('-%s-', '1')
    log.critical('-%s-', '2')
    log.fatal('-%s-', '3')
    log.exception(ValueError('test exception - 4'))
    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-1-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-2-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-3-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 4", "error": {"type": "ValueError", '
         '"details": "test exception - 4", "stacktrace": null}}'),
        normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.ERROR)
    log.error('-%s-', '5')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))
    self.AssertErrEquals("""\
    ERROR: -5-
    CRITICAL: -6-
    CRITICAL: -7-
    ERROR: test exception - 8
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

  def testMessagesLogOnly(self):
    """Test that all structured messages go to stderr log only."""
    log.SetVerbosity(logging.DEBUG)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('log')

    log.debug('-%s-', '1')
    log.info('-%s-', '2')
    log.warning('-%s-', '3')
    log.error('-5-')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "DEBUG", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-1-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "INFO", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-2-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "WARNING", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-3-"}'), normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-5-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-6-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-7-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 8", "error": {"type": "ValueError", '
         '"details": "test exception - 8", "stacktrace": null}}'),
        normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.DEBUG)
    log.debug('-%s-', '9')
    log.info('-%s-', '10')
    log.warning('-%s-', '11')
    log.error('-%s-', '13')
    log.critical('-%s-', '14')
    log.fatal('-%s-', '15')
    log.exception(ValueError('test exception - 16'))
    self.AssertErrEquals("""\
    DEBUG: -9-
    INFO: -10-
    WARNING: -11-
    ERROR: -13-
    CRITICAL: -14-
    CRITICAL: -15-
    ERROR: test exception - 16
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

  def testExceptionsAlways(self):
    """Test that structured errors/exceptions go to stderr log and terminal."""
    log.SetVerbosity(logging.ERROR)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('always')

    log.error('-%s-', '1')
    log.critical('-%s-', '2')
    log.fatal('-%s-', '3')
    log.exception(ValueError('test exception - 4'))
    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-1-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-2-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-3-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 4", "error": {"type": "ValueError", '
         '"details": "test exception - 4", "stacktrace": null}}'),
        normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.ERROR)
    log.error('-%s-', '5')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))
    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-5-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-6-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-7-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 8", "error": {"type": "ValueError", '
         '"details": "test exception - 8", "stacktrace": null}}'),
        normalize_space=True)

  def testMessagesAlways(self):
    """Test that all structured messages go to stderr log and terminal."""
    log.SetVerbosity(logging.DEBUG)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('always')

    log.debug('-%s-', '1')
    log.info('-%s-', '2')
    log.warning('-%s-', '3')
    log.error('-5-')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "DEBUG", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-1-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "INFO", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-2-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "WARNING", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-3-"}'), normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-5-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-6-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-7-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 8", "error": {"type": "ValueError", '
         '"details": "test exception - 8", "stacktrace": null}}'),
        normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.DEBUG)
    log.debug('-%s-', '9')
    log.info('-%s-', '10')
    log.warning('-%s-', '11')
    log.error('-%s-', '13')
    log.critical('-%s-', '14')
    log.fatal('-%s-', '15')
    log.exception(ValueError('test exception - 16'))
    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "DEBUG", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-9-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "INFO", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-10-"}'), normalize_space=True)

    self.AssertErrContains((r'{"version": "0.0.1", "verbosity": "WARNING", '
                            '"timestamp": "2017-01-01T00:00:00.000Z", '
                            '"message": "-11-"}'), normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-13-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-14-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "CRITICAL", '
         '"timestamp": "2017-01-01T00:00:00.000Z", "message": "-15-"}'),
        normalize_space=True)

    self.AssertErrContains(
        (r'{"version": "0.0.1", "verbosity": "ERROR", '
         '"timestamp": "2017-01-01T00:00:00.000Z", '
         '"message": "test exception - 16", "error": {"type": "ValueError", '
         '"details": "test exception - 16", "stacktrace": null}}'),
        normalize_space=True)

  def testStructuredOutputNever(self):
    """Test that no structured messages go to stderr log or terminal."""
    log.SetVerbosity(logging.DEBUG)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('never')

    log.debug('-%s-', '1')
    log.info('-%s-', '2')
    log.warning('-%s-', '3')
    log.error('-5-')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))
    self.AssertErrEquals("""\
    DEBUG: -1-
    INFO: -2-
    WARNING: -3-
    ERROR: -5-
    CRITICAL: -6-
    CRITICAL: -7-
    ERROR: test exception - 8
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

    self.StartObjectPatch(log._ConsoleWriter, 'isatty').return_value = True
    self.ClearErr()
    log.Reset()
    log.SetVerbosity(logging.DEBUG)
    log.debug('-%s-', '9')
    log.info('-%s-', '10')
    log.warning('-%s-', '11')
    log.error('-%s-', '13')
    log.critical('-%s-', '14')
    log.exception(ValueError('test exception - 15'))
    self.AssertErrEquals("""\
    DEBUG: -9-
    INFO: -10-
    WARNING: -11-
    ERROR: -13-
    CRITICAL: -14-
    ERROR: test exception - 15
    {}
    """.format(self.no_stacktrace_string), normalize_space=True)

  def testLogFileIsText(self):
    """Test that all messages sent to log file are plain text."""
    log.SetVerbosity(logging.DEBUG)
    log.SetUserOutputEnabled(True)
    properties.VALUES.core.show_structured_logs.Set('always')
    log.debug('-%s-', '1')
    log.info('-%s-', '2')
    log.warning('-%s-', '3')
    log.error('-5-')
    log.critical('-%s-', '6')
    log.fatal('-%s-', '7')
    log.exception(ValueError('test exception - 8'))
    self.AssertLogContains('DEBUG    root            -1-', normalize_space=True)
    self.AssertLogContains('INFO     root            -2-', normalize_space=True)
    self.AssertLogContains('WARNING  root            -3-', normalize_space=True)
    self.AssertLogContains('ERROR    root            -5-', normalize_space=True)
    self.AssertLogContains('CRITICAL root            -6-', normalize_space=True)
    self.AssertLogContains('CRITICAL root            -7-', normalize_space=True)
    self.AssertLogContains('ERROR    root            test exception - 8',
                           normalize_space=True)


class FileOrStdoutTests(sdk_test_base.WithOutputCapture):

  def testStdoutWrite(self):
    contents = 'abc123'
    log.WriteToFileOrStdout('-', contents)
    self.AssertOutputEquals(contents)

  def testStdoutWriteBytes(self):
    log.WriteToFileOrStdout(
        '-',
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n',
        binary=True)
    self.assertEqual(
        self.GetOutputBytes(),
        b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n')

  def testFileWrite(self):
    contents = 'abc123'
    path = os.path.join(self.temp_path, self.RandomFileName())
    file_utils.WriteFileContents(path, contents)
    self.AssertFileEquals(contents, path)

  def testFileWriteBinary(self):
    contents = b'\xc3\x9c\xc3\xb1\xc3\xae\xc3\xa7\xc3\xb2\xc3\x90\xc3\xa9\n'
    path = os.path.join(self.temp_path, self.RandomFileName())
    file_utils.WriteFileContents(path, contents, binary=True)
    self.assertEqual(file_utils.GetFileContents(path, binary=True), contents)


if __name__ == '__main__':
  test_case.main()
