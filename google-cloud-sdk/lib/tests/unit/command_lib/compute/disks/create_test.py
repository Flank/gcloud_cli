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

"""Unit tests for the disks create module."""
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.disks import create
from googlecloudsdk.core import resources
from tests.lib import cli_test_base
from tests.lib import test_case


class ParseRegionDisksResourcesTest(cli_test_base.CliTestBase):

  def SetUp(self):
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', 'alpha')

  def Create(self, collection, **kwargs):
    return self.resources.Create(collection, **kwargs)

  def CreateLink(self, collection, **kwargs):
    return self.Create(collection, **kwargs).SelfLink()

  def testProjectFromRegion(self):
    result = create.ParseRegionDisksResources(
        self.resources, ['disk-1'], ['central2-b', 'central2-c'], None,
        self.CreateLink(
            'compute.regions', project='project-1', region='central2'))

    self.assertEqual(result, [
        self.Create(
            'compute.regionDisks',
            project='project-1',
            region='central2',
            disk='disk-1'),
    ])

  def testProjectsCache(self):
    result = create.ParseRegionDisksResources(
        self.resources, ['disk-1', 'disk-2'], ['central2-b', 'central2-c'],
        None,
        self.CreateLink(
            'compute.regions', project='project-1', region='central2'))

    self.assertEqual(result, [
        self.Create(
            'compute.regionDisks',
            project='project-1',
            region='central2',
            disk='disk-1'),
        self.Create(
            'compute.regionDisks',
            project='project-1',
            region='central2',
            disk='disk-2'),
    ])

  def testZoneInDifferentProjectThanDisk(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--zone]: Zone [https://www.googleapis.com/compute/'
         'alpha/projects/project-2/zones/central2-b] lives in different '
         'project than disk [https://www.googleapis.com/compute/alpha/'
         'projects/project-1/regions/central2/disks/disk-1].')):
      create.ParseRegionDisksResources(self.resources, [
          self.CreateLink(
              'compute.regionDisks',
              project='project-1',
              region='central2',
              disk='disk-1')
      ], [
          self.CreateLink(
              'compute.zones', project='project-2', zone='central2-b'),
          self.CreateLink(
              'compute.zones', project='project-2', zone='central2-c')
      ], None, None)

  def testReplicaZonesInDifferentRegions(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Zones [central1-b, central2-c] '
         'live in different regions [central1, central2], but should live in '
         'the same.')):
      create.ParseRegionDisksResources(self.resources, [
          self.CreateLink(
              'compute.regionDisks',
              project='project-1',
              region='central2',
              disk='disk-1')
      ], [
          self.CreateLink(
              'compute.zones', project='project-1', zone='central1-b'),
          self.CreateLink(
              'compute.zones', project='project-1', zone='central2-c')
      ], None, None)

  def testReplicaZonesInconsistentWithExplicitRegion(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Region from [--replica-zones] '
         '(central2) is different from [--region] (central1).')):
      create.ParseRegionDisksResources(self.resources, [
          self.CreateLink(
              'compute.regionDisks',
              project='project-1',
              region='central2',
              disk='disk-1')
      ], [
          self.CreateLink(
              'compute.zones', project='project-1', zone='central2-b'),
          self.CreateLink(
              'compute.zones', project='project-1', zone='central2-c')
      ], None, 'central1')

  def testRegionFromDiskDifferentFromReplicaZones(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        ('Invalid value for [--replica-zones]: Region from [DISK_NAME] '
         '(https://www.googleapis.com/compute/alpha/projects/project-1/'
         'regions/central1/disks/disk-1) is different from [--replica-zones] '
         '(central2).')):
      create.ParseRegionDisksResources(self.resources, [
          self.CreateLink(
              'compute.regionDisks',
              project='project-1',
              region='central1',
              disk='disk-1')
      ], [
          self.CreateLink(
              'compute.zones', project='project-1', zone='central2-b'),
          self.CreateLink(
              'compute.zones', project='project-1', zone='central2-c')
      ], None, None)


if __name__ == '__main__':
  test_case.main()
