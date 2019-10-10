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
"""Tests for the ML Engine jobs_prep command_lib utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import contextlib
import os
import tarfile
import zipfile

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.command_lib.ml_engine import jobs_prep
from googlecloudsdk.command_lib.ml_engine import uploads
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.ml_engine import base

import mock
import six


@contextlib.contextmanager
def _UnwritableDirectory(path):
  """Makes a directory and its contents temporarily unwritable.

  All files have all their write bits removed, then their user-write bits
  restored at the end (whether they were originally user-writable or not).

  Doesn't work on Windows.

  Args:
    path: str, the path to the directory on which to modify the permissions.

  Yields:
    None
  """
  paths = []
  for dirpath, _, filenames in os.walk(six.text_type(path)):
    paths.append(dirpath)
    paths.extend([os.path.join(dirpath, filename) for filename in filenames])
  try:
    for path in paths:
      os.chmod(path, os.stat(path).st_mode & 0o555)
    yield
  finally:
    for path in paths:
      os.chmod(path, os.stat(path).st_mode | 0o200)


# For setuptools, which we include in our bundle but isn't accessible otherwise
@sdk_test_base.Filters.RunOnlyInBundle
class BuildPackagesTest(base.MlBetaPlatformTestBase):
  """Test BuildPackages, including integration with setuptools."""

  EXPECTED_FILES = {
      'PKG-INFO',
      os.path.join('test_package', 'test_task.py'),
      os.path.join('test_package', '__init__.py'),
      'setup.py'
  }
  EXPECTED_DIRS = {
      'test_package',
  }

  def SetUp(self):
    self.package_parent = os.path.join(self.temp_path, 'package_root')
    files.CopyTree(self.Resource('tests', 'unit', 'command_lib', 'ml_engine',
                                 'test_data', 'package_root'),
                   self.package_parent)
    self.package_dir = os.path.join(self.package_parent, 'test_package')
    self.output_dir = os.path.join(self.temp_path, 'output')

  def _AssertArchivePathsOkay(self, archive_paths, additional_files=None,
                              package_name='package1-1.0'):
    # Some setuptools versions generate a setup.cfg/MANIFEST; others don't.
    # Doesn't matter much either way.
    optional_files = {os.path.join(package_name, 'setup.cfg'), 'MANIFEST'}
    if additional_files is None:
      additional_files = [os.path.join(package_name, 'setup.py')]
    self.assertEqual(len(archive_paths), 1)
    expected_files = (
        {os.path.join(package_name, f) for f in self.EXPECTED_FILES} |
        set(additional_files)
    )
    try:
      with tarfile.open(archive_paths[0], 'r:gz') as archive:
        archive_files = archive.getnames()
    except tarfile.ReadError:
      with zipfile.ZipFile(archive_paths[0]) as archive:
        archive_files = archive.namelist()
    else:
      # tarfile reports directories in getnames(); zipfile does not
      expected_files = (
          expected_files |
          {os.path.join(package_name, d) for d in self.EXPECTED_DIRS} |
          {package_name}
      )

    # ZipFile.namelist() and TarFile.getnames() return '/' as the separator
    # regardless of platform
    archive_files = [name.replace('/', os.path.sep) for name in
                     archive_files]
    archive_files = set(archive_files)
    expected_files |= (archive_files & optional_files)
    self.assertSetEqual(archive_files, expected_files)

  def _AssertPackageDirUnmodified(self, additional_files=('setup.py',)):
    # Some setuptools versions generate one of these; others don't
    optional_files = {'MANIFEST'}
    all_files = []
    for _, _, filenames in os.walk(six.text_type(self.package_parent)):
      # The generated .pyc files vary a lot. For instance, pytest names them
      # differently.
      all_files.extend(f for f in filenames if not f.endswith('.pyc'))
    expected_files = ['__init__.py', 'test_task.py']
    expected_files.extend(additional_files)
    if 'setup.py' not in additional_files:
      # We want to verify that setup.pyc didn't get created if setup.py was
      # generated.
      self.AssertFileNotExists(os.path.join(self.package_parent, 'setup.pyc'))
    all_files = set(all_files)
    expected_files = set(expected_files) | (all_files & optional_files)
    self.assertSetEqual(all_files, expected_files)

  def testBuildPackagesExisting_Writable(self):
    archive_paths = jobs_prep.BuildPackages(self.package_dir, self.output_dir)
    self._AssertArchivePathsOkay(archive_paths)
    self._AssertPackageDirUnmodified()

  def testBuildPackagesExisting_UsesDistutils(self):
    with open(os.path.join(self.package_parent, 'setup.py'), 'w') as f:
      f.write(
          'from distutils.core import setup\n'
          'if __name__ == "__main__":\n'
          '  setup(name="package1", version="1.0", packages=["test_package"])'
          '\n')
    archive_paths = jobs_prep.BuildPackages(self.package_dir, self.output_dir)
    self._AssertArchivePathsOkay(archive_paths, additional_files=())
    self._AssertPackageDirUnmodified(additional_files=('setup.py', 'MANIFEST'))

  # As it turns out, making a directory read-only on Windows is pretty tricky.
  # It requires the Python Windows extensions.
  @test_case.Filters.DoNotRunOnWindows
  def testBuildPackagesExisting_ReadOnly(self):
    with _UnwritableDirectory(self.package_parent):
      archive_paths = jobs_prep.BuildPackages(self.package_dir, self.output_dir)
    self._AssertArchivePathsOkay(archive_paths)
    self._AssertPackageDirUnmodified()

  def testBuildPackages_Generated(self):
    os.remove(os.path.join(self.package_parent, 'setup.py'))
    archive_paths = jobs_prep.BuildPackages(self.package_dir, self.output_dir)
    self._AssertArchivePathsOkay(archive_paths,
                                 package_name='test_package-0.0.0',
                                 additional_files=())
    self._AssertPackageDirUnmodified(additional_files=())


_GENERATED_SETUP_PY = """\
from setuptools import setup

