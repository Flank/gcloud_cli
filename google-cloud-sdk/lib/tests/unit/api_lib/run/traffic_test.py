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


MESSAGES = core_apis.GetMessagesModule('run', 'v1')


def NewTrafficTargets(percentages):
  targets = [
      TrafficTarget(name, percentage)
      for name, percentage in percentages.items()
  ]
  return TrafficTargets(targets)


def TrafficTarget(key, percent=None, tag=None):
  return traffic.NewTrafficTarget(MESSAGES, key, percent, tag)


def TrafficTargets(targets_to_wrap):
  return traffic.TrafficTargets(MESSAGES, targets_to_wrap)


class TrafficTest(test_case.TestCase):

  def GetTargetsKeys(self, targets):
    """Returns the keys for targets sorted by revisionName with latest last."""
    return sorted([k for k in targets], key=traffic.SortKeyFromKey)

  def test_access_empty_traffic_targets(self):
    targets = NewTrafficTargets({})
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

    self.assertEqual(targets['r0'], [r0])
    self.assertEqual(targets['r1'], [r1])
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], [latest])
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

  def test_delete_missing(self):
    targets = NewTrafficTargets({'r0': 30, 'LATEST': 70})
    with self.assertRaises(KeyError):
      del targets['r1']

  def test_access_not_empty_multiple_targets_per_revision(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 10), TrafficTarget('r1', 20),
        TrafficTarget('r0', 25), TrafficTarget('r0', 30),
        TrafficTarget('LATEST', 15)])

    r0 = [
        TrafficTarget('r0', 10),
        TrafficTarget('r0', 25),
        TrafficTarget('r0', 30)
    ]
    r1 = [TrafficTarget('r1', 20)]
    latest = [TrafficTarget(traffic.LATEST_REVISION_KEY, 15)]

    self.assertEqual(targets['r0'], r0)
    self.assertEqual(targets['r1'], r1)
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], latest)
    self.assertIn('r1', targets)
    self.assertIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 5)
    self.assertIn(r0[0], targets.MakeSerializable())
    self.assertIn(r0[1], targets.MakeSerializable())
    self.assertIn(r0[2], targets.MakeSerializable())
    self.assertIn(r1[0], targets.MakeSerializable())
    self.assertIn(latest[0], targets.MakeSerializable())
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
    self.assertEqual(targets['r0'], [r0])
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], [latest])
    self.assertNotIn('r1', targets)
    targets['r1'] = [r1]
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], [r1])
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])

    targets['r1'] = [r1b]
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], [r1b])
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

    targets[traffic.LATEST_REVISION_KEY] = [latest]
    self.assertIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 2)
    self.assertEqual(
        self.GetTargetsKeys(targets), [u'r0', traffic.LATEST_REVISION_KEY])

  def test_modify_traffic_targets_multiple_targets_per_revision(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 10),
        TrafficTarget('r0', 25),
        TrafficTarget('LATEST', 15)])

    r0 = [TrafficTarget('r0', 10), TrafficTarget('r0', 25)]
    r1 = [TrafficTarget('r1', 20), TrafficTarget('r1', 30)]
    r1b = [TrafficTarget('r1', 25)]
    latest = [TrafficTarget(traffic.LATEST_REVISION_KEY, 15)]

    self.assertEqual(len(targets), 2)
    self.assertEqual(targets['r0'], r0)
    self.assertEqual(targets[traffic.LATEST_REVISION_KEY], latest)
    self.assertNotIn('r1', targets)
    self.assertEqual(len(targets.MakeSerializable()), 3)
    targets['r1'] = r1
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], r1)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 5)

    targets['r1'] = r1b
    self.assertIn('r1', targets)
    self.assertEqual(len(targets), 3)
    self.assertEqual(targets['r1'], r1b)
    self.assertEqual(
        self.GetTargetsKeys(targets),
        [u'r0', u'r1', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 4)

    del targets['r1']
    self.assertNotIn('r1', targets)
    self.assertEqual(len(targets), 2)
    self.assertEqual(
        self.GetTargetsKeys(targets), [u'r0', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 3)

    del targets[traffic.LATEST_REVISION_KEY]
    self.assertNotIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 1)
    self.assertEqual(self.GetTargetsKeys(targets), [u'r0'])
    self.assertEqual(len(targets.MakeSerializable()), 2)

    targets[traffic.LATEST_REVISION_KEY] = latest
    self.assertIn(traffic.LATEST_REVISION_KEY, targets)
    self.assertEqual(len(targets), 2)
    self.assertEqual(
        self.GetTargetsKeys(targets), [u'r0', traffic.LATEST_REVISION_KEY])
    self.assertEqual(len(targets.MakeSerializable()), 3)

  def test_traffic_targets_equality_order_independent(self):
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 10),
            TrafficTarget('LATEST', 15, tag='test'),
            TrafficTarget('LATEST', 15, tag='foo'),
            TrafficTarget('r0', 25),
            TrafficTarget('LATEST', 15)
        ]),
        TrafficTargets([
            TrafficTarget('LATEST', 15, tag='foo'),
            TrafficTarget('LATEST', 15, tag='test'),
            TrafficTarget('r0', 25),
            TrafficTarget('r0', 10),
            TrafficTarget('LATEST', 15)
        ]))

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

  def test_merges_existing_duplicate_percent_targets(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 10),
        TrafficTarget('r1', 70),
        TrafficTarget('r0', 20)
    ])
    targets.UpdateTraffic({'r1': 75})
    self.assertEqual(targets, NewTrafficTargets({'r0': 25, 'r1': 75}))

  def test_ignores_zero_percent_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r1', tag='prod'),
        TrafficTarget('r2', tag='candidate')
    ])
    targets.UpdateTraffic({'r1': 80})
    self.assertEqual(
        targets,
        TrafficTargets([
            TrafficTarget('r0', 20),
            TrafficTarget('r1', 80),
            TrafficTarget('r0', tag='staging'),
            TrafficTarget('r1', tag='prod'),
            TrafficTarget('r2', tag='candidate')
        ]))

  def test_sorts_by_key_and_puts_tags_last(self):
    wrapped_targets = [
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r1', 75),
        TrafficTarget('LATEST', tag='head'),
        TrafficTarget('r0', 25),
        TrafficTarget('r0', tag='alpha'),
        TrafficTarget('r1', tag='prod'),
    ]
    targets = TrafficTargets(wrapped_targets)
    targets.UpdateTraffic({'r1': 80})
    self.assertEqual(wrapped_targets, [
        TrafficTarget('r0', 20),
        TrafficTarget('r1', 80),
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('LATEST', tag='head'),
        TrafficTarget('r0', tag='alpha'),
        TrafficTarget('r1', tag='prod'),
    ])

  def test_drops_existing_zero_percent_without_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 80),
        TrafficTarget('r1', 20),
        TrafficTarget('r2'),
    ])
    targets.UpdateTraffic({'r0': 30})
    self.assertEqual(
        targets,
        TrafficTargets([
            TrafficTarget('r0', 30),
            TrafficTarget('r1', 70)
        ]))

  def test_moves_tags_to_zero_percent_targets(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25, tag='test'),
        TrafficTarget('r1', 75, tag='prod'),
    ])
    targets.UpdateTraffic({'r0': 30})
    self.assertEqual(
        targets,
        TrafficTargets([
            TrafficTarget('r0', 30),
            TrafficTarget('r1', 70),
            TrafficTarget('r0', tag='test'),
            TrafficTarget('r1', tag='prod')
        ]))

  def test_keeps_tags_on_targets_that_go_to_zero(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75, tag='prod'),
    ])
    targets.UpdateTraffic({'r0': 100})
    self.assertEqual(
        targets,
        TrafficTargets(
            [TrafficTarget('r0', 100),
             TrafficTarget('r1', tag='prod')]))

  def test_zero_latest_traffic_latest_revision_not_present_handles_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('LATEST', 75),
        TrafficTarget('r0', tag='prod'),
        TrafficTarget('r1', tag='test'),
        TrafficTarget('LATEST', tag='staging'),
        TrafficTarget('LATEST', tag='candidate')
    ])
    targets.ZeroLatestTraffic('r1')
    self.assertEqual(
        targets,
        TrafficTargets([
            TrafficTarget('r0', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='prod'),
            TrafficTarget('r1', tag='test'),
            TrafficTarget('LATEST', tag='staging'),
            TrafficTarget('LATEST', tag='candidate')
        ]))

  def test_zero_latest_traffic_latest_revision_present_handles_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('LATEST', 75),
        TrafficTarget('r0', tag='prod'),
        TrafficTarget('r1', tag='test'),
        TrafficTarget('LATEST', tag='staging'),
        TrafficTarget('LATEST', tag='candidate')
    ])
    targets.ZeroLatestTraffic('r0')
    self.assertEqual(
        targets,
        TrafficTargets([
            TrafficTarget('r0', 100),
            TrafficTarget('r0', tag='prod'),
            TrafficTarget('r1', tag='test'),
            TrafficTarget('LATEST', tag='staging'),
            TrafficTarget('LATEST', tag='candidate')
        ]))


