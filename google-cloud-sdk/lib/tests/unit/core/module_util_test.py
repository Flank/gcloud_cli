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

"""Unit tests for the core.module_util module."""

from argcomplete import completers as argcomplete_completers

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import module_util
from googlecloudsdk.core.util import files
from tests.lib import test_case


class ModulePathTest(test_case.TestCase):

  def testImportExistingCloudSdkModule(self):
    times = module_util.ImportModule('googlecloudsdk.core.util.times')
    dt = times.GetDateTimeFromTimeStamp(1496293728)
    ts = times.FormatDateTime(dt, tzinfo=times.UTC)
    self.assertEquals('2017-06-01T05:08:48.000Z', ts)

  def testImportMalformedStandardModule(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r'Module path \[argcomplete.completers.FilesCompleter] '
        r'not found: No module named FilesCompleter.'):
      module_util.ImportModule('argcomplete.completers.FilesCompleter')

  def testImportExistingStandardModule(self):
    files_completer = module_util.ImportModule(
        'argcomplete.completers:FilesCompleter')
    self.assertEquals(argcomplete_completers.FilesCompleter, files_completer)

  def testImportNoSuchPackage(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r'Module path \[scrooglecloudsdk.core.util.times] '
        r'not found: No module named scrooglecloudsdk.core.util.times.'):
      module_util.ImportModule('scrooglecloudsdk.core.util.times')

  def testImportNoSuchModule(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r'Module path \[googlecloudsdk.core.futile.times] '
        r'not found: No module named futile.times.'):
      module_util.ImportModule('googlecloudsdk.core.futile.times')

  def testImportNoSuchAttribute(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r"Module path \[googlecloudsdk.core.util.times:UnKnOwN] "
        r"not found: 'module' object has no attribute 'UnKnOwN'."):
      module_util.ImportModule('googlecloudsdk.core.util.times:UnKnOwN')

  def testImportNoSuchAttributePath(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r"Module path \[googlecloudsdk.core.util:FormatDateTime.UnKnOwN] "
        r"not found: 'module' object has no attribute 'FormatDateTime'."):
      module_util.ImportModule(
          'googlecloudsdk.core.util:FormatDateTime.UnKnOwN')

  def testImportBadForm(self):
    with self.assertRaisesRegexp(
        module_util.ImportModuleError,
        r'Module path \[googlecloudsdk.core.util:FormatDateTime:UnKnOwN] '
        r'must be in the form: '
        r'package\(.module\)\+\(:attribute\(.attribute\)\*\)\?'):
      module_util.ImportModule(
          'googlecloudsdk.core.util:FormatDateTime:UnKnOwN')

  def testGetModulePathModule(self):
    self.assertEqual(None, module_util.GetModulePath(files))

  def testGetModulePathClass(self):
    self.assertEqual('googlecloudsdk.core.util.files:Error',
                     module_util.GetModulePath(files.Error))

  def testGetModulePathObject(self):
    self.assertEqual('googlecloudsdk.core.util.files:Error',
                     module_util.GetModulePath(files.Error(
                         'Something happened')))

  def testGetModulePathFunction(self):
    self.assertEqual('googlecloudsdk.core.util.files:CopyTree',
                     module_util.GetModulePath(files.CopyTree))

  def testGetModulePathVariable(self):
    self.assertEqual(None, module_util.GetModulePath(files.NUM_RETRIES))

  def testGetModulePathNumber(self):
    self.assertEqual(None, module_util.GetModulePath(1))

  def testGetModulePathNone(self):
    self.assertEqual(None, module_util.GetModulePath(None))

  def testGetModulePathBuiltin(self):
    self.assertEqual(None, module_util.GetModulePath(int))

  def testGetModulePathResourceParamCompleter(self):
    self.assertEqual(
        'googlecloudsdk.command_lib.util.completers:ResourceParamCompleter',
        module_util.GetModulePath(completers.ResourceParamCompleter))

  def testGetModulePathNoCacheCompleter(self):
    self.assertEqual(
        'googlecloudsdk.command_lib.util.completers:NoCacheCompleter',
        module_util.GetModulePath(completers.NoCacheCompleter))

  def testGetModulePathFilesCompleter(self):
    self.assertEqual('argcomplete.completers:FilesCompleter',
                     module_util.GetModulePath(
                         argcomplete_completers.FilesCompleter))


if __name__ == '__main__':
  test_case.main()
