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
"""Tests for google3.third_party.py.tests.unit.surface.compute.instances.os_inventory.list_instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import textwrap
import zlib

from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute import utils


class ListInstancesTestBase(test_base.BaseTest,
                            completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi(self.api_version)

    self.api_mock = utils.ComputeApiMock(self.api_version).Start()
    self.addCleanup(self.api_mock.Stop)

    # os-inventory list implementation always uses this implementation
    self.implementation = lister.MultiScopeLister(
        self.api_mock.adapter,
        zonal_service=self.api_mock.adapter.apitools_client.instances,
        aggregation_service=self.api_mock.adapter.apitools_client.instances)

    if self.api_version == 'v1':
      self.instances = test_resources.INSTANCES_V1
    elif self.api_version == 'beta':
      self.instances = test_resources.INSTANCES_BETA
    elif self.api_version == 'alpha':
      self.instances = test_resources.INSTANCES_ALPHA
    else:
      raise ValueError(
          'api_version must be  \'v1\', \'beta\' or \'alpha\', got [{0}]'
          .format(self.api_version))

  def TearDown(self):
    self.api_mock.batch_responder.AssertDone()

  def CreateInstancesGetGuestAttributesRequest(self, instance_name):
    return self.api_mock.messages.ComputeInstancesGetGuestAttributesRequest(
        instance=instance_name,
        project=self.Project(),
        queryPath='guestInventory/',
        zone='zone-1')

  def GetGuestAttributes(self, instance_name):
    installed_packages = (b'{"deb":[{"Name":"' + instance_name.encode() +
                          b'-package1.1","Arch":"all","Version":"v1"}]}')

    return self.api_mock.messages.GuestAttributes(
        kind='compute#guestAttributes',
        queryPath='guestInventory/',
        queryValue=self.messages.GuestAttributesValue(items=[
            self.messages.GuestAttributesEntry(
                key='Hostname', namespace='guestInventory',
                value=instance_name),
            self.messages.GuestAttributesEntry(
                key='ShortName',
                namespace='guestInventory',
                value='debian-' + instance_name),
            self.messages.GuestAttributesEntry(
                key='Version',
                namespace='guestInventory',
                value='9-' + instance_name),
            self.messages.GuestAttributesEntry(
                key='KernelVersion',
                namespace='guestInventory',
                value='4.9.0-' + instance_name),
            self.messages.GuestAttributesEntry(
                key='InstalledPackages',
                namespace='guestInventory',
                value=base64.b64encode(zlib.compress(installed_packages)))
        ]),
        selfLink='link-to-instance?')

  def GetBatchRequestsAndResponses(self, instances):
    return [((self.compute.instances, 'GetGuestAttributes',
              self.CreateInstancesGetGuestAttributesRequest(instance.name)),
             self.GetGuestAttributes(instance.name)) for instance in instances]


class ListInstancesTestGA(ListInstancesTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testNoInventoryFilterArg(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run('compute instances os-inventory list-instances --uri')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-3
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testInventoryFilterContainingAllInstances(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --inventory-filter="" --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-3
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testInventoryFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --inventory-filter="InstalledPackages.deb[].['instance-1-package1.1'].Version>=v0" --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testInventoryFilterWithInstanceFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --inventory-filter="Hostname=instance-1" --filter="name=instance-2"
        --uri
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testInventoryFilterWithLimit(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        max_results=None,
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --inventory-filter="Hostname:instance" --limit=2 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testInventoryFilterWithSortBy(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --inventory-filter="NOT(Hostname=instance-3)" --sort-by ~name --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testOsShortnameFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --os-shortname debian-instance-1 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testOsVersionFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --os-version 9-instance-2 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testKernelVersionFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --kernel-version 4.9.0-instance-3 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-3
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testPackageNameFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --package-name instance-1-package1.1 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-1
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testPackageNameAndVersionFilter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --package-name instance-2-package1.1 --package-version v1 --uri
        """)
    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://compute.googleapis.com/compute/{api_version}/projects/my-project/zones/zone-1/instances/instance-2
            """.format(api_version=self.api_version)))
    self.AssertErrEquals('')

  def testPackageVersionFilterWithoutPackageName(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [{0}]: {1}'.format(
            '--package-version',
            """package version must be specified together with a package name. e.g. --package-name google-cloud-sdk --package-version 235.0.0-0"""
        )):
      self.Run("""
        compute instances os-inventory list-instances --package-version v1 --uri
        """)
    self.assertFalse(self.GetOutput())

  def testAllFilters(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""
        compute instances os-inventory list-instances
        --filter="name:(instance-1,instance-2)"
        --inventory-filter="Hostname=instance-1"
        --os-shortname="debian-instance-1"
        --os-version="9-instance-1"
        --kernel-version="4.9.0-instance-3"
        --package-name="instance-1-package1.1"
        --package-version="v10"
        --uri
        """)
    self.AssertOutputEquals('')
    self.AssertErrContains('Listed 0 items.')

  def testTableOutput(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopesWithRegistry(self.api_mock.resources),
        result=resource_projector.MakeSerializable(self.instances),
        with_implementation=self.implementation)
    self.api_mock.batch_responder.ExpectBatch(
        self.GetBatchRequestsAndResponses(self.instances))

    self.Run("""compute instances os-inventory list-instances""")
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       ZONE   MACHINE_TYPE  PREEMPTIBLE INTERNAL_IP EXTERNAL_IP   STATUS
            instance-1 zone-1 n1-standard-1             10.0.0.1    23.251.133.75 RUNNING
            instance-2 zone-1 n1-standard-1             10.0.0.2    23.251.133.74 RUNNING
            instance-3 zone-1 n1-standard-2             10.0.0.3    23.251.133.76 RUNNING
            """),
        normalize_space=True)
    self.AssertErrEquals('')


class ListInstancesTestBeta(ListInstancesTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class ListInstancesTestAlpha(ListInstancesTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