class TrafficTagsTest(test_case.TestCase):

  def test_adds_tag_to_existing_target(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'candidate': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='candidate'),
        ]), targets)

  def test_adds_tag_to_latest(self):
    targets = TrafficTargets([
        TrafficTarget('LATEST', 25),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'candidate': 'LATEST'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('LATEST', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('LATEST', tag='candidate'),
        ]), targets)

  def test_adds_tag_to_new_target(self):
    targets = TrafficTargets([
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({'candidate': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('r0', tag='candidate'),
        ]), targets)

  def test_adds_multiple_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'candidate': 'r0', 'prod': 'r1'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='candidate'),
            TrafficTarget('r1', tag='prod'),
        ]), targets)

  def test_adds_multiple_tags_to_same_revision(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'candidate': 'r0', 'staging': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='candidate'),
            TrafficTarget('r0', tag='staging'),
        ]), targets)

  def test_adds_tag_to_revision_with_existing_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25, tag='staging'),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'candidate': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 25, tag='staging'),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='candidate'),
        ]), targets)

  def test_adds_tag_to_revision_with_same_existing_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25, tag='staging'),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({'staging': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r0', 25),
            TrafficTarget('r1', 75),
            TrafficTarget('r0', tag='staging'),
        ]), targets)

  def test_adds_tag_to_zero_percent_revision_with_existing_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({'candidate': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('r0', tag='staging'),
            TrafficTarget('r0', tag='candidate'),
        ]), targets)

  def test_adds_tag_to_zero_percent_revision_with_same_existing_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({'staging': 'r0'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('r0', tag='staging')
        ]), targets)

  def test_adds_tag_to_latest_with_existing_tag(self):
    targets = TrafficTargets([
        TrafficTarget('LATEST', tag='staging'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({'candidate': 'LATEST'}, [], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('LATEST', tag='staging'),
            TrafficTarget('LATEST', tag='candidate'),
        ]), targets)

  def test_removes_tag(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25, tag='staging'),
        TrafficTarget('r1', 75),
    ])
    targets.UpdateTags({}, ['staging'], False)
    self.assertEqual(TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ]), targets)

  def test_removes_tag_from_zero_percent_target(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({}, ['staging'], False)
    self.assertEqual(TrafficTargets([
        TrafficTarget('r1', 100)
    ]), targets)

  def test_removes_multiple_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', 25, tag='staging'),
        TrafficTarget('r1', 75, tag='prod'),
    ])
    targets.UpdateTags({}, ['staging', 'prod'], False)
    self.assertEqual(TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ]), targets)

  def test_removes_latest_tag(self):
    targets = TrafficTargets([
        TrafficTarget('LATEST', tag='staging'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({}, ['staging'], False)
    self.assertEqual(TrafficTargets([
        TrafficTarget('r1', 100),
    ]), targets)

  def test_removes_tag_from_revision_with_multiple_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r0', tag='candidate'),
        TrafficTarget('r1', 100),
    ])
    targets.UpdateTags({}, ['staging'], False)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('r0', tag='candidate'),
        ]), targets)

  def test_updates_and_clears_existing_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r0', tag='candidate'),
        TrafficTarget('r1', 100, tag='current'),
    ])
    targets.UpdateTags({'prod': 'r1'}, [], True)
    self.assertEqual(
        TrafficTargets([
            TrafficTarget('r1', 100),
            TrafficTarget('r1', tag='prod'),
        ]), targets)

  def test_clears_tags(self):
    targets = TrafficTargets([
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('r0', tag='candidate'),
        TrafficTarget('r0', 25, tag='test'),
        TrafficTarget('r1', 75, tag='prod'),
    ])
    targets.UpdateTags({}, [], True)
    self.assertEqual(TrafficTargets([
        TrafficTarget('r0', 25),
        TrafficTarget('r1', 75),
    ]), targets)

  def test_preserves_existing_target_order_and_sorts_new_tags(self):
    wrapped_targets = [
        TrafficTarget('r0', 20),
        TrafficTarget('r1', 75),
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('LATEST', tag='head'),
        TrafficTarget('r0', 5, tag='canary'),
        TrafficTarget('LATEST', tag='candidate'),
        TrafficTarget('r0', tag='alpha'),
        TrafficTarget('r1', tag='prod'),
    ]
    targets = TrafficTargets(wrapped_targets)
    targets.UpdateTags({'ga': 'r1', 'alpha': 'r1', 'beta': 'r0'}, [], False)
    self.assertEqual(wrapped_targets, [
        TrafficTarget('r0', 20),
        TrafficTarget('r1', 75),
        TrafficTarget('r0', tag='staging'),
        TrafficTarget('LATEST', tag='head'),
        TrafficTarget('r0', 5, tag='canary'),
        TrafficTarget('LATEST', tag='candidate'),
        TrafficTarget('r1', tag='prod'),
        TrafficTarget('r1', tag='alpha'),
        TrafficTarget('r0', tag='beta'),
        TrafficTarget('r1', tag='ga'),
    ])


if __name__ == '__main__':
  test_case.main()
