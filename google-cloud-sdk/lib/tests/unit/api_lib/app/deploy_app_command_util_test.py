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

"""Package containing unit tests for the deploy_app_command_util module.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import json
import os

from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import parallel
from googlecloudsdk.core.util import times
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import cloud_storage_util
from tests.lib.surface.app import source_context_util
from googlecloudsdk.third_party.appengine.api import appinfo
from googlecloudsdk.third_party.appengine.tools import context_util

import mock
import six


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
  for name, contents in six.iteritems(_FILES):
    path = os.path.join(tmp_dir, name)
    _WriteFile(path, contents)


def _WriteFile(file_path, data):
  files.MakeDir(os.path.dirname(file_path))
  with open(file_path, 'w') as fp:
    fp.write(data)
  return file_path


class CopyFilesToCodeBucketTest(
    cloud_storage_util.WithGCSCalls, sdk_test_base.SdkBase):
  """Tests CopyFilesToCodeBucket codepath with threads."""

  _BUCKET = storage_util.BucketReference.FromBucketUrl('gs://somebucket/')
  _BUCKET_NAME = _BUCKET.bucket

  def SetUp(self):
    # Initialize some files
    _CreateFiles(self.temp_path)

    default_app_info = appinfo.AppInfoExternal()
    default_app_info.Set('runtime', 'python27')
    self.default_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'),
        default_app_info)
    self.default_source_dir = os.path.dirname(self.default_module.file)

    extra_app_info = appinfo.AppInfoExternal()
    extra_app_info.Set('runtime', 'python27')
    self.extra_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'extra', 'app.yaml'),
        extra_app_info)
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
    skip_files_app_info.Set('runtime', 'python27')
    skip_files_app_info.Set('skip_files', '^(.*/)?#.*#$')
    self.skip_files_module = yaml_parsing.ServiceYamlInfo(
        os.path.join(self.temp_path, 'app.yaml'), skip_files_app_info)
    self.skip_files_module._has_explicit_skip_files = True
    self.skip_files_source_dir = os.path.dirname(self.skip_files_module.file)

    self.lifecycle_patcher = mock.patch.object(
        deploy_app_command_util,
        '_GetLifecycleDeletePolicy',
        return_value=None)
    self.lifecycle_patcher.start()
    self.addCleanup(self.lifecycle_patcher.stop)

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
    self.ExpectUploads(six.iteritems(_FILES))

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)

    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest)
    self.get_pool_mock.assert_called_once_with(1)

  def testSingleModuleEmptyBucket(self):
    self.ExpectList([])
    self.ExpectUploads(six.iteritems(_FILES))

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.default_source_dir, self._BUCKET)

    self._AssertFilesInManifest(
        [filename.replace('\\', '/') for filename in _FILES],
        manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testSingleModuleLargeFile(self):
    self.ExpectList([])

    # 13 isn't arbitrary, it comes from the largest object in _FILES
    with self.assertRaisesRegex(
        deploy_app_command_util.LargeFileError,
        r'Cannot upload file \[.*\], which has size \[13\] '
        r'\(greater than maximum allowed size of \[12\]\).'):
      deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET,
          max_file_size=12)

  def testSingleModuleEmptyBucketSourceContext(self):
    self.ExpectList([])
    self.ExpectUploads(six.iteritems(_FILES_WITH_SOURCE_CONTEXTS))
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
    all_files = sorted(six.iteritems(_FILES))
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
    self.ExpectUploads(six.iteritems(_FILES))
    # We'll call List again for the second module, and all files should already
    # be uploaded.
    self.ExpectList(six.iteritems(_FILES))

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
    all_files = sorted(six.iteritems(_FILES))
    # Pretend that some of these are already in the bucket.
    existing_files = all_files[:4]
    remaining_files = all_files[4:]
    self.ExpectList(existing_files)
    self.ExpectUploads(remaining_files)
    # We'll call List again for the second module, and all files should already
    # be uploaded.
    self.ExpectList(six.iteritems(_FILES))

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

  def testLifecyclePolicy(self):
    """Check that life cycle policy is inspected.

    The methods are unit tested in other classes. This is more of an integration
    test, to ensure that the actual file upload respects the lifecycle policy.
    """

    # Temporarily disable the lifecycle mocks.
    self.lifecycle_patcher.stop()
    messages = cloud_storage_util.storage_v1
    self.now_mock = self.StartObjectPatch(
        times, 'Now', return_value=datetime.datetime(2018, 4, 30))

    # Expect buckets.Get for lifecycle metadata
    rules = [
        messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=15))
    ]
    self.apitools_client.buckets.Get.Expect(
        messages.StorageBucketsGetRequest(bucket=self._BUCKET_NAME),
        response=messages.Bucket(
            lifecycle=messages.Bucket.LifecycleValue(rule=rules)))

    # The boundary is 2018-04-16 00:00
    file_list = [
        ('somecontents5', datetime.datetime(2018, 4, 15, 23)),
        ('somecontents6', datetime.datetime(2018, 4, 16, 2))]
    objects = messages.Objects(
        items=[messages.Object(name=cloud_storage_util.GetSha(c),
                               timeCreated=d) for c, d in file_list])

    self.apitools_client.objects.List.Expect(
        messages.StorageObjectsListRequest(bucket=self._BUCKET_NAME),
        response=objects
    )

    # We are re-uploading app.yaml due to old age, to be safe
    self.ExpectUploads([('app.yaml', 'somecontents5')])

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.default_module, self.extra_source_dir, self._BUCKET)

    # Only files under extra/ should be in the extra manifest
    extra_module_files = [f for f in _FILES if os.path.dirname(f) == 'extra']
    rel_paths = [os.path.relpath(f, 'extra/') for f in extra_module_files]
    self._AssertFilesInManifest(
        [rel_path.replace('\\', '/') for rel_path in rel_paths],
        manifest)

    # re-enable
    self.lifecycle_patcher.start()

  def testListBucketError(self):
    exception = http_error.MakeHttpError(
        code=404,
        url='https://www.googleapis.com/storage/v1/b/missing_bucket/o',
        message='Not Found',
        reason='notFound')
    self.ExpectListException(exception)

    with self.assertRaisesRegex(
        storage_api.UploadError,
        r'Error uploading files: B \[missing_bucket\] not found: Not Found'):
      deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)

  def testNodeModulesNotUploaded(self):
    files_without_node_modules = {k: v for k, v in _FILES.items()
                                  if not k.startswith('node_modules')}
    self.ExpectList([])
    self.ExpectUploads(six.iteritems(files_without_node_modules))

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
    self.ExpectUploads(six.iteritems(files_without_vendor_dir))

    manifest = deploy_app_command_util.CopyFilesToCodeBucket(
        self.php_module_standard, self.php_source_dir, self._BUCKET)

    self._AssertFilesInManifest([
        filename.replace('\\', '/') for filename in files_without_vendor_dir
    ], manifest)
    self.get_pool_mock.assert_called_once_with(16)

  def testPhpVendorDirUploadedFlex(self):
    self.ExpectList([])
    self.ExpectUploads(six.iteritems(_FILES))

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
      self.ExpectUploads(six.iteritems(files_without_extra_dir))

      manifest = deploy_app_command_util.CopyFilesToCodeBucket(
          self.default_module, self.default_source_dir, self._BUCKET)

      self._AssertFilesInManifest([
          filename.replace('\\', '/') for filename in files_without_extra_dir
      ], manifest)
      self.get_pool_mock.assert_called_once_with(16)
    finally:
      os.remove(gcloudignore_path)


class LifeCyclePolicyTests(cloud_storage_util.WithGCSCalls):
  """Tests for _GetLifeCycleDeletePolicy."""

  def SetUp(self):
    self.bucket_ref = storage_util.BucketReference.FromBucketUrl('gs://bucko/')
    self.storage_client = storage_api.StorageClient()
    self.messages = self.storage_client.messages

  def testNoPolicies(self):
    """Bucket has no lifecycle policies."""
    # Note that the mocking library doesn't check global_params
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        response=self.messages.Bucket(
            lifecycle=self.messages.Bucket.LifecycleValue()))
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, None)

  def testSingleDeletePolicy(self):
    """Bucket has a single delete policy for 15 days."""
    rules = [
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=15))
    ]
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        response=self.messages.Bucket(
            lifecycle=self.messages.Bucket.LifecycleValue(rule=rules)))
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, datetime.timedelta(15))

  def testMultipleDeletePolicies(self):
    """Pick the minimum of multiple policies, and allow extra condition."""
    rules = [
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=15)),
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=10, isLive=True)),
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=13))
    ]
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        response=self.messages.Bucket(
            lifecycle=self.messages.Bucket.LifecycleValue(rule=rules)))
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, datetime.timedelta(10))

  def testWithOtherActionPolicy(self):
    """Policy with SetStorageClass rather than Delete is ignored."""
    rules = [
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='SetStorageClass', storageClass='NearLine'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=10)),
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=15))
    ]
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        response=self.messages.Bucket(
            lifecycle=self.messages.Bucket.LifecycleValue(rule=rules)))
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, datetime.timedelta(15))

  def testDeletePolicy0Day(self):
    """Edge case, delete policy with 0 days is 0 timedelta, not None."""
    rules = [
        self.messages.Bucket.LifecycleValue.RuleValueListEntry(
            action=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ActionValue(type='Delete'),
            condition=self.messages.Bucket.LifecycleValue.RuleValueListEntry.
            ConditionValue(age=0))
    ]
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        response=self.messages.Bucket(
            lifecycle=self.messages.Bucket.LifecycleValue(rule=rules)))
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, datetime.timedelta())

  def testPermissionDenied(self):
    """Assume no lifecycle when no buckets.Get permission.

    Getting the bucket requires GCS Admin privileges.
    File listing and uploading requires only the more narrow GCS Object Admin
    role. In cases where bucket metadata can't be accessed, we assume no
    lifecycle policy, despite that we will mostly be wrong, at time of
    writing.
    """
    exc = http_error.MakeHttpError(
        code=403,
        message='No look! >:( Only put!')
    self.apitools_client.buckets.Get.Expect(
        self.messages.StorageBucketsGetRequest(bucket='bucko'),
        exception=exc)
    delta = deploy_app_command_util._GetLifecycleDeletePolicy(
        self.storage_client, self.bucket_ref)
    self.assertEquals(delta, None)


class TTLFilterTests(sdk_test_base.SdkBase, parameterized.TestCase):
  """Tests for _IsTTLSafe."""

  def SetUp(self):
    self.now_mock = self.StartObjectPatch(
        times, 'Now', return_value=datetime.datetime(2018, 4, 30))
    self.ttl = datetime.timedelta(15)

  @parameterized.parameters(
      (datetime.datetime(2018, 1, 1), False),
      (datetime.datetime(2018, 4, 15), False),
      (datetime.datetime(2018, 4, 15, 23, 59, 59), False),
      (datetime.datetime(2018, 4, 16), True),
      (datetime.datetime(2018, 4, 16, 1), True),
      (datetime.datetime(2030, 1, 1), True))
  def testTTL(self, date, is_safe):
    """Check various dates for whether they are safe from being deleted.

    We have a TTL of 15 days, but with the global margin, we expect anything
    older than 14 days are going to be considered unsafe.

    Args:
      date: datetime.datetime, date to check.
      is_safe: bool, whether the expected outcome is that it is safe.
    """
    obj = mock.Mock()
    obj.timeCreated = date
    self.assertEquals(deploy_app_command_util._IsTTLSafe(self.ttl, obj),
                      is_safe)
    self.now_mock.assert_called_once_with(times.UTC)

  def testNoTTL(self):
    """When no TTL could be found, assume it is safe."""
    obj = mock.Mock()
    obj.timeCreated = datetime.datetime(1999, 1, 1)
    self.assertEquals(deploy_app_command_util._IsTTLSafe(None, obj), True)

if __name__ == '__main__':
  test_case.main()
