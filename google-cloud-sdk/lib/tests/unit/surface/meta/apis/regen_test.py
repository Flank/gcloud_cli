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

"""Tests of the 'gcloud meta apis regen' command."""
import os
import re
import shutil

from googlecloudsdk.command_lib.meta import regen as regen_utils
from tests.lib import cli_test_base


class RegenTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.testdata_dir = self.Resource(
        'tests', 'unit', 'surface', 'meta', 'apis', 'testdata')
    self.regen_config = os.path.join(self.testdata_dir,
                                     'regen_apis_config.yaml')

  def testMissingConfig(self):
    config_file = os.path.join(self.temp_path, 'DOES_NOT_EXIST')
    with self.assertRaisesRegex(
        regen_utils.ConfigFileError,
        ur'{} Not found'.format(re.escape(config_file))):
      self.Run(u'meta apis regen compute/v1 --config {}'.format(config_file))

  def testBadConfig(self):
    config_file = self.Touch(self.temp_path, 'blank')
    with self.assertRaisesRegex(
        regen_utils.ConfigFileError,
        ur'{} does not have format of gcloud api config file'
        .format(re.escape(config_file))):
      self.Run(u'meta apis regen compute/v1 --config {}'.format(config_file))

  def testRegenMissingAPI(self):
    with self.assertRaisesRegex(
        regen_utils.UnknownApi,
        ur'api \[asdfasdf/v1\] not found in "apis" section of {}. '
        ur'Use \[gcloud meta apis list\] to see available apis.'
        .format(re.escape(self.regen_config))):
      self.Run(u'meta apis regen asdfasdf/v1 --config {}'
               .format(self.regen_config))

  def testRegenExistingApi(self):
    shutil.copy(os.path.join(self.testdata_dir, 'cloudresourcemanager_v1.json'),
                self.temp_path)
    self.Run(u'meta apis regen cloudresourcemanager/v1 --config {} '
             u'--base-dir {}'.format(self.regen_config, self.temp_path))
    self.AssertOutputEquals('')
    self.AssertErrEquals(u"""\
Generating cloudresourcemanager v1 from cloudresourcemanager_v1.json
WARNING: {0} does not have __init__.py file, generating ...
WARNING: {0}cloudresourcemanager does not have __init__.py file, generating ...
""".format(os.path.join(self.temp_path, '')))
    self.AssertFileExists(os.path.join(self.temp_path, '__init__.py'))
    code_dir = os.path.join(self.temp_path, 'cloudresourcemanager')
    self.AssertDirectoryExists(code_dir)
    self.AssertFileExists(os.path.join(code_dir, '__init__.py'))
    self.AssertFileExists(os.path.join(code_dir, 'v1', '__init__.py'))
    self.AssertFileExists(os.path.join(code_dir, 'v1', 'resources.py'))
    self.AssertFileExists(
        os.path.join(code_dir, 'v1', 'cloudresourcemanager_v1_client.py'))
    self.AssertFileExists(
        os.path.join(code_dir, 'v1', 'cloudresourcemanager_v1_messages.py'))

  def testRegenNewApi(self):
    tmp_regen_config = os.path.join(self.temp_path,
                                    os.path.basename(self.regen_config))
    shutil.copyfile(self.regen_config, tmp_regen_config)

    discovery_doc = os.path.join(self.testdata_dir, 'apikeys_v1.json')
    shutil.copy(os.path.join(self.testdata_dir, 'cloudresourcemanager_v1.json'),
                self.temp_path)
    self.Run(u'meta apis regen apikeys/v1 --config {} --base-dir {} '
             u'--api-discovery-doc {}'
             .format(tmp_regen_config, self.temp_path, discovery_doc))
    self.AssertOutputEquals('')
    self.AssertErrEquals(u"""\
WARNING: No such api apikeys in config, adding...
Copying in {1}
Generating apikeys v1 from apikeys_v1.json
WARNING: {0} does not have __init__.py file, generating ...
WARNING: {0}apikeys does not have __init__.py file, generating ...
WARNING: Updated {0}regen_apis_config.yaml
""".format(os.path.join(self.temp_path, ''),
           os.path.realpath(discovery_doc)))
    self.AssertFileExists(os.path.join(self.temp_path, '__init__.py'))
    api_map_file = os.path.join(self.temp_path, 'apis_map.py')
    self.AssertFileExists(api_map_file)
    code_dir = os.path.join(self.temp_path, 'apikeys')
    self.AssertDirectoryExists(code_dir)
    self.AssertFileExists(os.path.join(code_dir, '__init__.py'))
    self.AssertFileExists(os.path.join(code_dir, 'v1', '__init__.py'))
    self.AssertFileExists(os.path.join(code_dir, 'v1', 'resources.py'))
    self.AssertFileExists(
        os.path.join(code_dir, 'v1', 'apikeys_v1_client.py'))
    self.AssertFileExists(
        os.path.join(code_dir, 'v1', 'apikeys_v1_messages.py'))
    self.AssertFileContains('apikeys:\n', tmp_regen_config)
    self.AssertFileContains('apikeys', api_map_file)


if __name__ == '__main__':
  cli_test_base.main()