if __name__ == '__main__':
    setup(name='test_package', packages=['test_package'])
"""
_EXISTING_SETUP_PY = '''\
# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
\"\"\"Dummy setup.py file for testing sdist packaging of user code.\"\"\"

import setuptools

NAME = 'package1'
VERSION = '1.0'

if __name__ == '__main__':
  setuptools.setup(name=NAME, version=VERSION, packages=['test_package'])
'''


@contextlib.contextmanager
def DummyContextManager(value=None):
  """Wraps a value for use as a no-op context manager.

  Example usage:

    >>> with DummyContextManager(42) as foo:
    ...   print foo
    42

  Args:
    value: any value to wrap.

  Yields:
    the given value.
  """
  yield value


_SetuptoolsInvocation = collections.namedtuple(
    '_SetuptoolsInvocation', ['use_cloudsdk_python', 'commands'])


class BuildPackagesUnitTest(base.MlBetaPlatformTestBase):
  """Test BuildPackages, mocking at the execution_utils.Exec level.

  Doesn't *explicitly* cover the case of a very large directory.
  """

  # We want to test that setuptools is run with the proper arguments. In the
  # event of multiple calls, we want to make sure the invocations occur in the
  # correct order.
  # We try from the most complicated to the simplest command, and preferring the
  # Cloud SDK bundled Python environment over the system Python environment.
  SETUPTOOLS_INVOCATIONS = [
      _SetuptoolsInvocation(True, ('egg_info', 'build', 'sdist')),
      _SetuptoolsInvocation(False, ('egg_info', 'build', 'sdist')),
      _SetuptoolsInvocation(True, ('build', 'sdist')),
      _SetuptoolsInvocation(False, ('build', 'sdist')),
      _SetuptoolsInvocation(True, ('sdist',)),
      _SetuptoolsInvocation(False, ('sdist',)),
  ]

  def _MakeFakeRunSetupTools(self, output_files=('trainer-0.0.0.tar.gz',),
                             setup_py_contents=_EXISTING_SETUP_PY,
                             exit_code=None):
    if exit_code is None:
      exit_code = [0]
    setuptools_invocations = self.SETUPTOOLS_INVOCATIONS[:]

    def _GetFlag(args, flag):
      return args[args.index(flag)+1] if flag in args else None

    def _FakeRunSetupTools(args, no_exit, out_func, err_func, cwd, env):
      self.assertTrue(no_exit)
      out_func('Writing to stdout...\n')
      err_func('Writing to stderr...\n')

      self.assertEqual(args[0], 'current/python')

      self.assertEqual(os.path.basename(args[1]), 'setup.py')
      self.AssertFileExistsWithContents(setup_py_contents, args[1])

      setuptools_invocation = setuptools_invocations.pop(0)

      if setuptools_invocation.use_cloudsdk_python:
        self.assertIn('PYTHONPATH', env)
      else:
        self.assertIs(env, None)

      if 'egg_info' in setuptools_invocation.commands:
        self.assertTrue(_GetFlag(args, 'egg_info'))
        self.AssertDirectoryExists(_GetFlag(args, '--egg-base'))
      else:
        self.assertFalse(_GetFlag(args, 'egg_info'))
        self.assertFalse(_GetFlag(args, '--egg-base'))
      if 'build' in setuptools_invocation.commands:
        self.assertTrue(_GetFlag(args, 'build'))
        self.AssertDirectoryExists(_GetFlag(args, '--build-base'))
        self.AssertDirectoryExists(_GetFlag(args, '--build-temp'))
      else:
        self.assertFalse(_GetFlag(args, 'build'))
        self.assertFalse(_GetFlag(args, '--build-base'))
        self.assertFalse(_GetFlag(args, '--build-temp'))
      if 'sdist' in setuptools_invocation.commands:
        self.assertTrue(_GetFlag(args, 'sdist'))
      else:
        raise ValueError('All setuptools invocations should have `sdist`')

      os.unlink(self.Touch(cwd, 'my-package'))  # Make sure we can write to CWD

      dist_dir = _GetFlag(args, '--dist-dir')
      for output_file in output_files:
        self.Touch(dist_dir, output_file, makedirs=True)
      return exit_code.pop(0)
    return _FakeRunSetupTools

  def _RunExpectingPackages(self, expected_packages, package_dir=None):
    packages = jobs_prep.BuildPackages(package_dir or self.package_dir,
                                       self.output_path)
    self.assertSetEqual(
        set(packages),
        {os.path.join(self.output_path, p) for p in expected_packages})

  def SetUp(self):
    self.exec_mock = self.StartObjectPatch(
        execution_utils, 'Exec', side_effect=self._MakeFakeRunSetupTools())
    self.package_root = os.path.join(self.temp_path, 'my-package')

    package = self.Resource('tests', 'unit', 'command_lib', 'ml_engine',
                            'test_data', 'package_root')
    files.CopyTree(package, self.package_root)
    self.output_path = os.path.join(self.temp_path, 'output')
    self.package_dir = os.path.join(self.package_root, 'test_package')

    self.get_python_mock = self.StartObjectPatch(execution_utils,
                                                 'GetPythonExecutable')
    self.get_python_mock.return_value = 'current/python'

  def testBuildPackages(self):
    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_Distutils(self):
    # A setup.py file with distuils will fail on the first execution, but
    # succeed on the second.
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(exit_code=[1, 0])
    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_RelativePath(self):
    with files.ChDir(self.package_root):
      self._RunExpectingPackages(['trainer-0.0.0.tar.gz'],
                                 package_dir=os.path.basename(self.package_dir))

  def testBuildPackages_MultipleOutputFiles(self):
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        output_files=['trainer-0.0.0.tar.gz', 'other-package-0.0.0.tar.gz'])

    self._RunExpectingPackages(['trainer-0.0.0.tar.gz',
                                'other-package-0.0.0.tar.gz'])

  # As it turns out, making a directory read-only on Windows is pretty tricky.
  # It requires the Python Windows extensions.
  @test_case.Filters.DoNotRunOnWindows
  def testBuildPackages_ReadOnly(self):
    with _UnwritableDirectory(self.package_root):
      self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  # As it turns out, making a directory read-only on Windows is pretty tricky.
  # It requires the Python Windows extensions.
  @test_case.Filters.DoNotRunOnWindows
  def testBuildPackages_CannotWriteToWorkingDirectory(self):
    unwriteable_dir = os.path.join(self.temp_path, 'unwritabletempdir')
    os.mkdir(unwriteable_dir)
    self.StartObjectPatch(
        files, 'TemporaryDirectory',
        side_effect=lambda: DummyContextManager(unwriteable_dir))
    with _UnwritableDirectory(self.package_root):
      with _UnwritableDirectory(unwriteable_dir):
        with self.AssertRaisesExceptionMatches(
            jobs_prep.UncopyablePackageError,
            'Cannot write to working location [{}]'.format(
                os.path.join(unwriteable_dir, 'dest'))):
          self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_ExecRaisesOSError(self):
    self.exec_mock.side_effect = OSError
    # While at first blush this seems bad--we don't want to be raising uncaught
    # exceptions--this will give us visibility into error situations.
    # This test is necessary because before we were accidentally quashing these
    # errors.
    with self.assertRaises(OSError):
      self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_CannotWriteToTmp(self):
    self.StartObjectPatch(files, 'TemporaryDirectory', side_effect=OSError)
    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  # As it turns out, making a directory read-only on Windows is pretty tricky.
  # It requires the Python Windows extensions.
  @test_case.Filters.DoNotRunOnWindows
  def testBuildPackages_CannotWriteToTmpAndReadOnly(self):
    self.StartObjectPatch(files, 'TemporaryDirectory', side_effect=OSError)
    with self.AssertRaisesExceptionMatches(
        jobs_prep.UncopyablePackageError,
        ('Cannot copy directory since working directory [{}] is inside of '
         'source directory [{}]').format(self.package_dir, self.package_root)):
      with _UnwritableDirectory(self.package_root):
        self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_NoInitPy(self):
    os.unlink(os.path.join(self.package_dir, '__init__.py'))
    with self.AssertRaisesExceptionMatches(jobs_prep.MissingInitError,
                                           self.package_dir):
      jobs_prep.BuildPackages(self.package_dir, self.output_path)

  def testBuildPackages_GenerateSetupPy(self):
    os.unlink(os.path.join(self.package_root, 'setup.py'))
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        setup_py_contents=_GENERATED_SETUP_PY)

    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_NoSysExecutable(self):
    self.StartDictPatch(os.environ, {}, clear=True)
    self.get_python_mock.side_effect = ValueError()
    with self.assertRaises(jobs_prep.SysExecutableMissingError):
      jobs_prep.BuildPackages(self.package_dir, self.output_path)

  def testBuildPackages_ExecFails(self):
    exit_codes = [1] * len(self.SETUPTOOLS_INVOCATIONS)
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        exit_code=exit_codes)

    with self.AssertRaisesExceptionMatches(
        jobs_prep.SetuptoolsFailedError,
        'Packaging of user Python code failed with message:\n\n'
        'Writing to stdout...\n'
        'Writing to stderr...\n\n\n'
        'Try manually building your Python code'):
      jobs_prep.BuildPackages(self.package_dir, self.output_path)

  def testBuildPackages_ExecFailsGenerated(self):
    os.unlink(os.path.join(self.package_root, 'setup.py'))
    exit_codes = [1] * len(self.SETUPTOOLS_INVOCATIONS)
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        exit_code=exit_codes, setup_py_contents=_GENERATED_SETUP_PY)

    with self.AssertRaisesExceptionMatches(
        jobs_prep.SetuptoolsFailedError,
        'Packaging of user Python code failed with message:\n\n'
        'Writing to stdout...\n'
        'Writing to stderr...\n\n\n'
        'Try manually writing a setup.py file'):
      jobs_prep.BuildPackages(self.package_dir, self.output_path)

  def testBuildPackages_ExecFailsThenPasses(self):
    exit_codes = [1] * (len(self.SETUPTOOLS_INVOCATIONS) - 1) + [0]
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        exit_code=exit_codes)

    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_ExecFailsThenPassesGenerated(self):
    os.unlink(os.path.join(self.package_root, 'setup.py'))
    exit_codes = [1] * (len(self.SETUPTOOLS_INVOCATIONS) - 1) + [0]
    self.exec_mock.side_effect = self._MakeFakeRunSetupTools(
        exit_code=exit_codes, setup_py_contents=_GENERATED_SETUP_PY)

    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  def testBuildPackages_TempDirInSubdir(self):
    # Making a temporary directory *inside* of the package root. This should be
    # fine, as we don't have to copy.
    other_temp_dir = os.path.join(self.package_root, 'tmp')
    files.MakeDir(other_temp_dir)

    self._RunExpectingPackages(['trainer-0.0.0.tar.gz'])

  # As it turns out, making a directory read-only on Windows is pretty tricky.
  # It requires the Python Windows extensions.
  @test_case.Filters.DoNotRunOnWindows
  def testBuildPackages_TempDirInSubdirUnwritable(self):
    # Making a temporary directory *inside* of the package root. This should
    # result in an error, since we *do* have to make a copy here (that would
    # result in an infinite loop).
    other_temp_dir = os.path.join(self.package_root, 'tmp')

    files.MakeDir(other_temp_dir)
    self.StartObjectPatch(files, 'TemporaryDirectory',
                          return_value=DummyContextManager(other_temp_dir))
    with _UnwritableDirectory(self.package_root):
      with self.AssertRaisesExceptionMatches(
          jobs_prep.UncopyablePackageError,
          ('Cannot copy directory since working directory [{}] is inside of '
           'source directory [{}]').format(other_temp_dir, self.package_root)):
        jobs_prep.BuildPackages(self.package_dir, self.output_path)

  def testBuildPackages_SourceDirDoesNotExist(self):
    bad_dir = 'junk/junk'
    with self.AssertRaisesExceptionMatches(
        jobs_prep.InvalidSourceDirError,
        'junk'):
      jobs_prep.BuildPackages(bad_dir, self.output_path)

  def testBuildPackages_ErrorVerifyingWriteAccess(self):
    self.StartObjectPatch(files, 'HasWriteAccessInDir',
                          side_effect=ValueError)
    with self.AssertRaisesExceptionMatches(
        jobs_prep.InvalidSourceDirError,
        os.path.dirname(self.package_dir)):
      jobs_prep.BuildPackages(self.package_dir, self.output_path)


def _FakeUploadFiles(paths, bucket, gs_prefix=None):
  uploaded_files = []
  for _, remote_path in paths:
    uploaded_files.append(
        '/'.join([f for f in [bucket.ToUrl(), gs_prefix, 'DEADBEEF',
                              remote_path] if f]))
  return uploaded_files


def _FakeBuildPackages(package_path, output_dir):
  del package_path  # Unused in _FakeBuildPackages
  return [
      os.path.join(output_dir, 'built-package.tar.gz'),
      os.path.join(output_dir, 'built-package2.whl')
  ]


class UploadPythonPackagesTest(base.MlBetaPlatformTestBase):
  """Test UploadPythonPackages, mocking BuildPackages."""

  def SetUp(self):
    self.build_packages_mock = self.StartObjectPatch(
        jobs_prep, 'BuildPackages', side_effect=_FakeBuildPackages)
    self.upload_mock = self.StartObjectPatch(uploads, 'UploadFiles',
                                             side_effect=_FakeUploadFiles)
    self.bucket_ref = storage_util.BucketReference.FromUrl('gs://bucket/')
    self.staging_location = storage_util.ObjectReference.FromBucketRef(
        self.bucket_ref, 'job_name')

  def testUploadPythonPackages_UploadRequiredButNoStagingLocationGiven(self):
    packages = [os.path.join('path', 'to', 'package.tar.gz'), 'package2.whl']
    with self.assertRaises(jobs_prep.NoStagingLocationError):
      jobs_prep.UploadPythonPackages(packages=packages)

  def testUploadPythonPackages_OnlyLocalPackages(self):
    packages = [os.path.join('path', 'to', 'package.tar.gz'), 'package2.whl']

    storage_paths = jobs_prep.UploadPythonPackages(
        packages=packages, staging_location=self.staging_location)

    self.upload_mock.assert_called_once_with(
        [(packages[0], 'package.tar.gz'), (packages[1], 'package2.whl')],
        self.bucket_ref, 'job_name')
    self.build_packages_mock.assert_not_called()
    self.assertEqual(
        storage_paths,
        [
            'gs://bucket/job_name/DEADBEEF/package.tar.gz',
            'gs://bucket/job_name/DEADBEEF/package2.whl'
        ])

  def testUploadPythonPackages_EmptyStagingLocation(self):
    staging_location = storage_util.ObjectReference.FromBucketRef(
        self.bucket_ref, '')
    packages = [os.path.join('path', 'to', 'package.tar.gz'), 'package2.whl']

    storage_paths = jobs_prep.UploadPythonPackages(
        packages=packages, staging_location=staging_location)

    self.upload_mock.assert_called_once_with(
        [(packages[0], 'package.tar.gz'), (packages[1], 'package2.whl')],
        self.bucket_ref, '')
    self.build_packages_mock.assert_not_called()
    self.assertEqual(
        storage_paths,
        [
            'gs://bucket/DEADBEEF/package.tar.gz',
            'gs://bucket/DEADBEEF/package2.whl'
        ])

  def testUploadPythonPackages_DuplicateFilenames(self):
    packages = [os.path.join('path', 'to', 'package.tar.gz'), 'package.tar.gz']

    with self.AssertRaisesExceptionMatches(
        jobs_prep.DuplicateEntriesError,
        'Cannot upload multiple packages with the same filename: '
        '[package.tar.gz]'):
      jobs_prep.UploadPythonPackages(
          packages=packages, staging_location=self.staging_location)

    self.upload_mock.assert_not_called()
    self.build_packages_mock.assert_not_called()

  def testUploadPythonPackages_OnlyRemotePackages(self):
    packages = ['gs://bucket1/package.tar.gz',
                'gs://bucket2/path/package2.tar.gz']

    storage_paths = jobs_prep.UploadPythonPackages(packages=packages)

    self.upload_mock.assert_not_called()
    self.build_packages_mock.assert_not_called()
    self.assertEqual(storage_paths, packages)

  def testUploadPythonPackages_SourcePackage(self):
    package_path = os.path.join('/path/to/package-root/package_name')

    storage_paths = jobs_prep.UploadPythonPackages(
        package_path=package_path, staging_location=self.staging_location)

    self.build_packages_mock.assert_called_once_with(package_path, mock.ANY)
    self.upload_mock.assert_called_once_with(
        [(mock.ANY, 'built-package.tar.gz'), (mock.ANY, 'built-package2.whl')],
        self.bucket_ref, 'job_name')
    self.assertSetEqual(
        set(storage_paths),
        {
            'gs://bucket/job_name/DEADBEEF/built-package.tar.gz',
            'gs://bucket/job_name/DEADBEEF/built-package2.whl'
        })

  def testUploadPythonPackages_MixedPackages(self):
    package_path = os.path.join('/path/to/package-root/package_name')
    packages = ['gs://bucket1/package.tar.gz',
                'local-package.tar.gz']

    storage_paths = jobs_prep.UploadPythonPackages(
        packages=packages, package_path=package_path,
        staging_location=self.staging_location)

    self.build_packages_mock.assert_called_once_with(package_path, mock.ANY)
    self.upload_mock.assert_has_calls(
        [mock.call(
            [
                ('local-package.tar.gz', 'local-package.tar.gz'),
                (mock.ANY, 'built-package.tar.gz'),
                (mock.ANY, 'built-package2.whl')
            ],
            self.bucket_ref, 'job_name')],
        any_order=True)
    self.assertSetEqual(
        set(storage_paths),
        {
            'gs://bucket1/package.tar.gz',
            'gs://bucket/job_name/DEADBEEF/local-package.tar.gz',
            'gs://bucket/job_name/DEADBEEF/built-package.tar.gz',
            'gs://bucket/job_name/DEADBEEF/built-package2.whl'
        })


class GetStagingLocationTest(test_case.TestCase):
  """Tests for jobs_prep.GetStagingLocation."""

  def SetUp(self):
    self.staging_bucket = storage_util.BucketReference.FromUrl(
        'gs://staging-bucket/')
    self.job_dir = storage_util.ObjectReference.FromUrl(
        'gs://job-bucket/job-dir/')

  def testGetStagingLocation_NoFlags(self):
    self.assertEqual(
        jobs_prep.GetStagingLocation(),
        None)

  def testGetStagingLocation_StagingBucket(self):
    self.assertEqual(
        jobs_prep.GetStagingLocation(job_id='job_id',
                                     staging_bucket=self.staging_bucket),
        storage_util.ObjectReference.FromUrl('gs://staging-bucket/job_id'))

  def testGetStagingLocation_JobDir(self):
    self.assertEqual(
        jobs_prep.GetStagingLocation(job_dir=self.job_dir),
        storage_util.ObjectReference.FromUrl(
            'gs://job-bucket/job-dir/packages'))

  def testGetStagingLocation_JobDirEmptyPrefix(self):
    job_dir = storage_util.ObjectReference.FromUrl('gs://job-bucket',
                                                   allow_empty_object=True)
    self.assertEqual(
        jobs_prep.GetStagingLocation(job_dir=job_dir),
        storage_util.ObjectReference.FromUrl(
            'gs://job-bucket/packages'))

  def testGetStagingLocation_JobDirAndStagingBucket(self):
    self.assertEqual(
        jobs_prep.GetStagingLocation(job_id='job_id', job_dir=self.job_dir,
                                     staging_bucket=self.staging_bucket),
        storage_util.ObjectReference.FromUrl('gs://staging-bucket/job_id'))

if __name__ == '__main__':
  test_case.main()
