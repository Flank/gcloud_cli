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

"""Package containing unit tests for the deploy_app_command_util module.
"""

import json
import os
import re

from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import parallel
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.app import source_context_util
from googlecloudsdk.third_party.appengine.api import appinfo
from googlecloudsdk.third_party.appengine.tools import context_util

import mock


_FILES = {
    'app.yaml': 'somecontents',
    'main.py': 'somecontents1',
    os.path.join('sub', 'main.py'): 'somecontents1',
    'main.html': 'somecontents2',
    os.path.join('sub', 'main.html'): 'somecontents3',
    os.path.join('sub', 'main.css'): 'somecontents4',
    os.path.join('extra', 'app.yaml'): 'somecontents5',
    os.path.join('extra', 'extra.py'): 'somecontents6',
    os.path.join('node_modules/mod1/main.js'): 'javascript1',
    os.path.join('node_modules/test.js'): 'javascript2',
    os.path.join('vendor/init.php'): 'php',
}

_FILES_WITH_SOURCE_CONTEXTS = _FILES.copy()
_FILES_WITH_SOURCE_CONTEXTS.update({
    'source-context.json':
        json.dumps(source_context_util.REMOTE_CONTEXT['context'])
})


def _CreateFiles(tmp_dir):
  for name, contents in _FILES.iteritems():
    path = os.path.join(tmp_dir, name)
    _WriteFile(path, contents)


def _WriteFile(file_path, data):
  files.MakeDir(os.path.dirname(file_path))
  with open(file_path, 'w') as fp:
    fp.write(data)
  return file_path


class BuildStagingDirectoryTest(sdk_test_base.SdkBase):

  _BUCKET = storage_util.BucketReference.FromBucketUrl('gs://somebucket/')

  def _WriteFile(self, file_path, data):
    files.MakeDir(os.path.dirname(file_path))
    with open(file_path, 'w') as fp:
      fp.write(data)
    return file_path

  def SetUp(self):
    self.app_dir = self.CreateTempDir()
    _CreateFiles(self.app_dir)
    self._hashes = {}
    for name, contents in _FILES.iteritems():
      self._hashes[name] = cloud_storage_util.GetSha(contents)

  def TearDown(self):
    del self._hashes

  def _RunTest(self, skip_files, files_that_should_be_copied):
    manifest = deploy_app_command_util._BuildStagingDirectory(
        self.app_dir, self.temp_path, self._BUCKET, re.compile(skip_files))
    for name, content in _FILES.iteritems():
      staging_name = self._hashes[name] + os.path.splitext(name)[1]
      if name in files_that_should_be_copied:
        self.AssertFileExistsWithContents(content, self.temp_path, staging_name)
        self.assertIn(name, manifest)
      else:
        self.assertFalse(os.path.isfile(staging_name))
        self.assertNotIn(name, manifest)

  def testNoSkipFiles(self):
    self._RunTest(r'(?!)', [filename.replace('\\', '/') for filename in _FILES])

  def testSkipFiles(self):
    self._RunTest(
        r'^.*\.css$',
        [f.replace('\\', '/') for f in _FILES if not f.endswith('.css')])

  def testLargeFile(self):
    self.StartPatch('os.path.getsize').return_value = 32 * 1024 * 1024 + 1
    with self.assertRaisesRegexp(
        deploy_app_command_util.LargeFileError,
        r'Cannot upload file \[.*\], which has size \[33554433\] '
        r'\(greater than maximum allowed size of \[33554432\]\).'):
      self._RunTest(r'(?!)',
                    [filename.replace('\\', '/') for filename in _FILES])


