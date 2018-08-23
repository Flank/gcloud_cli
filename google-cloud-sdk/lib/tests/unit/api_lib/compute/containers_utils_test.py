# -*- coding: utf-8 -*- #
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
"""Tests for googlecloudsdk.api_lib.compute.containers_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


class ContainersUtilsTest(sdk_test_base.WithTempCWD, test_case.TestCase):

  def SetUp(self):
    self.cos_prefix = 'cos-stable-55'
    self.messages = core_apis.GetMessagesModule('compute', 'alpha')

  def testSelectNewestCosImage(self):
    m = self.messages
    images = [
        m.Image(
            name=(self.cos_prefix + '-1-1-0'),
            creationTimestamp='2016-05-05T18:52:15.455-07:00',
            selfLink='link-1'
        ),
        m.Image(
            name='cos-beta-55-0-0-0',
            creationTimestamp='2016-06-06T18:52:15.455-07:00',
            selfLink='link-beta-0'
        ),
        m.Image(
            name=(self.cos_prefix + '-1-3-0'),
            creationTimestamp='2016-05-07T18:52:15.455-07:00',
            selfLink='link-3'
        ),
        m.Image(
            name=(self.cos_prefix + '-1-2-0'),
            creationTimestamp='2016-05-06T18:52:15.455-07:00',
            selfLink='link-2'
        ),
    ]
    cos_image_link = containers_utils._SelectNewestCosImage(images)
    self.assertEqual('link-3', cos_image_link)

  def testSelectNoCosImage(self):
    m = self.messages
    images = [
        m.Image(
            name='cos-beta-55-0-0-0',
            creationTimestamp='2016-06-06T18:52:15.455-07:00',
            selfLink='link-beta-0'
        ),
        m.Image(
            name='cos-alpha-54-1-3-0',
            creationTimestamp='2016-05-07T18:52:15.455-07:00',
            selfLink='link-3'
        ),
    ]
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Could not find COS \(Cloud OS\) for release family '
        r'\'' + self.cos_prefix + '\''):
      containers_utils._SelectNewestCosImage(images)

  def testManifestWithoutVolumeMounts(self):
    metadata = {'spec': {'containers': [{}]}}
    containers_utils._CleanupMounts(metadata, [], [], [])
    self.assertEqual(metadata, {
        'spec': {
            'containers': [{
                'volumeMounts': []
            }],
            'volumes': []
        }
    })

  def testRemoveContainerEnv(self):
    manifest = {
        'spec': {
            'containers': [{
                'env': [{
                    'name': 'A',
                    'value': 'A'
                }, {
                    'name': 'C',
                    'value': 'C'
                }]
            }]
        }
    }
    containers_utils._UpdateEnv(manifest, ['A', 'B'], None, [])
    self.assertEqual(manifest, {
        'spec': {
            'containers': [{
                'env': [{
                    'name': 'C',
                    'value': 'C'
                }]
            }]
        }
    })

  def testReadEnvVars(self):
    file_name = 'env_vars.correct'
    file_content = """\
# Comment
ENV0=1234

_MY_ENV_= asdf  # Not a comment
"""

    with open(file_name, 'w') as f:
      f.write(file_content)

    env_vars = containers_utils._ReadDictionary(file_name)
    self.assertDictEqual(env_vars,
                         {'ENV0': '1234',
                          '_MY_ENV_': ' asdf  # Not a comment'})

    env_vars = containers_utils._ReadDictionary(None)
    self.assertDictEqual(env_vars, {})

  def testReadEnvVarsErrors(self):
    file_name = 'env_vars.corrupted'
    file_content = 'asdf'

    # File doesn't exist
    with self.assertRaisesRegex(files.Error,
                                '.*env_vars.corrupted.*'):
      containers_utils._ReadDictionary(file_name)

    with open(file_name, 'w') as f:
      f.write(file_content)

    # File has wrong format
    with self.assertRaisesRegex(
        exceptions.BadFileException,
        '.*Syntax error in env_vars.corrupted:0: Expected VAR=VAL, got asdf.*'
    ):
      containers_utils._ReadDictionary(file_name)

  def testReadEnvVarMalformedName(self):
    file_name = 'env_vars.malformed'
    file_content = 'key =value'

    with open(file_name, 'w') as f:
      f.write(file_content)

    # File has wrong format
    with self.assertRaisesRegex(
        exceptions.BadFileException,
        'Syntax error in env_vars.malformed:0 Variable name cannot contain '
        'whitespaces, got "key "'):
      containers_utils._ReadDictionary(file_name)

  def testDumpYamlHasDisclaimer(self):
    self.assertTrue('# DISCLAIMER' in containers_utils.DumpYaml({}))


if __name__ == '__main__':
  test_case.main()
