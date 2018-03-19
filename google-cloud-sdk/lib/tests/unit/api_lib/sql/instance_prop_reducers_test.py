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
"""Tests for googlecloudsdk.api_lib.sql.instances."""

import argparse
from googlecloudsdk.api_lib.sql import instance_prop_reducers as reducers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from tests.lib import subtests
from tests.lib import test_case
from tests.lib.calliope import util


class MachineTypeFromArgsTest(subtests.Base):
  """Tests reducers.MachineType."""

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.parser.add_argument('--cpu', type=int, help='Auxilio aliis.')
    self.parser.add_argument('--memory', type=arg_parsers.BinarySize(),
                             help='Auxilio aliis.')
    self.parser.add_argument('--tier', '-t', help='Auxilio aliis.')

  def testTier(self):
    args = self.parser.parse_args('--tier D0'.split())
    self.assertEqual('D0', reducers.MachineType(tier=args.tier))

  def testCustomMemoryAndCpu(self):
    args = self.parser.parse_args('--cpu 1 --memory 1024MiB'.split())
    self.assertEqual('db-custom-1-1024',
                     reducers.MachineType(memory=args.memory, cpu=args.cpu))

  def testNoInstanceDefaultValue(self):
    self.assertEqual('db-n1-standard-1', reducers.MachineType())

  def testExistingInstanceDefaultValue(self):
    instance = object()
    self.assertEqual(None, reducers.MachineType(instance))

  def testNoMemorySpecified(self):
    args = self.parser.parse_args('--cpu 2'.split())
    try:
      reducers.MachineType(cpu=args.cpu)
    except exceptions.RequiredArgumentException:
      assert True

  def testNoCPUSpecified(self):
    args = self.parser.parse_args('--memory 1024MiB'.split())
    try:
      reducers.MachineType(memory=args.memory)
    except exceptions.RequiredArgumentException:
      assert True

  def testTierAndCustomMachineSpecified(self):
    args = self.parser.parse_args('--tier D0 --cpu 2 --memory 1024MiB'.split())
    try:
      reducers.MachineType(tier=args.tier, memory=args.memory, cpu=args.cpu)
    except exceptions.InvalidArgumentException:
      assert True


class ConstructCustomMachineTypeTest(subtests.Base):
  """Tests reducers._ConstructCustomMachineType."""

  def test2Cpus1024MiB(self):
    self.assertEqual('db-custom-2-1024',
                     reducers._CustomMachineTypeString(2, 1024))

  def testStringArgs(self):
    self.assertEqual('db-custom-2-1024',
                     reducers._CustomMachineTypeString('2', '1024'))


class RegionTest(subtests.Base):
  """Tests reducers.Region."""

  def SetUp(self):
    self.parser = argparse.ArgumentParser()
    self.parser.add_argument('--region')
    self.parser.add_argument('--gce-zone')

  def testConsistentRegionAndZone(self):
    args = self.parser.parse_args(
        '--region europe-west1 --gce-zone europe-west1-a'.split())
    self.assertEqual(
        reducers.Region(args.region, args.gce_zone), 'europe-west1')

  def testInconsistentRegionAndZone(self):
    args = self.parser.parse_args(
        '--region us-central1 --gce-zone europe-west1-a'.split())
    # The zone is more precise than the region, so should inform the region.
    self.assertEqual(
        reducers.Region(args.region, args.gce_zone), 'europe-west1')

  def testRegionAndNoZone(self):
    args = self.parser.parse_args('--region us-central1'.split())
    self.assertEqual(reducers.Region(args.region, args.gce_zone), 'us-central1')

  def testZoneAndNoRegion(self):
    args = self.parser.parse_args('--gce-zone us-central1-b'.split())
    self.assertEqual(reducers.Region(args.region, args.gce_zone), 'us-central1')


if __name__ == '__main__':
  test_case.main()
