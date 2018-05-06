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

from __future__ import absolute_import
from __future__ import unicode_literals
import io
import json
import os
import time

from googlecloudsdk.core import config
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.util import platforms
from tests.lib import test_case
from tests.lib.core.updater import util
import six
from six.moves import range  # pylint: disable=redefined-builtin


class ParseTests(util.Base):

  def CheckEquality(self, first, second):
    """Checks to see if 2 json schemas are equal."""
    self.assertEqual(type(first), type(second),
                     msg='{0} != {1}'.format(first, second))
    if isinstance(first, list):
      for i in range(len(first)):
        self.CheckEquality(first[i], second[i])
    elif isinstance(first, dict):
      for key, v1 in six.iteritems(first):
        if key in second:
          self.CheckEquality(v1, second[key])
        elif v1:
          # Only fail if the key is not found and the value is not False, or
          # an empty collection.
          self.fail('Key {key}:{val} not in dictionary: {other}'.format(
              key=key, val=v1, other=second))
    else:
      self.assertEqual(first, second)

  def testBasicParse(self):
    json_file = self.Resource('parsetest.json')
    snapshot = snapshots.ComponentSnapshot.FromFile(json_file)
    self.assertEqual(3, len(snapshot.components))
    self.assertEqual(snapshot.sdk_definition.LastUpdatedString(), '2000/01/01')

    with io.open(json_file, 'rt') as input_file:
      raw_data = json.load(input_file)

    full_url = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         raw_data['schema_version']['url']))
    raw_data['schema_version']['url'] = full_url
    full_notes = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         raw_data['release_notes_url']))
    raw_data['release_notes_url'] = full_notes
    full_source = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         'someurl'))
    raw_data['components'][1]['data']['source'] = full_source
    # Unknown enums turn into None.
    raw_data['components'][1]['platform'] = {
        'operating_systems': [None, 'WINDOWS'],
        'architectures': [None, 'x86'],
    }
    new_data = snapshot.sdk_definition.ToDictionary()
    self.CheckEquality(raw_data, new_data)

  def testParseFromURL(self):
    json_file = self.Resource('parsetest.json')
    snapshot = snapshots.ComponentSnapshot.FromURLs(self.URLFromFile(json_file))
    self.assertEqual(3, len(snapshot.components))

    with open(json_file) as input_file:
      raw_data = json.load(input_file)

    full_url = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         raw_data['schema_version']['url']))
    raw_data['schema_version']['url'] = full_url
    full_notes = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         raw_data['release_notes_url']))
    raw_data['release_notes_url'] = full_notes
    full_source = six.text_type(
        self.URLFromFile(os.path.dirname(json_file),
                         'someurl'))
    raw_data['components'][1]['data']['source'] = full_source
    # Unknown enums turn into None.
    raw_data['components'][1]['platform'] = {
        'operating_systems': [None, 'WINDOWS'],
        'architectures': [None, 'x86'],
    }
    new_data = snapshot.sdk_definition.ToDictionary()
    self.CheckEquality(raw_data, new_data)

  def testMerge(self):
    json_file = self.Resource('parsetest.json')
    with open(json_file) as fp:
      sdk_def = schemas.SDKDefinition.FromDictionary(json.load(fp))
    sdk_def2 = schemas.SDKDefinition.FromDictionary(
        {
            'revision': 20020101000000,
            'components': [
                {
                    'id': 'c3',
                    'details': {
                        'display_name': 'component3',
                        'description': 'This is component 3'
                    },
                    'version': {
                        'build_number': 1,
                        'version_string': '1.0.0'
                    }
                }
            ]
        })

    sdk_def.Merge(sdk_def2)
    self.assertEqual(20000101000000, sdk_def.revision)
    self.assertEqual(3, len(sdk_def.components))
    self.assertEqual('c1', sdk_def.components[0].id)
    self.assertEqual('c2', sdk_def.components[1].id)
    self.assertEqual('c3', sdk_def.components[2].id)

    sdk_def3 = schemas.SDKDefinition.FromDictionary(
        {
            'revision': 20030101000000,
            'components': [
                {
                    'id': 'c1',
                    'details': {
                        'display_name': 'component3',
                        'description': 'This is component 3'
                    },
                    'version': {
                        'build_number': 3,
                        'version_string': '1.0.0'
                    }
                }
            ]
        })

    sdk_def.Merge(sdk_def3)
    self.assertEqual(20000101000000, sdk_def.revision)
    self.assertEqual(3, len(sdk_def.components))
    self.assertEqual('c2', sdk_def.components[0].id)
    self.assertEqual('c3', sdk_def.components[1].id)
    self.assertEqual('c1', sdk_def.components[2].id)
    self.assertEqual(3, sdk_def.components[2].version.build_number)

  def testBadSchemaVersion(self):
    sdk_def = schemas.SDKDefinition(
        revision=1,
        schema_version=schemas.SchemaVersion(
            config.INSTALLATION_CONFIG.snapshot_schema_version + 1,
            no_update=False, message='', url=''),
        release_notes_url=None,
        version=None,
        gcloud_rel_path=None,
        post_processing_command=None,
        components=[],
        notifications={})

    with self.assertRaises(snapshots.IncompatibleSchemaVersionError):
      snapshots.ComponentSnapshot._FromDictionary((sdk_def.ToDictionary(),
                                                   None))

  def testErrors(self):
    class BogusClass(object):
      pass

    p = schemas.DictionaryParser(BogusClass, {'b': ['c'], 'd': 'e'})
    with self.assertRaisesRegex(
        schemas.ParseError,
        r'Required field \[a\] not found while parsing \[.*BogusClass.*\]'):
      p.Parse('a', required=True)

    with self.assertRaisesRegex(
        schemas.ParseError,
        r'Did not expect a list for field \[b\] in component '
        r'\[.*BogusClass.*\]'):
      p.Parse('b', required=True)

    with self.assertRaisesRegex(
        schemas.ParseError,
        r'Expected a list for field \[d\] in component \[.*BogusClass.*\]'):
      p.ParseList('d', required=True)

    with self.assertRaisesRegex(
        schemas.ParseError,
        r'Expected a dict for field \[d\] in component \[.*BogusClass.*\]'):
      p.ParseDict('d', required=True)


