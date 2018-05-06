# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Integration test for the 'functions deploy' command."""
import os

from googlecloudsdk.api_lib.functions import exceptions
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.e2e_utils import GetResourceNameGenerator
from tests.lib.sdk_test_base import WithTempCWD

PACKAGE_JSON_FILE = """{
        "name": "test",
        "version": "0.0.1",
        "main": "functions.js"
        }"""

FUNCTION_JS_FILE = """exports.function = function(context, data) {
        console.log('hello');
        context.success('it works');
        };
        """


class DeployIntegrationTest(e2e_base.WithServiceAuth, WithTempCWD):

  def _PrepareFunctionFiles(self):
    path = self.CreateTempDir()
    with open(os.path.join(path, 'package.json'), 'w') as f:
      f.write(PACKAGE_JSON_FILE)
    with open(os.path.join(path, 'functions.js'), 'w') as f:
      f.write(FUNCTION_JS_FILE)
    return path

  def _CreateOversizedFile(self, parent_dir, file_name, subdir=''):
    if subdir:
      os.makedirs(os.path.join(parent_dir, subdir))
    with open(os.path.join(parent_dir, subdir, file_name), 'w') as f:
      f.write(' ' * (512 * 2**20 + 1))

  def SetUp(self):
    self.function_path = self._PrepareFunctionFiles()
    generator = GetResourceNameGenerator(
        prefix='function-deploy', sequence_start=0)
    self.function_name = generator.next()
    self.track = calliope_base.ReleaseTrack.BETA
    self.delete_function_on_tear_down = True

  def testDeployHttp(self):
    self.Run(
        'functions deploy {0} '
        '--source={1} '
        '--trigger-http '
        '--entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployCloudPubSub(self):
    self.Run(
        'functions deploy {0} '
        '--source={1} '
        '--trigger-topic test-topic '
        '--entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployCloudStorage(self):
    self.Run(
        'functions deploy {0} '
        '--source={1} '
        '--trigger-bucket e2e-input-functions --entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployCloudPubSubWithNewFlags(self):
    self.Run(
        'functions deploy {0} '
        '--source {1} '
        '--trigger-event providers/cloud.pubsub/eventTypes/topic.publish '
        '--trigger-resource test-topic --entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployRespectingGcloudIgnoreToSucceed(self):
    self._dirs_size_limit_method = 513 * (2 **20)
    self._CreateOversizedFile(self.function_path, 'trash')
    with open(os.path.join(self.function_path, '.gcloudignore'), 'w') as f:
      f.write('trash')
    # The deployment will fail if it doesn't skip trash file because it's
    # uncompressed size will be over allowed max of 512MB.
    self.Run(
        'functions deploy {0} '
        '--source {1} '
        '--stage-bucket e2e-input-functions '
        '--trigger-http --entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployCreatingGcloudignore(self):
    self._dirs_size_limit_method = 513 * (2 **20)
    self._CreateOversizedFile(self.function_path, 'trash', 'node_modules')
    with open(os.path.join(self.function_path, '.gitignore'), 'w') as f:
      f.write('something')
    # The deployment will fail if it doesn't skip node_modules directory because
    # it's uncompressed size will be over allowed max of 512MB.
    self.Run(
        'functions deploy {0} '
        '--source {1} '
        '--stage-bucket e2e-input-functions '
        '--trigger-http --entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployCreatingGcloudignoreWithOnly_node_modules(self):
    self._dirs_size_limit_method = 513 * (2 **20)
    self._CreateOversizedFile(self.function_path, 'trash', 'node_modules')
    # The deployment will fail if it doesn't skip node_modules directory because
    # it's uncompressed size will be over allowed max of 512MB.
    self.Run(
        'functions deploy {0} '
        '--source {1} '
        '--stage-bucket e2e-input-functions '
        '--trigger-http --entry-point function'.format(
            self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self.AssertOutputContains(self.function_name)

  def testDeployRespectingGcloudIgnoreToFail(self):
    self._dirs_size_limit_method = 513 * (2 **20)
    self.delete_function_on_tear_down = False
    self._CreateOversizedFile(self.function_path, 'trash')
    with open(os.path.join(self.function_path, '.gcloudignore'), 'w') as f:
      f.write('debris')
    # The deployment will fail if because it doesn't skip trash file, it's
    # uncompressed size is over allowed max of 512MB.
    with self.assertRaisesRegex(
        exceptions.OversizedDeployment,
        (r'Uncompressed deployment is \d+B, bigger than maximum allowed '
         r'size of \d+B')):
      self.Run(
          'functions deploy {0} '
          '--source {1} '
          '--stage-bucket e2e-input-functions '
          '--trigger-http --entry-point function'.format(
              self.function_name, self.function_path))
    # test-topic is created automatically and automatically cleaned-up
    self.Run('functions list')
    self. AssertOutputNotContains(self.function_name)

  def testDeployChangeSourceType(self):
    self.Run(
        'functions deploy {0} '
        '--source={1} '
        '--trigger-http '
        '--entry-point function'.format(
            self.function_name, self.function_path))
    # No exceptions being thrown is proof of update success.
    self.Run(
        'functions deploy {0} '
        '--source '
        'https://source.developers.google.com/projects/'
        'cloud-sdk-integration-testing/'
        'repos/foom/moveable-aliases/master/paths//'.format(self.function_name))

  def TearDown(self):
    # Calling this from AddCleanup handler will trigger an exception
    # FIXME(b/32226349)
    if self.delete_function_on_tear_down:
      self.Run('functions delete ' + self.function_name)

if __name__ == '__main__':
  test_case.main()
