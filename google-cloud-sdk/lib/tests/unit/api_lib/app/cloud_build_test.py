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

"""Unit tests for deploy_command_util."""

import gzip
import json
import os
import re
import tarfile

from apitools.base.py.testing import mock as api_mock

from googlecloudsdk.api_lib.app import cloud_build
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.app import source_context_util
from tests.lib.surface.app import util as test_util
import mock

# pylint: disable=anomalous-backslash-in-string
APP_DATA = """\
api_version: 1
env: flex
threadsafe: true

handlers:
- url: /
  script: home.app
- url: /static
  static_dir: foo
skip_files:
- ^.*\.zip$
- .*subdir.*
"""
# pylint: enable=anomalous-backslash-in-string


class TarfileTest(cli_test_base.CliTestBase,
                  sdk_test_base.WithFakeAuth,
                  test_util.WithAppData):
  """Test cloud_build.UploadSource."""

  def SetUp(self):
    self.storage_client = api_mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.storage_client.Mock()
    self.addCleanup(self.storage_client.Unmock)
    self.storage_messages = core_apis.GetMessagesModule('storage', 'v1')
    # The size of the tar generated is slightly non-deterministic. Just patch
    # it to 1.
    self.get_size = self.StartObjectPatch(storage_api, '_GetFileSize')
    self.get_size.return_value = 1
    self.object_ref = storage_util.ObjectReference.FromUrl('gs://bucket/object')

  def _ExpectUpload(self, exception=None):
    if exception:
      response = None
    else:
      response = self.storage_messages.Object(size=1)

    self.storage_client.objects.Insert.Expect(
        self.storage_messages.StorageObjectsInsertRequest(
            bucket='bucket',
            name='object',
            object=self.storage_messages.Object(size=1)
        ),
        response=response,
        exception=exception
    )

  def testUpload(self):
    """Test basic upload with single file."""
    tmp = self.CreateTempDir('project')
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref)

  def testUploadWithGenFiles(self):
    """Test that generated files passed to UploadSource don't raise error."""
    tmp = self.CreateTempDir('project')
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    gen_files = {'Dockerfile': 'empty'}
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref, gen_files=gen_files)

  def testFailure(self):
    """Test HttpError raises to user."""
    tmp = self.CreateTempDir('project')
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self._ExpectUpload(
        exception=http_error.MakeHttpError())
    with self.assertRaises(exceptions.BadFileException):
      cloud_build.UploadSource(tmp, self.object_ref)

  def testUploadWithGeneratedDockerignore(self):
    """Test that UploadSource correctly interprets generated .dockerignore."""
    tmp = self.CreateTempDir('project')
    create_tar_mock = self.StartObjectPatch(cloud_build, '_CreateTar')
    create_tar_mock.return_value = 1
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    gen_files = {'.dockerignore': 'main.py'}
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref, gen_files)
    # Test that _CreateTar was called with the correct directory, files, and
    # exclusions
    create_tar_mock.assert_called_once_with(
        tmp,
        gen_files,
        {'Dockerfile', 'fake.zip', 'tmpsubdir',
         os.path.join('tmpsubdir', 'fake2.zip')},
        mock.ANY)

  def testUploadWithDockerignore(self):
    """Test that UploadSource correctly interprets .dockerignore on disk."""
    tmp = self.CreateTempDir('project')
    create_tar_mock = self.StartObjectPatch(cloud_build, '_CreateTar')
    create_tar_mock.return_value = 1
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, '.dockerignore'), 'main.py')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref)
    self.assertEqual(create_tar_mock.call_count, 1)
    # Test that _CreateTar was called with the correct directory, files, and
    # exclusions
    create_tar_mock.assert_called_once_with(
        tmp,
        {},
        {'Dockerfile', '.dockerignore', 'fake.zip', 'tmpsubdir',
         os.path.join('tmpsubdir', 'fake2.zip')},
        mock.ANY)

  def testUploadWithSkipFilesRegex(self):
    """Test that UploadSource correctly skips files when regex is given."""
    tmp = self.CreateTempDir('project')
    create_tar_mock = self.StartObjectPatch(cloud_build, '_CreateTar')
    create_tar_mock.return_value = 1
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'app.yaml'), APP_DATA)
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    # Read app data to get the skip files regex.
    info = yaml_parsing.ServiceYamlInfo.FromFile(os.path.join(tmp, 'app.yaml'))
    skip = info.parsed.skip_files.regex
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref, skip_files=skip)
    # Assert that _CreateTar was called with the correct directory, files, and
    # exclusions
    create_tar_mock.assert_called_once_with(
        tmp, {}, {'app.yaml', 'Dockerfile', 'main.py'}, mock.ANY)

  def testUploadWithSkipFilesRegexAndDockerignore(self):
    """Same as above, but with a dockerignore file as well."""
    tmp = self.CreateTempDir('project')
    create_tar_mock = self.StartObjectPatch(cloud_build, '_CreateTar')
    create_tar_mock.return_value = 1
    self.SetSdkRoot('FakeRoot')
    self.WriteFile(os.path.join(tmp, 'app.yaml'), APP_DATA)
    self.WriteFile(os.path.join(tmp, 'Dockerfile'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, '.dockerignore'), 'main.py')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    # Make sure subdirectories that aren't supposed to be ignored are
    # included.
    os.mkdir(os.path.join(tmp, 'anothersubdir'))
    self.WriteFile(os.path.join(tmp, 'anotherdir', 'fake3.txt'), 'Dummy')
    # Read app data to get the skip files regex.
    info = yaml_parsing.ServiceYamlInfo.FromFile(os.path.join(tmp, 'app.yaml'))
    skip = info.parsed.skip_files.regex
    self._ExpectUpload()
    cloud_build.UploadSource(tmp, self.object_ref, skip_files=skip)
    # Assert that _CreateTar was called with the correct directory, files, and
    # exclusions
    create_tar_mock.assert_called_once_with(
        tmp, {},
        {'app.yaml', 'Dockerfile', '.dockerignore',
         os.path.join('anotherdir', 'fake3.txt')},
        mock.ANY)

  def testCreateTar(self):
    """Test _CreateTar correctly creates tarfile incl. subdirectories."""
    # Create directory
    tmp = self.CreateTempDir('project')
    self.WriteFile(os.path.join(tmp, 'app.yaml'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    # Create generated files
    source_context = json.dumps(source_context_util.FAKE_CONTEXTS)
    gen_files = {'Dockerfile': 'empty',
                 'source-context.json': source_context}
    # Call _CreateTar
    with open(os.path.join(tmp, 'tmp.tgz'), 'w+b') as f:
      with gzip.GzipFile(mode='wb', fileobj=f) as gz:
        cloud_build._CreateTar(tmp,
                               gen_files,
                               {'app.yaml', 'main.py', 'fake.zip', 'tmpsubdir',
                                os.path.join('tmpsubdir', 'fake2.zip')},
                               gz)
    # Extract tar to check contents
    t = tarfile.open(os.path.join(tmp, 'tmp.tgz'), 'r:gz')
    dest_tmp = self.CreateTempDir('extracted')
    t.extractall(dest_tmp)
    self.assertEqual(set(os.listdir(dest_tmp)),
                     {'app.yaml', 'main.py', 'Dockerfile',
                      'source-context.json', 'fake.zip', 'tmpsubdir'})
    self.assertEqual(set(os.listdir(os.path.join(dest_tmp, 'tmpsubdir'))),
                     {'fake2.zip'})
    with open(os.path.join(dest_tmp, 'Dockerfile')) as f:
      self.assertEqual(f.read(), 'empty')
    with open(os.path.join(dest_tmp, 'source-context.json')) as f:
      self.assertEqual(json.loads(f.read()),
                       source_context_util.FAKE_CONTEXTS)

  def testCreateTar_SomeFilesExcluded(self):
    """Test _CreateTar correctly creates tarfile from subset of root dir."""
    # Create directory
    tmp = self.CreateTempDir('project')
    self.WriteFile(os.path.join(tmp, 'app.yaml'), 'empty')
    self.WriteFile(os.path.join(tmp, 'main.py'), 'empty')
    self.WriteFile(os.path.join(tmp, 'fake.zip'), 'Dummy')
    os.mkdir(os.path.join(tmp, 'tmpsubdir'))
    self.WriteFile(os.path.join(tmp, 'tmpsubdir', 'fake2.zip'), 'Dummy')
    # Create generated files
    source_context = json.dumps(source_context_util.FAKE_CONTEXTS)
    gen_files = {'Dockerfile': 'empty',
                 'source-context.json': source_context}
    # Call _CreateTar
    with open(os.path.join(tmp, 'tmp.tgz'), 'w+b') as f:
      with gzip.GzipFile(mode='wb', fileobj=f) as gz:
        cloud_build._CreateTar(tmp,
                               gen_files,
                               {'app.yaml', 'main.py'},
                               gz)
    # Extract tar to check contents
    t = tarfile.open(os.path.join(tmp, 'tmp.tgz'), 'r:gz')
    dest_tmp = self.CreateTempDir('extracted')
    t.extractall(dest_tmp)
    self.assertEqual(set(os.listdir(dest_tmp)),
                     {'app.yaml', 'main.py', 'Dockerfile',
                      'source-context.json'})

  def SetSdkRoot(self, value):
    self.StartPropertyPatch(config.Paths, 'sdk_root', return_value=value)


class CloudBuildTest(test_case.TestCase):
  """Test cloud_build.GetDefaultBuild and .FixUpBuild."""

  _OUTPUT_IMAGE = 'gcr.io/my-project/output-tag'

  def SetUp(self):
    self.messages = cloudbuild_util.GetMessagesModule()
    self.object_ref = storage_util.ObjectReference.FromUrl(
        'gs://bucket/path/object.tgz')
    for prop in (properties.VALUES.app.container_builder_image,
                 properties.VALUES.app.cloud_build_timeout):
      self.addCleanup(prop.Set, prop.Get())

  def testGetDefaultBuild(self):
    self.assertEqual(
        cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE),
        self.messages.Build(
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', self._OUTPUT_IMAGE, '.'])],
            images=[self._OUTPUT_IMAGE]))

  def testGetDefaultBuild_DifferentBuilderImage(self):
    properties.VALUES.app.container_builder_image.Set('gcr.io/other_image')
    self.assertEqual(
        cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE),
        self.messages.Build(
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/other_image',
                    args=['build', '-t', self._OUTPUT_IMAGE, '.'])],
            images=[self._OUTPUT_IMAGE]))

  def testFixUpBuild(self):
    basic_build = cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE)
    self.assertEqual(
        cloud_build.FixUpBuild(basic_build, self.object_ref),
        self.messages.Build(
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', self._OUTPUT_IMAGE, '.'])],
            images=[self._OUTPUT_IMAGE],
            logsBucket='bucket',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='path/object.tgz'))))

  def testFixUpBuild_Timeout(self):
    properties.VALUES.app.cloud_build_timeout.Set(100)
    basic_build = cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE)
    self.assertEqual(
        cloud_build.FixUpBuild(basic_build, self.object_ref),
        self.messages.Build(
            steps=[
                self.messages.BuildStep(
                    name='gcr.io/cloud-builders/docker',
                    args=['build', '-t', self._OUTPUT_IMAGE, '.'])],
            images=[self._OUTPUT_IMAGE],
            logsBucket='bucket',
            timeout='100s',
            source=self.messages.Source(
                storageSource=self.messages.StorageSource(
                    bucket='bucket',
                    object='path/object.tgz'))))

  def testFixUpBuild_InvalidBuild(self):
    basic_build = cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE)
    basic_build.source = self.messages.Source()
    with self.assertRaisesRegex(cloud_build.InvalidBuildError, re.escape(
        'Field [source] was provided, but should not have been. '
        'You may be using an improper Cloud Build pipeline.')):
      cloud_build.FixUpBuild(basic_build, self.object_ref)

    basic_build = cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE)
    basic_build.timeout = '100s'
    with self.assertRaisesRegex(cloud_build.InvalidBuildError, re.escape(
        'Field [timeout] was provided, but should not have been. '
        'You may be using an improper Cloud Build pipeline.')):
      cloud_build.FixUpBuild(basic_build, self.object_ref)

    basic_build = cloud_build.GetDefaultBuild(self._OUTPUT_IMAGE)
    basic_build.logsBucket = 'bucket'
    with self.assertRaisesRegex(cloud_build.InvalidBuildError, re.escape(
        'Field [logsBucket] was provided, but should not have been. '
        'You may be using an improper Cloud Build pipeline.')):
      cloud_build.FixUpBuild(basic_build, self.object_ref)


if __name__ == '__main__':
  test_case.main()