class PlatformTests(util.Base):

  def testMatchNone(self):
    """Ensure that an empty filter will match all OS and Arch."""
    for component_platform in [schemas.ComponentPlatform(None, None),
                               schemas.ComponentPlatform([], [])]:
      for p in [platforms.Platform(None, None),
                platforms.Platform(platforms.OperatingSystem.WINDOWS, None),
                platforms.Platform(platforms.OperatingSystem.MACOSX, None),
                platforms.Platform(None, platforms.Architecture.x86),
                platforms.Platform(None, platforms.Architecture.x86_64),
                platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                   platforms.Architecture.x86)]:
        self.assertTrue(component_platform.Matches(p))

  def testMatchOne(self):
    component_platform = schemas.ComponentPlatform(
        [platforms.OperatingSystem.WINDOWS], None)

    for p in [platforms.Platform(platforms.OperatingSystem.WINDOWS, None),
              platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                 platforms.Architecture.x86_64),
              platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                 platforms.Architecture.x86),]:
      self.assertTrue(component_platform.Matches(p))

    for p in [platforms.Platform(None, None),
              platforms.Platform(None, platforms.Architecture.x86),
              platforms.Platform(platforms.OperatingSystem.MACOSX, None),
              platforms.Platform(platforms.OperatingSystem.MACOSX,
                                 platforms.Architecture.x86_64),
              platforms.Platform(platforms.OperatingSystem.LINUX,
                                 platforms.Architecture.x86)]:
      self.assertFalse(component_platform.Matches(p))

    component_platform = schemas.ComponentPlatform(
        None, [platforms.Architecture.x86])

    for p in [platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                 platforms.Architecture.x86),
              platforms.Platform(platforms.OperatingSystem.LINUX,
                                 platforms.Architecture.x86),
              platforms.Platform(None, platforms.Architecture.x86)]:
      self.assertTrue(component_platform.Matches(p))

    for p in [platforms.Platform(None, None),
              platforms.Platform(platforms.OperatingSystem.WINDOWS, None),
              platforms.Platform(None, platforms.Architecture.x86_64),
              platforms.Platform(platforms.OperatingSystem.MACOSX,
                                 platforms.Architecture.x86_64),
              platforms.Platform(platforms.OperatingSystem.LINUX,
                                 platforms.Architecture.x86_64)]:
      self.assertFalse(component_platform.Matches(p))

  def testMatchEither(self):
    component_platform = schemas.ComponentPlatform(
        [platforms.OperatingSystem.WINDOWS, platforms.OperatingSystem.LINUX],
        None)

    for p in [platforms.Platform(platforms.OperatingSystem.WINDOWS, None),
              platforms.Platform(platforms.OperatingSystem.LINUX,
                                 platforms.Architecture.x86_64)]:
      self.assertTrue(component_platform.Matches(p))

    for p in [platforms.Platform(None, None),
              platforms.Platform(platforms.OperatingSystem.MACOSX, None),
              platforms.Platform(platforms.OperatingSystem.MACOSX,
                                 platforms.Architecture.x86_64)]:
      self.assertFalse(component_platform.Matches(p))

  def testMatchUnknown(self):
    """Test we can parse unknown enums and that the matching works."""
    component_platform = schemas.ComponentPlatform.FromDictionary(
        {'operating_systems': ['ASDF', 'LINUX']})
    # Doesn't match unknown, even though the enum itself is unknown.
    self.assertFalse(component_platform.Matches(platforms.Platform(None, None)))
    # Doesn't match a known OS that is wrong.
    self.assertFalse(component_platform.Matches(
        platforms.Platform(platforms.OperatingSystem.WINDOWS, None)))
    # Matches a known OS that is correct.
    self.assertTrue(component_platform.Matches(
        platforms.Platform(platforms.OperatingSystem.LINUX, None)))

    component_platform = schemas.ComponentPlatform.FromDictionary(
        {'architectures': ['ASDF', 'x86_64']})
    # Doesn't match unknown, even though the enum itself is unknown.
    self.assertFalse(component_platform.Matches(platforms.Platform(None, None)))
    # Doesn't match a known arch that is wrong
    self.assertFalse(component_platform.Matches(
        platforms.Platform(None, platforms.Architecture.x86)))
    # Matches a known arch that is correct.
    self.assertTrue(component_platform.Matches(
        platforms.Platform(None, platforms.Architecture.x86_64)))

  def testIntersect(self):
    everything = schemas.ComponentPlatform(None, None)
    everything32 = schemas.ComponentPlatform(None, [platforms.Architecture.x86])
    everything64 = schemas.ComponentPlatform(None,
                                             [platforms.Architecture.x86_64])
    win = schemas.ComponentPlatform([platforms.OperatingSystem.WINDOWS], None)
    win64 = schemas.ComponentPlatform([platforms.OperatingSystem.WINDOWS],
                                      [platforms.Architecture.x86_64])
    linux = schemas.ComponentPlatform([platforms.OperatingSystem.LINUX], None)
    linux64 = schemas.ComponentPlatform([platforms.OperatingSystem.LINUX],
                                        [platforms.Architecture.x86_64])
    linux32 = schemas.ComponentPlatform([platforms.OperatingSystem.LINUX],
                                        [platforms.Architecture.x86])

    self.assertTrue(everything.IntersectsWith(everything))
    self.assertTrue(everything.IntersectsWith(everything32))
    self.assertTrue(everything.IntersectsWith(everything64))
    self.assertFalse(everything32.IntersectsWith(everything64))
    self.assertTrue(everything.IntersectsWith(win))
    self.assertTrue(everything.IntersectsWith(linux64))
    self.assertFalse(win.IntersectsWith(linux))
    self.assertFalse(win64.IntersectsWith(linux64))
    self.assertFalse(win64.IntersectsWith(linux32))
    self.assertTrue(linux.IntersectsWith(linux))
    self.assertTrue(linux32.IntersectsWith(linux32))
    self.assertFalse(linux64.IntersectsWith(linux32))


