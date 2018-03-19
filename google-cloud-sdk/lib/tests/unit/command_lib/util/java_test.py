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

"""Tests of the java module."""

import subprocess

from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base


class JavaTests(sdk_test_base.WithOutputCapture):

  def testJavaExecutableNotFound(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = None

    with self.assertRaises(java.JavaError):
      java.RequireJavaInstalled('foo')

  def testJavaExecutableNotExecutable(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    called_process_err = subprocess.CalledProcessError(1, 'cmd', 'output')
    check_out_mock.side_effect = called_process_err

    with self.assertRaises(java.JavaError):
      java.RequireJavaInstalled('foo')

  def testJavaExecutableNotJava7(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "not1.7'

    with self.assertRaises(java.JavaError):
      java.RequireJavaInstalled('foo')

    check_out_mock.return_value = 'version "1.6'

    with self.assertRaises(java.JavaError):
      java.RequireJavaInstalled('foo')

  def testJava7InstalledAndOnPath(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "1.7.'

    try:
      java.RequireJavaInstalled('foo')
    except java.JavaError:
      self.fail('JavaError should not be thrown here')

    check_out_mock.return_value = 'version "1.8.'

    self.assertEquals(java.RequireJavaInstalled('foo'),
                      '/path/to/java')

  def testJava8Error(self):
    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "1.7.'

    with self.assertRaises(java.JavaError):
      java.RequireJavaInstalled('foo', min_version=8)

  def testJava9InstalledAndOnPath(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "9.0.1"'

    self.assertEquals(java.RequireJavaInstalled('foo', min_version=7),
                      '/path/to/java')

  def testJava9InstalledAndOnPath_JustMajorVersion(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "9"'

    self.assertEquals(java.RequireJavaInstalled('foo', min_version=7),
                      '/path/to/java')

  def testJava9InstalledAndOnPath_JustMajorVersionWithPrelease(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "9-internal"'

    self.assertEquals(java.RequireJavaInstalled('foo', min_version=7),
                      '/path/to/java')

  def testJava9InstalledAndOnPath_JustMajorMinorSecurityVersion(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "9.1.3"'

    self.assertEquals(java.RequireJavaInstalled('foo', min_version=7),
                      '/path/to/java')

  def testJava10InstalledAndOnPath_JustMajor(self):
    find_exec_mock = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec_mock.return_value = '/path/to/java'

    check_out_mock = self.StartObjectPatch(subprocess, 'check_output')
    check_out_mock.return_value = 'version "10"'

    self.assertEquals(java.RequireJavaInstalled('foo', min_version=7),
                      '/path/to/java')