class CopyFilesToCodeBucketTest(
    cloud_storage_util.WithGCSCalls, sdk_test_base.SdkBase):
  """Tests CopyFilesToCodeBucket codepath with threads."""

  _BUCKET = storage_util.BucketReference.FromBucketUrl('gs://somebucket/')
  _BUCKET_NAME = _BUCKET.bucket

  def SetUp(self):
    # Initialize some files
    _CreateFiles(self.temp_path)

    self.default_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), appinfo.AppInfoExternal())
    self.default_source_dir = os.path.dirname(self.default_module.file)

    self.extra_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'extra', 'app.yaml'),
        appinfo.AppInfoExternal())
    self.extra_source_dir = os.path.dirname(self.extra_module.file)

    node_app_info = appinfo.AppInfoExternal()
    node_app_info.Set('runtime', 'nodejs8')
    self.node_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), node_app_info)
    self.node_source_dir = os.path.dirname(self.node_module.file)

    php_standard_app_info = appinfo.AppInfoExternal()
    php_standard_app_info.Set('runtime', 'php72')
    self.php_module_standard = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), php_standard_app_info)
    self.php_source_dir = os.path.dirname(self.php_module_standard.file)

    php_flex_app_info = appinfo.AppInfoExternal()
    php_flex_app_info.Set('runtime', 'php72')
    php_flex_app_info.Set('env', 'flex')
    self.php_module_flex = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), php_flex_app_info)

    skip_files_app_info = appinfo.AppInfoExternal()
    skip_files_app_info.Set('skip_files', '^(.*/)?#.*#$')
    self.skip_files_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), skip_files_app_info)
    self.skip_files_module._has_explicit_skip_files = True
    self.skip_files_source_dir = os.path.dirname(self.skip_files_module.file)

    # Mock out the multithreading--this causes all sorts of complications
    # for unit tests, and will be fully tested in the e2e tests. We have full
    # unit/e2e tests for storage_parallel.
    # Need to create a new DummyPool each time because they can only be started
    # once.
    def _MockGetPool(*args, **kwargs):
      del args, kwargs  # Unused in _MockGetPool
      return parallel.DummyPool()
    self.get_pool_mock = self.StartObjectPatch(
        parallel, 'GetPool', side_effect=_MockGetPool, autospec=True)

  def _AssertFilesInManifest(self, file_list, manifest):
    for name in file_list:
      self.assertIn(name, manifest)

  def testSingleModuleEmptyBucketOneThread(self):
    properties.VALUES.app.num_file_upload_threads.Set('1')
    self.ExpectList([])
    self.ExpectUploads(_FILES.iteritems())

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)

    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest)
    self.get_pool_mock.assert_called_once_with(1)

  def testSingleModuleEmptyBucket(self):
    self.ExpectList([])
    self.ExpectUploads(_FILES.iteritems())

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)

    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testSingleModuleLargeFile(self):
    self.ExpectList([])
    self.StartPatch('os.path.getsize').return_value = 32 * 1024 * 1024 + 1

    with self.assertRaisesRegexp(
        deploy_app_command_util.LargeFileError,
        r'Cannot upload file \[.*\], which has size \[33554433\] '
        r'\(greater than maximum allowed size of \[33554432\]\).'):
      deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)

  def testSingleModuleEmptyBucketSourceContext(self):
    self.ExpectList([])
    self.ExpectUploads(_FILES_WITH_SOURCE_CONTEXTS.iteritems())
    with mock.patch.object(
        context_util, '_GetSourceContexts', autospec=True,
        return_value=source_context_util.FAKE_CONTEXTS) as get_source_context:
      manifest = deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)
    get_source_context.assert_called_once_with(
        os.path.dirname(self.default_module.file))
    self._AssertFilesInManifest(
        [filename.replace('\\', '/')
         for filename in _FILES_WITH_SOURCE_CONTEXTS],
        manifest)

  def testSingleModulePartialUpload(self):
    all_files = sorted(_FILES.iteritems())
    # Pretend that two of these are already in the bucket.
    existing_files = all_files[:2]
    remaining_files = all_files[2:]

    self.ExpectList(existing_files)
    self.ExpectUploads(remaining_files)

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)

    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest)

  def testMultiModuleEmptyBucket(self):
    self.ExpectList([])
    self.ExpectUploads(_FILES.iteritems())
    # We'll call List again for the second module, and all files should already
    # be uploaded.
    self.ExpectList(_FILES.iteritems())

    manifest1 = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)
    manifest2 = deploy_app_command_util.CopyFilesToCodeBucket(
        self.extra_module, self.extra_source_dir, self._BUCKET)

    # All files should be in the default manifest
    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest1)
    # Only files under extra/ should be in the extra manifest
    extra_module_files = [f for f in _FILES if os.path.dirname(f) == 'extra']
    rel_paths = [os.path.relpath(f, 'extra/') for f in extra_module_files]
    self._AssertFilesInManifest(
        [rel_path.replace('\\', '/') for rel_path in rel_paths],
        manifest2)

  def testMultiModulePartialUpload(self):
    all_files = sorted(_FILES.iteritems())
    # Pretend that some of these are already in the bucket.
    existing_files = all_files[:4]
    remaining_files = all_files[4:]
    self.ExpectList(existing_files)
    self.ExpectUploads(remaining_files)
    # We'll call List again for the second module, and all files should already
    # be uploaded.
    self.ExpectList(_FILES.iteritems())

    manifest1 = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)
    manifest2 = deploy_app_command_util.CopyFilesToCodeBucket(
        self.extra_module, self.extra_source_dir, self._BUCKET)

    # All files should be in the default manifest
    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest1)
    # Only files under extra/ should be in the extra manifest
    extra_module_files = [f for f in _FILES if os.path.dirname(f) == 'extra']
    rel_paths = [os.path.relpath(f, 'extra/') for f in extra_module_files]
    self._AssertFilesInManifest(
        [rel_path.replace('\\', '/') for rel_path in rel_paths],
        manifest2)

  def testListBucketError(self):
    exception = http_error.MakeHttpError(
        code=404,
        url='https://www.googleapis.com/storage/v1/b/missing_bucket/o',
        message='Not Found',
        reason='notFound')
    self.ExpectListException(exception)

    with self.assertRaisesRegexp(
        storage_api.UploadError,
        r'Error uploading files: B \[missing_bucket\] not found: Not Found'):
      deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)

  def testNodeModulesNotUploaded(self):
    files_without_node_modules = {k: v for k, v in _FILES.items()
                                  if not k.startswith('node_modules')}
    self.ExpectList([])
    self.ExpectUploads(files_without_node_modules.iteritems())

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.node_module, self.node_source_dir, self._BUCKET)

    self._AssertFilesInManifest([
        filename.replace('\\', '/') for filename in files_without_node_modules
    ], manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testPhpVendorDirNotUploadedStandard(self):
    files_without_vendor_dir = {k: v for k, v in _FILES.items()
                                if not k.startswith('vendor')}
    self.ExpectList([])
    self.ExpectUploads(files_without_vendor_dir.iteritems())

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.php_module_standard, self.php_source_dir, self._BUCKET)

    self._AssertFilesInManifest([
        filename.replace('\\', '/') for filename in files_without_vendor_dir
    ], manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testPhpVendorDirUploadedFlex(self):
    self.ExpectList([])
    self.ExpectUploads(_FILES.iteritems())

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.php_module_flex, self.php_source_dir, self._BUCKET)

    # Since the default skip_files for flex env contains node_modules, instead
    # of checking that every file was uploaded, just check for vendor/init.php
    self._AssertFilesInManifest(['vendor/init.php'], manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testUsesExistingGcloudignore(self):
    gcloudignore_path = os.path.join(self.default_source_dir,
                                     '.gcloudignore')
    _WriteFile(gcloudignore_path, 'extra/')
    try:
      files_with_gcloudignore = _FILES.copy()
      files_with_gcloudignore['.gcloudignore'] = 'extra/'
      files_without_extra_dir = {
          k: v
          for k, v in files_with_gcloudignore.items()
          if not k.startswith('extra')
      }
      self.ExpectList([])
      self.ExpectUploads(files_without_extra_dir.iteritems())

      manifest = deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)

      self._AssertFilesInManifest([
          filename.replace('\\', '/') for filename in files_without_extra_dir
      ], manifest)
      self.get_pool_mock.assert_called_once_with(16)
    finally:
      os.remove(gcloudignore_path)


if __name__ == '__main__':
  test_case.main()
