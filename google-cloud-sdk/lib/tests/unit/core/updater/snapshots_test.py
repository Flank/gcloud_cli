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

from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.util import platforms
from tests.lib import test_case
from tests.lib.core.updater import util


class SnapshotsTests(util.Base):

  def CreateSnapshotsFromStrings(self, str1, str2):
    snapshot1 = self.CreateSnapshotFromStrings(
        1, str1[0], str1[1])
    snapshot2 = self.CreateSnapshotFromStrings(
        2, str2[0], str2[1])
    return (snapshot1, snapshot2)

  def CreateSnapshotDiffFromStrings(self, str1, str2, platform_filter=None):
    (snapshot1, snapshot2) = self.CreateSnapshotsFromStrings(str1, str2)
    return snapshot1.CreateDiff(snapshot2, platform_filter=platform_filter)

  def ValidateActions(self, snapshot_diff, seed, to_remove, to_install):
    self.assertEqual(set(to_remove), snapshot_diff.ToRemove(seed))
    self.assertEqual(set(to_install), snapshot_diff.ToInstall(seed))

  def testURLs(self):
    snapshot = self.CreateSnapshotFromStrings(1, 'a', '')
    url = self.URLFromFile(self.CreateTempSnapshotFileFromSnapshot(snapshot))
    with self.assertRaisesRegexp(snapshots.URLFetchError,
                                 '(additional component repository)'):
      snapshot.FromURLs(url, 'file://junk')
    junk = self.URLFromFile(self.Touch(self.temp_path, contents='asdfasdf'))
    with self.assertRaises(snapshots.MalformedSnapshotError):
      snapshots.ComponentSnapshot.FromURLs(junk)

  def testUnknownDependency(self):
    a = self.CreateFakeComponent('a', ['b'])
    snapshot = snapshots.ComponentSnapshot(
        schemas.SDKDefinition(
            revision=1, schema_version=None, release_notes_url=None,
            version=None, gcloud_rel_path=None, post_processing_command=None,
            components=[a], notifications={}))
    # Invalid dependency should be removed
    self.assertEquals(set(['a']),
                      snapshot.DependencyClosureForComponents(['a']))

  def testGetDependencies(self):
    snapshot = self.CreateSnapshotFromStrings(
        1,
        'a,b,c,d,e,f,g,h,i,j,k',
        'a->b,c|b->d,e|c->f,g|d->h|f->h|i->j|j->k|k->i')

    all_set = set(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
    all_second_set = set(['i', 'j', 'k'])

    self.assertEqual(all_set, snapshot.DependencyClosureForComponents(['a']))
    self.assertEqual(set(['b', 'd', 'e', 'h']),
                     snapshot.DependencyClosureForComponents(['b']))
    self.assertEqual(set(['c', 'f', 'g', 'h']),
                     snapshot.DependencyClosureForComponents(['c']))
    self.assertEqual(set(['g']), snapshot.DependencyClosureForComponents(['g']))

    # Everything is totally connected in this example
    for component in all_set:
      self.assertEqual(all_set, snapshot.ConnectedComponents([component]))

    for component in all_second_set:
      self.assertEqual(all_second_set,
                       snapshot.DependencyClosureForComponents([component]))

    self.assertEqual(all_second_set, snapshot.ConnectedComponents(['i']))
    self.assertEqual(all_second_set, snapshot.ConnectedComponents(['j']))
    self.assertEqual(all_second_set, snapshot.ConnectedComponents(['k']))

    everything = set(all_set)
    everything.update(all_second_set)
    self.assertEqual(everything, snapshot.ConnectedComponents(['a', 'i']))

  def testGetDependenciesWithPlatformFilter(self):
    snapshot = self.CreateSnapshotFromStrings(
        1,
        'a,b,c,d,e,f,g,h',
        'a->b,c|b->d,e|c->f,g|d->h|f->h')
    self.ChangePlatformForComponents(
        snapshot, ['b'],
        platforms.Platform(platforms.OperatingSystem.WINDOWS, None))

    all_set = set(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
    filtered_set = set(['a', 'c', 'f', 'g', 'h'])

    self.assertEqual(all_set, snapshot.DependencyClosureForComponents(
        ['a'],
        platform_filter=platforms.Platform(platforms.OperatingSystem.WINDOWS,
                                           platforms.Architecture.x86_64)))
    self.assertEqual(filtered_set, snapshot.DependencyClosureForComponents(
        ['a'],
        platform_filter=platforms.Platform(platforms.OperatingSystem.LINUX,
                                           platforms.Architecture.x86_64)))

    self.assertEqual(set(), snapshot.ConnectedComponents(
        ['b'],
        platform_filter=platforms.Platform(platforms.OperatingSystem.LINUX,
                                           platforms.Architecture.x86_64)))
    self.assertEqual(
        set(['h', 'd', 'f', 'c', 'a']), snapshot.ConsumerClosureForComponents(
            ['h'],
            platform_filter=platforms.Platform(platforms.OperatingSystem.LINUX,
                                               platforms.Architecture.x86_64)))

  def testCircularSnapshot(self):
    snapshot = self.CreateSnapshotFromStrings(
        1, 'a,b,c,d', 'a->b,c,d|b->a,c,d|c->a,b,d|d->a,b,c')
    self.assertEqual(set(['a', 'b', 'c', 'd']),
                     snapshot.DependencyClosureForComponents(['a']))
    self.assertEqual(set(['a', 'b', 'c', 'd']),
                     snapshot.ConnectedComponents(['c']))

  def testBasicSnapshotDiff(self):
    # all components are connected, b gets updated
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b2,c1', 'a->b|b->c'))
    # we always need to update b
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b'], to_install=['b'])
    self.ValidateActions(snapshot_diff, seed=['c'],
                         to_remove=['b'], to_install=['b'])

  def testSnapshotDiffNoChange(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b1,c1', 'a->b|b->c'))
    # need to update b and get c
    self.ValidateActions(snapshot_diff, seed=['a'], to_remove=[], to_install=[])

  def testSnapshotDiffUpdateAndAdd(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('b1', ''), ('a1,b2', 'a->b'))
    self.ValidateActions(snapshot_diff, seed=['a'], to_remove=['b'],
                         to_install=['a', 'b'])

  def testSnapshotDiffNoConnectedChange(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1,d1', 'a->b|b->c'), ('a1,b1,c1,d2', 'a->b|b->c'))
    # need to update b and get c
    self.ValidateActions(snapshot_diff, seed=['a'], to_remove=[], to_install=[])

  def testSnapshotDiffWithNewDependency(self):
    # c is not needed right now, b gets updated, now requires c
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1', 'a->b'), ('a1,b2,c2', 'a->b|b->c'))
    # need to update b and c
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b', 'c'], to_install=['b', 'c'])

  def testSnapshotDiffNewComponent(self):
    # c gets added
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1', 'a->b'), ('a1,b2,c1', 'a->b|b->c'))
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b'], to_install=['b', 'c'])

  def testSnapshotDiffRemovedComponent(self):
    # c gets removed
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b2', 'a->b'))
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b', 'c'], to_install=['b'])

  def testSnapshotDiffDisjoint(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1,d1', 'a->b|c->d'), ('a1,b2,c2,d1', 'a->b|c->d'))
    # should only update things connected to a
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b'], to_install=['b'])
    self.ValidateActions(snapshot_diff, seed=['d'],
                         to_remove=['c'], to_install=['c'])
    self.ValidateActions(snapshot_diff, seed=['b', 'c'],
                         to_remove=['b', 'c'], to_install=['b', 'c'])

  def testSnapshotDiffDisjointMerged(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1,d1', 'a->b|c->d'), ('a1,b2,c2,d1', 'a->b|b->c|c->d'))
    # should update everything because c,d end up being connected to a
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=['b', 'c'], to_install=['b', 'c'])

  def testSnapshotDiffNewInstall(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('', ''), ('a1', ''))
    # should update everything because c,d end up being connected to a
    self.ValidateActions(snapshot_diff, seed=['a'],
                         to_remove=[], to_install=['a'])

  def testSnapshotDiffNewInstallAndDiff(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1', 'a->b'), ('a1,b2,c1,d1', 'a->b|c->d'))
    # should update everything because c,d end up being connected to a
    self.ValidateActions(snapshot_diff, seed=['a', 'd'],
                         to_remove=['b'], to_install=['b', 'd'])
    self.ValidateActions(snapshot_diff, seed=['a', 'c'],
                         to_remove=['b'], to_install=['b', 'c', 'd'])

  def testNewInstallWithUpdatesNonLinear(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1', 'b->a'),
        ('a2,b2,c1', 'b->a|c->a'))
    self.ValidateActions(snapshot_diff, seed=['c'], to_remove=['a', 'b'],
                         to_install=['a', 'b', 'c'])

  def testSnapshotDiffBasicInstallWithPlatform(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('', ''), ('a1,b1,c1', 'a->b|b->c'))
    self.ChangePlatformForComponents(s2, ['c'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=[], to_install=['a', 'b'])
    self.ValidateActions(diff, seed=['c'], to_remove=[], to_install=[])

    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('', ''), ('a1,b1,c1', 'a->b|b->c'))
    self.ChangePlatformForComponents(s2, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=[], to_install=['a'])
    self.ValidateActions(diff, seed=['b'], to_remove=[], to_install=[])
    self.ValidateActions(diff, seed=['c'], to_remove=[], to_install=['c'])

  def testSnapshotDiffUpdateWithPlatformChange(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b2,c1', 'a->b|b->c'))
    self.ChangePlatformForComponents(s2, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['b'], to_install=[])

  def testSnapshotDiffDoubleUpdateWithPlatformChange(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b2,c2', 'a->b|b->c'))
    self.ChangePlatformForComponents(s2, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['b', 'c'],
                         to_install=['c'])

  def testSnapshotDiffUpdateWithPlatformChangeReverse(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,b2,c1', 'a->b|b->c'))
    self.ChangePlatformForComponents(s1, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['b'], to_install=['b'])

  def testSnapshotDiffRemoveWithPlatformChangeReverse(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a1,c1', ''))
    self.ChangePlatformForComponents(s1, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=[], to_install=[])

  def testSnapshotDiffUpdateAndRemoveWithPlatformChangeReverse(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a2,c1', ''))
    self.ChangePlatformForComponents(s1, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['a'], to_install=['a'])

  def testSnapshotDiffOtherPlatform(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1', 'a->b|b->c'), ('a2,b2,c1', 'a->b|b->c'))
    self.ChangePlatformForComponents(s1, ['b'])
    self.ChangePlatformForComponents(s2, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['a'], to_install=['a'])

  def testSnapshotDiffTreeWithOtherPlatform(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1,c1,d1', 'a->b|a->c|b->d|c->d'),
        ('a2,b2,c1,d2', 'a->b|a->c|b->d|c->d'))
    self.ChangePlatformForComponents(s1, ['b'])
    self.ChangePlatformForComponents(s2, ['b'])
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a'], to_remove=['a', 'd'],
                         to_install=['a', 'd'])

  def testSnapshotDiffRemovedPlatformSpecific(self):
    (s1, s2) = self.CreateSnapshotsFromStrings(
        ('a1,b1', 'a->b|b->a'), ('', ''))
    self.ChangePlatformForComponents(s1, ['b'], platform=self.CURRENT_PLATFORM)
    diff = s1.CreateDiff(s2, self.CURRENT_PLATFORM)
    self.ValidateActions(diff, seed=['a', 'b'],
                         to_remove=['a', 'b'], to_install=[])

  def _IDs(self, dictionary):
    return [d.id for d in dictionary]

  def testSnapshotDiffAvailableUpdates(self):
    snapshot_diff = self.CreateSnapshotDiffFromStrings(
        ('a1,b1,c1,d1', 'a->b|b->c|c->d'), ('a1,b2,d2,e1', 'a->b|d->e'))
    self.assertEqual(['b', 'd'], self._IDs(snapshot_diff.AvailableUpdates()))
    self.assertEqual(['e'], self._IDs(snapshot_diff.AvailableToInstall()))
    self.assertEqual(['c'], self._IDs(snapshot_diff.Removed()))
    self.assertEqual(['a'], self._IDs(snapshot_diff.UpToDate()))
    self.assertEqual(['a', 'b', 'c', 'd', 'e'],
                     self._IDs(snapshot_diff.AllDiffs()))

  def testSnapshotDiffAvailableUpdatesLaterVersion(self):
    # Normal case.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a1', ''), ('a2', ''))
    self.assertEqual(['a'], self._IDs(snapshot_diff.AvailableUpdates()))

    # We have a later version, no data in components, don't report update.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a2', ''), ('a1', ''))
    self.assertEqual([], self._IDs(snapshot_diff.AvailableUpdates()))

    # One has data, its an update.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a2', ''), ('a1', ''))
    snapshot_diff.current.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, None)
    snapshot_diff = snapshot_diff.current.CreateDiff(snapshot_diff.latest)
    self.assertEqual(['a'], self._IDs(snapshot_diff.AvailableUpdates()))

    # The other has data, its an update.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a2', ''), ('a1', ''))
    snapshot_diff.current.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, None)
    snapshot_diff = snapshot_diff.current.CreateDiff(snapshot_diff.latest)
    self.assertEqual(['a'], self._IDs(snapshot_diff.AvailableUpdates()))

    # Both have data, contents match, not an update.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a2', ''), ('a1', ''))
    snapshot_diff.current.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, contents_checksum='asdf')
    snapshot_diff.latest.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, contents_checksum='asdf')
    snapshot_diff = snapshot_diff.current.CreateDiff(snapshot_diff.latest)
    self.assertEqual([], self._IDs(snapshot_diff.AvailableUpdates()))

    # Both have data, contents mismatch, it's an update.
    snapshot_diff = self.CreateSnapshotDiffFromStrings(('a2', ''), ('a1', ''))
    snapshot_diff.current.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, contents_checksum='asdf')
    snapshot_diff.latest.ComponentFromId('a').data = schemas.ComponentData(
        None, None, None, None, contents_checksum='qwer')
    snapshot_diff = snapshot_diff.current.CreateDiff(snapshot_diff.latest)
    self.assertEqual(['a'], self._IDs(snapshot_diff.AvailableUpdates()))

  def testGetEffectiveSize(self):
    snapshot = self.CreateSnapshotFromStrings(1, 'a1,b1,c1,d1,e1,f1',
                                              'a->b|b->c|a->d|d->e|a->f')
    snapshot.components['b'].is_hidden = True
    snapshot.components['b'].data = schemas.ComponentData.FromDictionary(
        {'type': 'tar', 'source': 'foo', 'size': 1})
    snapshot.components['c'].is_hidden = True
    snapshot.components['c'].data = schemas.ComponentData.FromDictionary(
        {'type': 'tar', 'source': 'foo', 'size': 2})
    snapshot.components['d'].is_hidden = False
    snapshot.components['d'].data = schemas.ComponentData.FromDictionary(
        {'type': 'tar', 'source': 'foo', 'size': 4})
    snapshot.components['e'].is_hidden = True
    snapshot.components['e'].data = schemas.ComponentData.FromDictionary(
        {'type': 'tar', 'source': 'foo', 'size': 8})
    snapshot.components['f'].is_hidden = True
    snapshot.components['f'].data = schemas.ComponentData.FromDictionary(
        {'type': 'tar', 'source': 'foo', 'size': 16})
    self.ChangePlatformForComponents(
        snapshot, ['f'],
        platforms.Platform(platforms.OperatingSystem.WINDOWS, None))

    # We only include the size of b in the size of a.
    self.assertEquals(
        1, snapshot.GetEffectiveComponentSize('a', platform_filter=None))
    # c is a regular component with data just return its size.
    self.assertEquals(
        2, snapshot.GetEffectiveComponentSize('c', platform_filter=None))
    # asdf does not exist.  It has no size.
    self.assertEquals(
        0, snapshot.GetEffectiveComponentSize('asdf', platform_filter=None))
    # f does not match this platform.  It has no size.
    self.assertEquals(
        0, snapshot.GetEffectiveComponentSize('f', platform_filter=None))


if __name__ == '__main__':
  test_case.main()
