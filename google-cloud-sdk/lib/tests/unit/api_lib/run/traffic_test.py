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
"""Unit tests for the Run flags module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case


MESSAGES = core_apis.GetMessagesModule('run', 'v1alpha1')


def NewTrafficTargets(percentages):
  targets = []
  for revision_name in percentages:
    targets.append(
        traffic.NewTrafficTarget(
            MESSAGES, revision_name, percentages[revision_name]))

  sorted(targets, key=traffic.SortKeyFromTarget)
  return traffic.TrafficTargets(MESSAGES, targets)


class TrafficTest(test_case.TestCase):

  def GetTargetsKeys(self, targets):
    """Returns the keys for targets sorted by revisionName with latest last."""
    return sorted([k for k in targets], key=traffic.SortKeyFromKey)

  def test_access_empty_traffic_targets(self):
    targets = NewTrafficTargets([])
    with self.assertRaises(KeyError):
      unused = targets['r1']
      del unused
    with self.assertRaises(KeyError):
      unused = targets[traffic.LATEST_REVISION_KEY]
      del unused
    self.assertNotIn('r1', targets)
    self.assertNotIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertFalse(targets)
    self.assertEqual([k for k in targets], [])
    self.assertEqual(targets.MakeSerializable(), [])
    self.assertEqual(str(targets), '[]')

  def test_access_not_empty_traffic_targets(self):
    targets = NewTrafficTargets({'r0': 10, 'r1': 20, 'LATEST': 70})
    r0 = traffic.NewTrafficTarget(
        MESSAGES, 'r0', 10)
    r1 = traffic.NewTrafficTarget(
        MESSAGES, 'r1', 20)
    latest = traffic.NewTrafficTarget(
        MESSAGES, traffic.LATEST_REVISION_KEY, 70)

    self.assertEqual(targets['r0'], r0)
    self.assertEqual(targets['r1'], r1)
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], latest)
    self.assertIn('r1', targets)
    self.assertIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 3)
    self.assertIn(r0, targets.MakeSerializable())
    self.assertIn(r1, targets.MakeSerializable())
    self.assertIn(latest, targets.MakeSerializable())
    self.assertIn('r0:', str(targets))
    self.assertIn('r1:', str(targets))
    self.assertIn('LATEST:', str(targets))

  def test_modify_traffic_targets(self):
    targets = NewTrafficTargets({'r0': 10, 'LATEST': 70})
    r0 = traffic.NewTrafficTarget(
        MESSAGES, 'r0', 10)
    r1 = traffic.NewTrafficTarget(
        MESSAGES, 'r1', 20)
    r1b = traffic.NewTrafficTarget(
        MESSAGES, 'r1', 30)
    latest = traffic.NewTrafficTarget(
        MESSAGES, traffic.LATEST_REVISION_KEY, 70)

    self.assertEqual(len(targets), 2)
    self.assertEqual(targets['r0'], r0)
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], latest)
    self.assertNotIn('r1', targets)
    targets['r1'] = r1
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], r1)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])

    targets['r1'] = r1b
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], r1b)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])

    del targets['r1']
    self.assertNotIn('r1', targets)
    self.assertEqual(len(targets), 2)
    self.assertEqual(
        self.GetTargetsKeys(targets), [u'r0', traffic.LATEST_REVISION_KEY])

    del targets[traffic.LATEST_REVISION_KEY]
    self.assertNotIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 1)
    self.assertEqual(self.GetTargetsKeys(targets), [u'r0'])

    targets[traffic.LATEST_REVISION_KEY] = latest
    self.assertIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 2)
    self.assertEqual(
        self.GetTargetsKeys(targets), [u'r0', traffic.LATEST_REVISION_KEY])

  def test_validate_current_traffic_99_fails(self):
    targets = NewTrafficTargets({'r0': 10, 'r1': 20, 'LATEST': 69})
    with self.assertRaises(ValueError):
      targets.UpdateTraffic({'LATEST': 100})

  def test_validate_current_traffic_negative_target_fails(self):
    targets = NewTrafficTargets({'r0': -1, 'r1': 101})
    with self.assertRaises(ValueError):
      targets.UpdateTraffic({'LATEST': 100})
    targets = NewTrafficTargets({'r0': 100, 'LATEST': -1})
    with self.assertRaises(ValueError):
      targets.UpdateTraffic({'LATEST': 100})

  def test_validate_new_percentages_101_fails(self):
    targets = NewTrafficTargets({'r0': 10, 'r1': 20, 'LATEST': 70})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'LATEST': 101})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r1': 101})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r1': 10, 'r2': 91})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r1': 2, 'LATEST': 99})

  def test_validate_new_percentages_101_negative_target_fails(self):
    targets = NewTrafficTargets({'r0': 10, 'r1': 20, 'LATEST': 70})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r1': 10, 'r2': 91, 'r3': -1})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r1': 10, 'r2': 91, 'LATEST': -1})

  def test_validate_new_percentages_99_no_unspecified_fails(self):
    targets = NewTrafficTargets({'r0': 10, 'r1': 20, 'LATEST': 70})
    with self.assertRaises(traffic.InvalidTrafficSpecificationError):
      targets.UpdateTraffic({'r0': 10, 'r1': 20, 'LATEST': 69})

  def test_round_none(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 25.0, 'r1': 75.0}),
        {'r0': 25, 'r1': 75})

  def test_round_extra_biggest_loss(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 24.9, 'r1': 75.0}),
        {'r0': 25, 'r1': 75})

  def test_round_extra_2biggest_loss(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 20.2, 'r1': 38.9, 'r2': 40.9}),
        {'r0': 20, 'r1': 39, 'r2': 41})

  def test_round_extra_2smallest_percent(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 40.66, 'r1': 30.66, 'r2': 28.66}),
        {'r0': 40, 'r1': 31, 'r2': 29})

  def test_round_extra_smallest_key(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 33.33, 'r1': 33.33, 'r2': 33.33}),
        {'r0': 34, 'r1': 33, 'r2': 33})

  def test_round_assign_40_percent(self):
    targets = NewTrafficTargets({'LATEST': 100})
    self.assertEqual(
        targets._IntPercentages({'r0': 30.1, 'r1': 9.9}),
        {'r0': 30, 'r1': 10})

  def test_all_active_revisions_changed(self):
    targets = NewTrafficTargets({'r0': 60, 'r1': 40})
    targets.UpdateTraffic({'r0': 40, 'r1': 60})
    self.assertEqual(
        targets, NewTrafficTargets({'r0': 40, 'r1': 60}))

  def test_active_one_active_revision_unchanged_no_drain(self):
    targets = NewTrafficTargets(
        {'r0': 25, 'r1': 25, 'r2': 50})
    targets.UpdateTraffic({'r0': 20, 'r1': 30, 'r2': 50})
    self.assertEqual(
        targets, NewTrafficTargets({'r0': 20, 'r1': 30, 'r2': 50}))

  def test_active_one_active_revision_unchanged_drain(self):
    targets = NewTrafficTargets(
        {'r0': 25, 'r1': 25, 'r2': 50})
    targets.UpdateTraffic({'r0': 35, 'r1': 30})
    self.assertEqual(
        targets, NewTrafficTargets({'r0': 35, 'r1': 30, 'r2': 35}))

  def test_active_one_active_revision_unassigned_one_unchanged_drain(self):
    targets = NewTrafficTargets(
        {'r0': 25, 'r1': 25, 'r2': 50})
    targets.UpdateTraffic({'r0': 25, 'r1': 30})
    self.assertEqual(
        targets, NewTrafficTargets({'r0': 25, 'r1': 30, 'r2': 45}))

  def test_active_one_active_revision_unchanged_undrain(self):
    targets = NewTrafficTargets(
        {'r0': 25, 'r1': 25, 'r2': 50})
    targets.UpdateTraffic({'r0': 20, 'r1': 15})
    self.assertEqual(
        targets,
        NewTrafficTargets({'r0': 20, 'r1': 15, 'r2': 65}))

  def test_active_three_active_revisions_unchanged_no_drain(self):
    targets = NewTrafficTargets(
        {'r0': 5, 'r1': 10, 'r2': 15, 'r3': 30, 'r4': 40})
    targets.UpdateTraffic({'r0': 8, 'r1': 7})
    self.assertEqual(
        targets,
        NewTrafficTargets(
            {'r0': 8, 'r1': 7, 'r2': 15, 'r3': 30, 'r4': 40}))

  def test_active_three_active_revisions_unchanged_drain(self):
    targets = NewTrafficTargets(
        {'r0': 3, 'r1': 7, 'r2': 15, 'r3': 30, 'r4': 45})
    targets.UpdateTraffic({'r0': 3 + 6, 'r1': 7})
    self.assertEqual(
        targets,
        NewTrafficTargets(
            {'r0': 3 + 6,
             'r1': 7,
             'r2': 15 - 1,
             'r3': 30 - 2,
             'r4': 45 - 3}))

  def test_active_three_active_revisions_unchanged_undrain(self):
    targets = NewTrafficTargets(
        {'r0': 3, 'r1': 7, 'r2': 15, 'r3': 30, 'r4': 45})
    targets.UpdateTraffic({'r0': 3, 'r1': 7 - 6})
    self.assertEqual(
        targets,
        NewTrafficTargets(
            {'r0': 3,
             'r1': 7 - 6,
             'r2': 15 + 1,
             'r3': 30 + 2,
             'r4': 45 + 3}))

  def test_three_active_revisions_unchanged_drain_round(self):
    targets = NewTrafficTargets(
        {'r0': 3, 'r1': 7, 'r2': 15, 'r3': 30, 'r4': 45})
    targets.UpdateTraffic({'r0': 3 + 5, 'r1': 7})
    self.assertEqual(
        targets,
        NewTrafficTargets(
            {'r0': 3 + 5,
             'r1': 7,
             'r2': 15 - 1,
             'r3': 30 - 2,
             'r4': 45 - 2}))

  def test_three_active_revisions_unchanged_undrain_round(self):
    targets = NewTrafficTargets(
        {'r0': 3, 'r1': 7, 'r2': 15, 'r3': 30, 'r4': 45})
    targets.UpdateTraffic({'r0': 3, 'r1': 7 - 5})
    self.assertEqual(
        targets,
        NewTrafficTargets(
            {'r0': 3,
             'r1': 7 - 5,
             'r2': 15 + 1,
             'r3': 30 + 2,
             'r4': 45 + 2}))

  def test_latest_drain(self):
    targets = NewTrafficTargets({'r0': 20, 'LATEST': 80})
    targets.UpdateTraffic({'r0': 30})
    self.assertEqual(targets, NewTrafficTargets({'r0': 30, 'LATEST': 70}))

  def test_latest_undrain(self):
    targets = NewTrafficTargets({'r0': 20, 'LATEST': 80})
    targets.UpdateTraffic({'r0': 10})
    self.assertEqual(targets, NewTrafficTargets({'r0': 10, 'LATEST': 90}))

  def test_add_revision(self):
    targets = NewTrafficTargets({'r0': 20, 'LATEST': 80})
    targets.UpdateTraffic({'r1': 30})
    self.assertEqual(targets, NewTrafficTargets(
        {'r0': 14, 'r1': 30, 'LATEST': 56}))

  def test_add_latest(self):
    targets = NewTrafficTargets({'r0': 100})
    targets.UpdateTraffic({'LATEST': 20})
    self.assertEqual(targets, NewTrafficTargets({'r0': 80, 'LATEST': 20}))

  def test_zero_revision(self):
    targets = NewTrafficTargets({'r0': 20, 'LATEST': 80})
    targets.UpdateTraffic({'r0': 0})
    self.assertEqual(targets, NewTrafficTargets({'LATEST': 100}))

  def test_zero_one_keep_onerevision(self):
    targets = NewTrafficTargets({'r0': 1, 'r1': 1, 'LATEST': 98})
    targets.UpdateTraffic({'LATEST': 99})
    self.assertEqual(targets, NewTrafficTargets(
        {'r0': 1, 'r1': 0, 'LATEST': 99}))

  def test_zero_latest(self):
    targets = NewTrafficTargets({'r0': 20, 'LATEST': 80})
    targets.UpdateTraffic({'r0': 100})
    self.assertEqual(targets, NewTrafficTargets({'r0': 100}))


def NewTrafficTargetPair(
    latest_revision_name,
    spec_percent=None,
    spec_latest=None,
    spec_revision_name=None,
    status_percent=None,
    status_latest=None,
    status_revision_name=None,
    status_percent_override=None):

  if (spec_percent is not None
      or spec_latest is not None
      or spec_revision_name is not None):
    spec_target = MESSAGES.TrafficTarget(
        latestRevision=spec_latest,
        revisionName=spec_revision_name,
        percent=spec_percent)
  else:
    spec_target = None

  if (status_percent is not None
      and (status_latest is not None
           or status_revision_name is not None)):
    status_target = MESSAGES.TrafficTarget(
        latestRevision=status_latest,
        revisionName=status_revision_name,
        percent=status_percent)
  else:
    status_target = None

  return traffic.TrafficTargetPair(
      spec_target, status_target, latest_revision_name, status_percent_override)


class TrafficTargetPairTest(test_case.TestCase):

  def testSpecOnlyLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, None)
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testSpecOnlyRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '100% (currently -)')

  def testStatusOnlyLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', status_percent=100, status_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, None)
    self.assertFalse(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testStatusOnlyRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', status_percent=100, status_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertFalse(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '-    (currently 100%)')

  def testBothLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_latest=True,
        status_percent=100, status_revision_name='s1-r1', status_latest=True)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '100%')

  def testBothRevisionName(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=100, spec_revision_name='s1-r2',
        status_percent=100, status_revision_name='s1-r2')
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')
    self.assertEqual(target_pair.displayPercent, '100%')

  def testBothStatusLatest(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=40, spec_latest=True,
        status_percent=60, status_revision_name='s1-r1')
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '40')
    self.assertEqual(target_pair.statusPercent, '60')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '40%  (currently 60%)')

  def testBothStatusLatestWithStatusPercentOverride(self):
    target_pair = NewTrafficTargetPair(
        's1-r1', spec_percent=40, spec_latest=True,
        status_percent=60, status_revision_name='s1-r1',
        status_percent_override=40)
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '40')
    self.assertEqual(target_pair.statusPercent, '40')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')
    self.assertEqual(target_pair.displayPercent, '40%')


def GetTrafficTargetPairs(
    spec_traffic, status_traffic, is_platform_managed,
    latest_ready_revision_name):
  return traffic.GetTrafficTargetPairs(
      list(spec_traffic.values()),
      list(status_traffic.values()),
      is_platform_managed,
      latest_ready_revision_name)


class GetTrafficPairsTest(test_case.TestCase):

  def testSpecOnlyNoLatest(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 10, 's1-r2': 90}),
        status_traffic=NewTrafficTargets({}),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  def testBothNoLatestMatch(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 10, 's1-r2': 90}),
        status_traffic=NewTrafficTargets({'s1-r1': 10, 's1-r2': 90}),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  def testBothNoLatestNoMatch(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 100}),
        status_traffic=NewTrafficTargets({'s1-r2': 100}),
        is_platform_managed=False,
        latest_ready_revision_name=None)
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, 's1-r2')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r2')
    self.assertFalse(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '-')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r2')

  def testSpecOnlyExplicitLatest(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 90, 'LATEST': 10}),
        status_traffic=NewTrafficTargets({}),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, None)
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  def testBothExplicitLatest(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 90, 'LATEST': 10}),
        status_traffic=NewTrafficTargets({'s1-r1': 90, 'LATEST': 10}),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, None)
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  def testBothImplicitLatestMissingStatusGke(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 90, 'LATEST': 10}),
        status_traffic=NewTrafficTargets({'s1-r1': 100}),
        is_platform_managed=False,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, None)
    self.assertTrue(target_pair.specTarget)
    self.assertFalse(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '-')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  def testBothImplicitManaged(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 90, 'LATEST': 10}),
        status_traffic=NewTrafficTargets({'s1-r1': 100}),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 2)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '90')
    self.assertEqual(target_pair.statusPercent, '90')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
    target_pair = traffic_pairs[1]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '10')
    self.assertEqual(target_pair.statusPercent, '10')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  def testLatestImplicitManaged(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'LATEST': 100}),
        status_traffic=NewTrafficTargets({'s1-r1': 100}),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 1)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, traffic.LATEST_REVISION_KEY)
    self.assertTrue(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId,
                     'LATEST (currently s1-r1)')

  def testLatestByNameOnlyManaged(self):
    traffic_pairs = GetTrafficTargetPairs(
        spec_traffic=NewTrafficTargets({'s1-r1': 100}),
        status_traffic=NewTrafficTargets({'s1-r1': 100}),
        is_platform_managed=True,
        latest_ready_revision_name='s1-r1')
    self.assertEqual(len(traffic_pairs), 1)
    target_pair = traffic_pairs[0]
    self.assertEqual(target_pair.key, 's1-r1')
    self.assertFalse(target_pair.latestRevision)
    self.assertEqual(target_pair.revisionName, 's1-r1')
    self.assertTrue(target_pair.specTarget)
    self.assertTrue(target_pair.statusTarget)
    self.assertEqual(target_pair.specPercent, '100')
    self.assertEqual(target_pair.statusPercent, '100')
    self.assertEqual(target_pair.displayRevisionId, 's1-r1')