class NotificationTests(util.Base):

  def testNotificationStrings(self):
    """Ensure that an empty filter will match all OS and Arch."""
    n = schemas.Notification(None, None, None)
    self.assertEqual(n.NotificationMessage(), """

Updates are available for some Cloud SDK components.  To install them,
please run:
  $ gcloud components update

""")

    n = schemas.Notification(None, '0.0.0', None)
    self.assertEqual(n.NotificationMessage(), """

Updates are available for some Cloud SDK components.  To install them,
please run:
  $ gcloud components update --version 0.0.0

""")

    n = schemas.Notification('annotation', '0.0.0', None)
    self.assertEqual(n.NotificationMessage(), """

annotation

Updates are available for some Cloud SDK components.  To install them,
please run:
  $ gcloud components update --version 0.0.0

""")

    n = schemas.Notification('annotation', '0.0.0', 'custom')
    self.assertEqual(n.NotificationMessage(), """

custom

""")

  def testTriggerMatch(self):
    t = schemas.Trigger(0, None)
    self.assertTrue(t.Matches(0, 'gcloud.foo'))

    t = schemas.Trigger(100, None)
    self.assertTrue(t.Matches(0))

    t = schemas.Trigger(10000, None)
    self.assertFalse(t.Matches(time.time(), 'gcloud.foo'))

    t = schemas.Trigger(100, 'gcloud.compute.instances')
    self.assertFalse(t.Matches(0, 'gcloud.foo'))

    t = schemas.Trigger(100, r'gcloud\.compute\..*')
    self.assertTrue(t.Matches(0, 'gcloud.compute.instances*'))
    self.assertFalse(t.Matches(0, None))

  def testConditionMatch(self):
    c = schemas.Condition(start_version='1.0.0', end_version='3.0.0',
                          version_regex=r'2\.[0-2].0', age=1000,
                          check_components=True)
    self.assertTrue(c.Matches(current_version='2.0.0',
                              current_revision=20000101000000,
                              component_updates_available=True))

    # Start version doesn't match.
    self.assertFalse(c.Matches(current_version='0.0.0',
                               current_revision=20000101000000,
                               component_updates_available=True))
    # End version doesn't match.
    self.assertFalse(c.Matches(current_version='4.0.0',
                               current_revision=20000101000000,
                               component_updates_available=True))
    # Regex doesn't match.
    self.assertFalse(c.Matches(current_version='2.3.0',
                               current_revision=20000101000000,
                               component_updates_available=True))
    # Age doesn't match
    self.assertFalse(c.Matches(
        current_version='2.0.0',
        current_revision=config.InstallationConfig.FormatRevision(
            time.localtime()),
        component_updates_available=True))
    # Test failing to parse the revision.
    self.assertFalse(c.Matches(current_version='2.0.0',
                               current_revision=0,
                               component_updates_available=False))
    # Check components doesn't match.
    self.assertFalse(c.Matches(current_version='2.0.0',
                               current_revision=20000101000000,
                               component_updates_available=False))

    c = schemas.Condition(start_version='1.0.0', end_version='3.0.0',
                          version_regex=r'2\.[0-2].0', age=0,
                          check_components=True)
    self.assertTrue(c.Matches(
        current_version='2.0.0',
        current_revision=config.InstallationConfig.FormatRevision(
            time.localtime()),
        component_updates_available=True))
    # Current version is None, no match.
    self.assertFalse(c.Matches(
        current_version=None,
        current_revision=config.InstallationConfig.FormatRevision(
            time.localtime()),
        component_updates_available=True))
    # Current version can't be parsed, no match.
    self.assertFalse(c.Matches(
        current_version='1.2',
        current_revision=config.InstallationConfig.FormatRevision(
            time.localtime()),
        component_updates_available=True))
    # Revision is None, no match.
    self.assertFalse(c.Matches(
        current_version='2.0.0',
        current_revision=None,
        component_updates_available=True))
    # Revision can't be parsed, no match.
    self.assertFalse(c.Matches(
        current_version='2.0.0',
        current_revision=123,
        component_updates_available=True))

    c = schemas.Condition(start_version=None, end_version=None,
                          version_regex=None, age=None, check_components=True)
    self.assertTrue(c.Matches(current_version=None, current_revision=0,
                              component_updates_available=True))


if __name__ == '__main__':
  test_case.main()
