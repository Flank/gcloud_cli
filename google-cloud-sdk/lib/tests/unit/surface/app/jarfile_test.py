# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests jarfile.py."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from __future__ import with_statement

import os
import os.path
import shutil

from googlecloudsdk.command_lib.app import jarfile
from googlecloudsdk.core.util import files as file_utils
from tests.lib import test_case
from tests.lib.surface.app import api_test_util


class ManifestParseTest(api_test_util.ApiTestBase):
  """Tests parsing of jar manifests."""

  def SetUp(self):
    self.jars_dir = self.Resource('tests', 'unit', 'surface', 'app',
                                  'test_data', 'jars')

  def testSimple(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
        'Name: com/google/appengine/api/',
        'Implementation-Vendor: Google',
        'Specification-Version: 1.0',
        '',
        'Name: com/google/something/else/',
        'This: that',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(manifest.main_section, {
        'Manifest-Version': '1.0',
        'Created-By': 'ManifestParseTest',
    })
    self.assertEqual(
        manifest.sections, {
            'com/google/appengine/api/': {
                'Name': 'com/google/appengine/api/',
                'Implementation-Vendor': 'Google',
                'Specification-Version': '1.0',
            },
            'com/google/something/else/': {
                'Name': 'com/google/something/else/',
                'This': 'that',
            },
        })

  def testManifestOnly(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(manifest.main_section, {
        'Manifest-Version': '1.0',
        'Created-By': 'ManifestParseTest',
    })
    self.assertEqual(manifest.sections, {})

  def testEmptyManifest(self):
    manifest_string = '\r\n'
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(manifest.main_section, {})
    self.assertEqual(manifest.sections, {})

  def testTrailingBlanks(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
        'Name: com/google/appengine/api/',
        'Implementation-Vendor: Google',
        'Specification-Version: 1.0',
        '',
        'Name: com/google/something/else/',
        'This: that',
        '',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(len(manifest.sections), 2)

  def testTwoBlankLinesBetweenSections(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
        'Name: com/google/appengine/api/',
        'Implementation-Vendor: Google',
        'Specification-Version: 1.0',
        '',
        '',
        'Name: com/google/something/else/',
        'This: that',
        '',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(len(manifest.sections), 2)

  def testThreeBlankLinesBetweenSections(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
        'Name: com/google/appengine/api/',
        'Implementation-Vendor: Google',
        'Specification-Version: 1.0',
        '',
        '',
        '',
        'Name: com/google/something/else/',
        'This: that',
        '',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(len(manifest.sections), 2)

  def testContinuationLines(self):
    manifest_string = '\r\n'.join([
        'Manifest-Version: 1',
        ' .0',
        'Created-By: ManifestParseTest',
        '',
        'Name: com/google/',
        ' appengine/api/',
        'Implementation-Vendor: Go',
        ' ogle',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(manifest.main_section, {
        'Manifest-Version': '1.0',
        'Created-By': 'ManifestParseTest',
    })
    self.assertEqual(
        manifest.sections, {
            'com/google/appengine/api/': {
                'Name': 'com/google/appengine/api/',
                'Implementation-Vendor': 'Google',
            },
        })

  def testUnicode(self):
    manifest_string = u'\r\n'.join([
        'Manifest-Version: 1.0',
        'Created-By: ManifestParseTest',
        '',
        'Name: one',
        'One: 1',
        '',
        'Name: two',
        'Two: 2',
    ])
    manifest = jarfile._ParseManifest(manifest_string, 'dummy.jar')
    self.assertEqual(manifest.main_section, {
        'Manifest-Version': '1.0',
        'Created-By': 'ManifestParseTest',
    })
    self.assertEqual(manifest.sections, {
        'one': {
            'Name': 'one',
            'One': '1',
        },
        'two': {
            'Name': 'two',
            'Two': '2',
        },
    })

  def testParseMissingColon(self):
    self.assertRaisesRegex(
        jarfile.InvalidJarError, r'dummy.jar: Invalid manifest',
        jarfile._ParseManifest, 'Manifest-Version: 1.0\n'
        '\n'
        'Name: yes\n'
        'Forgot the colon\n', 'dummy.jar')

  def testParseMissingName(self):
    self.assertRaisesRegex(
        jarfile.InvalidJarError,
        r'dummy.jar: Manifest entry has no Name attribute: ',
        jarfile._ParseManifest, 'Manifest-Version: 1.0\n'
        '\n'
        'Not-Name: yes\n'
        'Not-Name-Either: also yes\n', 'dummy.jar')

  def testManifestFromJar(self):
    # exploded_jar has a complex MANIFEST.MF entry used for testing.
    dir_name = self.Resource('tests', 'unit', 'surface', 'app', 'test_data',
                             'exploded_jar')
    with file_utils.TemporaryDirectory() as tmp_dir:
      jar_file = os.path.join(tmp_dir, 'foo.jar')
      shutil.make_archive(jar_file, 'zip', dir_name)
      manifest = jarfile.ReadManifest(jar_file + '.zip')
      self.assertIn('Manifest-Version', manifest.main_section)
      self.assertEqual(manifest.main_section['Implementation-Title'], 'Ludo')
      libs = manifest.main_section['Class-Path'].split()
      # Test only the first 3 classpath entries to validate the parsing.
      self.assertEqual(len(libs), 32)
      self.assertEqual(libs[0], 'lib/dependent.jar')
      self.assertEqual(libs[1], 'lib/google-cloud-datastore-1.6.0.jar')
      self.assertEqual(libs[2],
                       'lib/com.google.cloud.google-cloud-core-1.64.0.jar')


if __name__ == '__main__':
  test_case.main()
