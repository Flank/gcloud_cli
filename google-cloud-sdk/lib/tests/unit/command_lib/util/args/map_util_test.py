# -*- coding: utf-8 -*- #
#
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Unit tests for the map_util module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util as calliope_util


_TEST_MAP = {'cod': 12, 'tomato': 2}

_TEST_MAP_YAML = 'cod: 12\ntomato: 2'

_TEST_KEYS = ['cod', 'tomato']


class MapUtilTestBase(sdk_test_base.WithTempCWD,
                      cli_test_base.CliTestBase):
  """Base class for map util tests."""

  def SetUp(self):
    self.parser = calliope_util.ArgumentParser()


class MapUtilFlagTest(MapUtilTestBase):
  """Tests various map flags individually."""

  def testMapUpdateFlag(self):
    """Standard --update-* invocation."""
    map_util.AddMapUpdateFlag(self.parser, 'food-prices',
                              'prices of food items', None, int)
    args = self.parser.parse_args(['--update-food-prices=cod=12,tomato=2'])

    self.assertEqual(args.update_food_prices, _TEST_MAP)

  def testMapSetFlag(self):
    """Standard --set-* invocation."""
    map_util.AddMapSetFlag(self.parser, 'food-prices',
                           'prices of food items', None, int)
    args = self.parser.parse_args(['--set-food-prices=cod=12,tomato=2'])

    self.assertEqual(args.set_food_prices, _TEST_MAP)

  def testMapRemoveFlag(self):
    """Standard --remove-* invocation."""
    map_util.AddMapRemoveFlag(self.parser, 'food-prices',
                              'prices of food items', None)
    args = self.parser.parse_args(['--remove-food-prices=cod,tomato'])

    self.assertEqual(args.remove_food_prices, _TEST_KEYS)

  def testMapClearFlag(self):
    """Standard --clear-* invocation."""
    map_util.AddMapClearFlag(self.parser, 'food-prices', 'prices of food items')
    args = self.parser.parse_args(['--clear-food-prices'])

    self.assertEqual(args.clear_food_prices, True)

  def testMapSetFileFlag(self):
    """Standard --*-file invocation."""
    map_util.AddMapSetFileFlag(self.parser, 'food-prices',
                               'prices of food items', None, int)
    files.WriteFileContents('daily-prices.yaml', _TEST_MAP_YAML)
    args = self.parser.parse_args(['--food-prices-file=daily-prices.yaml'])

    self.assertEqual(args.food_prices_file, _TEST_MAP)

  def testMapSetFileFlag_FileMissing(self):
    """Standard --*-file invocation, file is missing."""
    map_util.AddMapSetFileFlag(self.parser, 'food-prices',
                               'prices of food items', None, int)
    with self.assertRaises(yaml.FileLoadError):
      self.parser.parse_args(['--food-prices-file=unknown-file'])


class MapUtilCompoundFlagsTest(MapUtilTestBase,
                               parameterized.TestCase):
  """Tests multiple map flags and evaluates their combined semantics."""

  def SetUp(self):
    map_util.AddUpdateMapFlags(self.parser, 'food-prices',
                               'prices of food items', None, int)
    self.old_map = {'B': 2, 'C': 3, 'D': 4}

  @parameterized.parameters(
      (['--update-food-prices=A=1', '--clear-food-prices'],),
      (['--set-food-prices=A=1', '--update-food-prices=B=2'],),
      (['--set-food-prices=A=1', '--remove-food-prices=B'],),
  )
  def testMutuallyExclusiveErrors(self, args):
    """All flags are mutually exclusive except for --update-* and --remove-*."""
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args(args)

  def testMutuallyExclusiveFile(self):
    """Check simple mutual exclusion with a file reference."""
    files.WriteFileContents('daily-prices.yaml', _TEST_MAP_YAML)
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args([
          '--food-prices-file=daily-prices.yaml',
          '--set-food-prices'])

  def testUpdateAndRemoveFlags(self):
    """Check that --update-* and --remove-* works in conjunction."""
    args = self.parser.parse_args([
        '--update-food-prices=A=1,B=22', '--remove-food-prices=C'])
    map_flags = map_util.GetMapFlagsFromArgs('food-prices', args)
    expected = {
        'set_flag_value': None,
        'update_flag_value': {'A': 1, 'B': 22},
        'clear_flag_value': None,
        'remove_flag_value': ['C'],
        'file_flag_value': None,
    }
    self.assertEqual(map_flags, expected)

    new_map = map_util.ApplyMapFlags(self.old_map, **map_flags)
    self.assertEqual(new_map, {'A': 1, 'B': 22, 'D': 4})

  def testSetFlag(self):
    """Check that --set-* works."""
    args = self.parser.parse_args(['--set-food-prices=B=22,E=5'])
    map_flags = map_util.GetMapFlagsFromArgs('food-prices', args)
    expected = {
        'set_flag_value': {'B': 22, 'E': 5},
        'update_flag_value': None,
        'clear_flag_value': None,
        'remove_flag_value': None,
        'file_flag_value': None,
    }
    self.assertEqual(map_flags, expected)

    new_map = map_util.ApplyMapFlags(self.old_map, **map_flags)
    self.assertEqual(new_map, {'B': 22, 'E': 5})

  def testRemoveFlag(self):
    """Check that --remove-* works."""
    args = self.parser.parse_args(['--remove-food-prices=C,D'])
    map_flags = map_util.GetMapFlagsFromArgs('food-prices', args)
    expected = {
        'set_flag_value': None,
        'update_flag_value': None,
        'clear_flag_value': None,
        'remove_flag_value': ['C', 'D'],
        'file_flag_value': None,
    }
    self.assertEqual(map_flags, expected)

    new_map = map_util.ApplyMapFlags(self.old_map, **map_flags)
    self.assertEqual(new_map, {'B': 2})

  def testClearFlag(self):
    """Check that --clear-* works."""
    args = self.parser.parse_args(['--clear-food-prices'])
    map_flags = map_util.GetMapFlagsFromArgs('food-prices', args)
    expected = {
        'set_flag_value': None,
        'update_flag_value': None,
        'clear_flag_value': True,
        'remove_flag_value': None,
        'file_flag_value': None,
    }
    self.assertEqual(map_flags, expected)

    new_map = map_util.ApplyMapFlags(self.old_map, **map_flags)
    self.assertEqual(new_map, {})

  def testSetFileFlag(self):
    """Check that --*-file works."""
    files.WriteFileContents('daily-prices.yaml', _TEST_MAP_YAML)
    args = self.parser.parse_args(['--food-prices-file=daily-prices.yaml'])
    map_flags = map_util.GetMapFlagsFromArgs('food-prices', args)
    expected = {
        'set_flag_value': None,
        'update_flag_value': None,
        'clear_flag_value': None,
        'remove_flag_value': None,
        'file_flag_value': _TEST_MAP,
    }
    self.assertEqual(map_flags, expected)

    new_map = map_util.ApplyMapFlags(self.old_map, **map_flags)
    self.assertEqual(new_map, {'cod': 12, 'tomato': 2})


if __name__ == '__main__':
  test_case.main()
