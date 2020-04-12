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
"""Tests for the instances import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resources import InvalidResourceException
from tests.lib import test_case
from tests.lib.surface.compute import ovf_import_test_base
from tests.lib.surface.compute import test_resources

_DEFAULT_TIMEOUT = '7056s'


class InstanceImportTest(ovf_import_test_base.OVFimportTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.instance_name = 'my-instance'
    self.resource_name = self.instance_name
    self.source_uri = 'gs://31dd/source-vm.ova'
    self.https_source_disk = ('https://storage.googleapis.com/'
                              '31dd/source-vm.ova')
    self.ovf_builder = daisy_utils._OVF_IMPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.os = 'ubuntu-1604'
    self.tags = ['gce-ovf-import']
    self.zone = 'us-west1-c'
    properties.VALUES.compute.zone.Set(self.zone)

  def PrepareZonalMocksForValidZone(self, zone):
    # The empty list is for the response of _CheckForExistingInstance, i.e.
    # no existing instance with given name, so validation can proceed to zone
    # validation.
    self.make_requests.side_effect = iter([
        [],
        [self.compute_v1_messages.Zone(name=zone)],
    ])

  def PrepareZonalMocksForInvalidZone(self, zone):
    # Need to use a closure to mock MakeRequests due to the combination of
    # a return value and an exception for the two calls that are being mocked
    def make_requests_mock(requests,
                           errors_to_collect=None,
                           progress_tracker=None,
                           followup_overrides=None,
                           http=None,
                           errors=None,
                           batch_url=None,
                           log_result=None):
      del errors_to_collect, progress_tracker, followup_overrides, http, errors, batch_url, log_result

      # Easier to check type of the request using strings due to different
      # release tracks having different implementations for each request type
      if requests and requests[0][1] == 'Get' and str.endswith(
          type(requests[0][2]).__name__, 'ComputeInstancesGetRequest'):
        # For the call to _CheckForExistingInstances
        return []
      else:
        # For the call to daisy_utils.ValidateZone
        raise exceptions.ToolException('')

    self.make_requests.side_effect = make_requests_mock

  def GetOVFImportStep(self, instance_names=None):
    return self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(instance_names or self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
    ],)

  def GetOVFNetworkStep(self, network_args):
    return self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
    ] + network_args + [
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
    ])

  def GetOVFImportStepForArgs(self, args):
    return self.cloudbuild_v1_messages.BuildStep(
        args=args,
        name=self.ovf_builder,
    )

  def PrepareMocks(self,
                   step,
                   async_flag=False,
                   permissions=None,
                   timeout='7200s'):
    self.PrepareDaisyMocks(
        step, async_flag=async_flag, permissions=permissions, timeout=timeout)

  def testCommonCase(self):
    self.PrepareMocks(self.GetOVFImportStep())
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             """.format(self.instance_name, self.source_uri, self.os))

  def testHttpsLinkToGcsImageNoAPIVersion(self):
    self.doTestHttpLinkToGcsImage(
        'https://storage.googleapis.com/31dd/source-vm.ova')

  def testHttpsLinkToGcsImageWithAPIVersion(self):
    self.doTestHttpLinkToGcsImage(
        'https://www.googleapis.com/storage/v1/b/31dd/o/source-vm.ova')

  def testHttpLinkToGcsImageWithAPIVersion(self):
    self.doTestHttpLinkToGcsImage(
        'http://www.googleapis.com/storage/v1/b/31dd/o/source-vm.ova')

  def doTestHttpLinkToGcsImage(self, http_url):
    """Make sure http(s):// URIs are converted correctly to gs:// ones.

    This test should behave *exactly* like testCommonCase. gcloud ought to
    recognize a URI like https://storage.googleapis.com/bucket/image.ova
    and translate it to gs://bucket/image.ova automatically.

    Args:
      http_url: HTTP style GCS URI.
    """
    self.PrepareMocks(self.GetOVFImportStep())
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2}
               """.format(self.instance_name, http_url, self.os))

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "http(s)://" URLs that point to GCS are accepted."""
    with self.assertRaises(InvalidResourceException):
      self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(self.instance_name,
                          'https://example.com/not-a-gcs-bucket/va.ova',
                          self.os))

  def testAsync(self):
    self.PrepareMocks(self.GetOVFImportStep(), async_flag=True)
    self.Run("""
               compute instances import {0}
               --source-uri {1} --os {2} --async
               """.format(self.instance_name, self.source_uri, self.os))
    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testTimeoutFlag(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=59s',  # OVF import timeout 2% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step, timeout='60s')
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --timeout 1m
               """.format(self.instance_name, self.source_uri, self.os))

  def testLongTimeoutFlag(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=21300s',  # OVF import timeout 5min sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step, timeout='21600s')
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --timeout 6h
               """.format(self.instance_name, self.source_uri, self.os))

  def testExitOnMissingPermissions(self):
    missing_permissions = self.crm_v1_messages.Policy(bindings=[],)
    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',),
        response=self.project,
    )
    self._ExpectServiceUsage()
    self._ExpectIamRolesGet(
        is_import=True, permissions=missing_permissions, skip_compute=True)
    get_request = self.crm_v1_messages \
        .CloudresourcemanagerProjectsGetIamPolicyRequest(
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
                options=self.crm_v1_messages.GetPolicyOptions(
                    requestedPolicyVersion=
                    iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
            resource='my-project')
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=missing_permissions,
    )
    with self.assertRaises(console_io.UnattendedPromptError):
      self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(self.instance_name, self.source_uri, self.os))

  def testOVFImportUsesZoneArg(self):
    self.doZoneFlagTest()

  def testOVFImportUsesZoneConfigProperty(self):
    properties.VALUES.compute.zone.Set('us-west1-c')
    self.doZoneFlagTest(add_zone_cli_arg=False)

  def doZoneFlagTest(self,
                     add_zone_cli_arg=True,
                     zone='us-central1-b',
                     is_valid_zone=True):

    flags = '{0} --source-uri {1} --os {2}'
    zone_arg = properties.VALUES.compute.zone.Get()
    if add_zone_cli_arg:
      # Testing if zone is being used from CLI arg (vs. global config property)
      zone_arg = zone
      properties.VALUES.compute.zone.Set('')
      flags += ' --zone ' + zone_arg

    ovf_import_step_with_zone = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(zone_arg),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
    ])

    # Setting up mocks
    if is_valid_zone:
      self.PrepareZonalMocksForValidZone(zone)
      self.PrepareMocks(ovf_import_step_with_zone)
    else:
      # No standard mocks are needed for invalid zone as the logic terminates
      # before any of the mocks are called.
      self.PrepareZonalMocksForInvalidZone(zone)

    if is_valid_zone:
      self._RunAndAssertSuccess(
          flags.format(self.instance_name, self.source_uri, self.os))
    else:
      # Assertion to be done by calling function
      self._RunFlags(flags.format(self.instance_name, self.source_uri, self.os))

  def testMissingSourceUri(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-uri: Must be specified.'):
      self._RunFlags('{0} --os {1}'.format(self.instance_name, self.os))

  def testMissingInstanceName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument INSTANCE_NAME: Must be specified.'):
      self._RunFlags('--source-uri {0} --os {1}'.format(self.source_uri,
                                                        self.os))

  def testNoGuestEnvironment(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-no-guest-environment',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))

    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --no-guest-environment
             """.format(self.instance_name, self.source_uri, self.os))

  def testCanIPForward(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-can-ip-forward',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --can-ip-forward
             """.format(self.instance_name, self.source_uri, self.os))

  def testDeletionProtection(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-deletion-protection',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --deletion-protection
             """.format(self.instance_name, self.source_uri, self.os))

  def testDescription(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-description=a_desc',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --description=a_desc
             """.format(self.instance_name, self.source_uri, self.os))

  def testLabels(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-labels=lk1=lv1,lk2=lv2',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --labels=lk1=lv1,lk2=lv2
             """.format(self.instance_name, self.source_uri, self.os))

  def testMachineType(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=n2-standard-4',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --machine-type=n2-standard-4
             """.format(self.instance_name, self.source_uri, self.os))

  def testCustomMachineNoExtendedMemory(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=custom-2-5120',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --custom-cpu=2 --custom-memory=5242880KB
             """.format(self.instance_name, self.source_uri, self.os))

  def testCustomMachineExtendedMemory(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=n1-custom-2-5120-ext',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --custom-vm-type n1 --custom-cpu=2 --custom-memory=5242880KB --custom-extensions
             """.format(self.instance_name, self.source_uri, self.os))

  def testCustomMemoryWithoutCPU(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-memory: --custom-cpu must be specified.'):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-memory=5242880KB
               """.format(self.instance_name, self.source_uri, self.os))

  def testCustomCPUWithoutMemory(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-cpu=2
               """.format(self.instance_name, self.source_uri, self.os))

  def testCustomExtensionWithoutCPUOrMemory(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-extensions: --custom-cpu --custom-memory must be specified.'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-extensions
               """.format(self.instance_name, self.source_uri, self.os))

  def testMachineTypeAndCustomCPUMachineSet(self):
    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--machine-type\]: Cannot set both '
        r'\[--machine-type\] and \[--custom-cpu\]/\[--custom-memory\]'
        r' for the same instance.'):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --machine-type=n1-standard-2
               --custom-cpu=2 --custom-memory=2048MB
               """.format(self.instance_name, self.source_uri, self.os))

  def testNetwork(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-network=anetwork']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network=anetwork
             """.format(self.instance_name, self.source_uri, self.os))

  def testNetworkAndSubnet(self):
    self.PrepareMocks(
        self.GetOVFNetworkStep(['-network=anetwork', '-subnet=asubnet']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network=anetwork --subnet=asubnet
             """.format(self.instance_name, self.source_uri, self.os))

  def testSubnetWithoutNetwork(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-subnet=asubnet']))
    self._RunFlags("""
             {0} --source-uri {1} --os {2} --subnet=asubnet
             """.format(self.instance_name, self.source_uri, self.os))

  def testNetworkTier(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-network-tier=PREMIUM']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network-tier=PREMIUM
             """.format(self.instance_name, self.source_uri, self.os))

  def testInvalidNetworkTier(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-tier\]: Invalid network tier \[NOT_A_TIER\]'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --network-tier=NOT_A_TIER
               """.format(self.instance_name, self.source_uri, self.os))

  def testPrivateNetworkIP(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-private-network-ip=10.0.0.1']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --private-network-ip=10.0.0.1
             """.format(self.instance_name, self.source_uri, self.os))

  def testNoRestartOnFailure(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-instance-names={0}'.format(self.instance_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-no-restart-on-failure',
            '-os={0}'.format(self.os),
            '-zone={0}'.format(self.zone),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
        ]))

    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --no-restart-on-failure
             """.format(self.instance_name, self.source_uri, self.os))

  def testInvalidInstanceNames(self):
    invalid_names = [
        'test-',
        'Hello',
        '4image',
        'my_image',
        ('this-is-a-very-long-image-name-that-is-longer-than'
         '-64-characters-but-otherwise-ok'),
    ]
    for name in invalid_names:
      with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                            'Name must start with a lowercase'):
        self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(name, self.source_uri, self.os))

  def testExistingInstance(self):
    self.make_requests.side_effect = iter([
        [test_resources.INSTANCES_V1[0]],
        [self.compute_v1_messages.Zone(name=self.zone)],
    ])
    instance_name = 'my-instance'
    error = (r'The instance \[{instance_name}\] already exists in zone '
             r'\[{zone}\]').format(
                 instance_name=instance_name, zone=self.zone)

    with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                          error):
      self._RunFlags("""
          {0} --source-uri {1} --os {2}
          """.format(instance_name, self.source_uri, self.os))

  def testTags(self):
    tags = 't1,t2,t3'
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-tags={0}'.format(tags),
        '-zone={0}'.format(self.zone),
        '-timeout=7056s',  # OVF import timeout 2% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --tags {3}
               """.format(self.instance_name, self.source_uri, self.os, tags))

  def testSoleTenantNode(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=7056s',  # OVF import timeout 2% sooner than Argo.
        '-node-affinity-label=compute.googleapis.com/node-name,IN,A_NODE',
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --node A_NODE
               """.format(self.instance_name, self.source_uri, self.os))

  def testSoleTenantNodeGroup(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=7056s',  # OVF import timeout 2% sooner than Argo.
        '-node-affinity-label=compute.googleapis.com/node-group-name,IN,A_NODE_GROUP',
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --node-group A_NODE_GROUP
               """.format(self.instance_name, self.source_uri, self.os))

  def testSoleTenantNodeAffinityFile(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=7056s',  # OVF import timeout 2% sooner than Argo.
        '-node-affinity-label=key1,IN,value1,value2',
        '-node-affinity-label=key2,NOT_IN,value3,value4,value5',
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step)
    contents = """\
[
  {"operator": "IN", "values": ["value1", "value2"], "key": "key1"},
  {"operator": "NOT_IN", "values": ["value3", "value4", "value5"], "key": "key2"}
]
    """
    node_affinity_file = self.Touch(
        self.temp_path, 'affinity_config.json', contents=contents)

    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2}
               --node-affinity-file {3}
               """.format(self.instance_name, self.source_uri, self.os,
                          node_affinity_file))

  def testSourceFileBucketOnlyGCSPath(self):
    self.doTestSourceFileBucketOnly('gs://bucket-name')

  def testSourceFileBucketOnlyWithTrailingSlashGCSPath(self):
    self.doTestSourceFileBucketOnly('gs://bucket-name/')

  def testSourceFileBucketOnlyHttpsGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'https://www.googleapis.com/storage/v1/b/bucket-name')

  def testSourceFileBucketOnlyWithTrailingSlashHttpsGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'https://www.googleapis.com/storage/v1/b/bucket-name/')

  def testSourceFileBucketOnlyHttpGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'http://www.googleapis.com/storage/v1/b/bucket-name')

  def testSourceFileBucketOnlyWithTrailingSlashHttpGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'http://www.googleapis.com/storage/v1/b/bucket-name/')

  def doTestSourceFileBucketOnly(self, bucket_path):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format('gs://bucket-name/'),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout=7056s',  # OVF import timeout 2% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             """.format(self.instance_name, bucket_path, self.os))

  def testSourceFileErrorOnInvalidGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [source-uri]: must be a path to an object or a directory in Google Cloud Storage'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(self.instance_name, 'not-a-gcs-path', self.os))

  def testDockerImageTag(self):
    self.ovf_builder = daisy_utils._OVF_IMPORT_BUILDER.format(
        daisy_utils._DEFAULT_BUILDER_VERSION)
    self.testCommonCase()

    self.ovf_builder = daisy_utils._OVF_IMPORT_BUILDER.format('latest')
    self.PrepareMocks(self.GetOVFImportStep())
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --docker-image-tag latest
             """.format(self.instance_name, self.source_uri, self.os))

  def _RunFlags(self, flags):
    self.Run('compute instances import {0}'.format(flags))

  def _RunAndAssertSuccess(self, flags):
    self._RunFlags(flags)
    self.AssertOutputContains(
        """\
        [import-ovf] output
        """, normalize_space=True)

  def testOVFImportFailsOnInvalidZoneArg(self):
    invalid_zone = 'not-a-zone'
    error = r'Invalid value for \[--zone\]: {0}'.format(invalid_zone)

    with self.AssertRaisesExceptionRegexp(exceptions.InvalidArgumentException,
                                          error):
      self.doZoneFlagTest(zone=invalid_zone, is_valid_zone=False)

  def testHostname(self):
    hostname = 'a-hostname.a-domain'
    step = self.GetOVFImportStepForArgs([
        '-instance-names={0}'.format(self.instance_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(self.zone),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
        '-hostname={0}'.format(hostname),
    ],)
    self.PrepareMocks(step)
    self.Run("""
                 compute instances import {0}
                 --source-uri {1} --os {2} --hostname {3}
                 """.format(self.instance_name, self.source_uri, self.os,
                            hostname))
    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')


class InstanceImportTestBeta(InstanceImportTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class InstanceImportTestAlpha(InstanceImportTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
