# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the machine images import command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resources import InvalidResourceException
from tests.lib import test_case
from tests.lib.surface.compute import ovf_import_test_base

_DEFAULT_TIMEOUT = '6984s'


class MachineImageImportTestBeta(ovf_import_test_base.OVFimportTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def SetUp(self):
    self.machine_image_name = 'my-machine-image'
    self.resource_name = self.machine_image_name
    self.source_uri = 'gs://31dd/source-vm.ova'
    self.https_source_disk = ('https://storage.googleapis.com/'
                              '31dd/source-vm.ova')
    self.ovf_builder = ''
    self.os = 'ubuntu-1604'
    self.tags = ['gce-daisy', 'gce-ovf-machine-image-import']
    self.zone = 'us-west1-c'

  def PrepareZonalMocksForValidZone(self, zone):
    self.make_requests.side_effect = iter([
        [self.compute_v1_messages.Zone(name=zone)],
    ])

  def PrepareZonalMocksForInvalidZone(self):
    # Need to use a closure to mock MakeRequests due to the combination of
    # a return value and an exception for the two calls that are being mocked
    def make_requests_mock(requests,
                           errors_to_collect=None,
                           progress_tracker=None,
                           followup_overrides=None,
                           always_return_operation=None,
                           no_followup=None,
                           http=None,
                           errors=None,
                           batch_url=None,
                           log_result=None,
                           timeout=None):
      del requests, errors_to_collect, progress_tracker, followup_overrides, no_followup, http, errors, batch_url, log_result, timeout, always_return_operation
      # For the call to daisy_utils.ValidateZone
      raise exceptions.ToolException('')
    self.make_requests.side_effect = make_requests_mock

  def prepareArtifactRegistryMocks(self,
                                   expect_source_file_bucket_check=True,
                                   expected_builder_location='',
                                   regionalized=True):
    pass

  def GetOVFImportStep(self, machine_image_name=None):
    return self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(machine_image_name or
                                         self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])

  def GetOVFNetworkStep(self, network_args):
    return self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
    ] + network_args + [
        '-os={0}'.format(self.os),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])

  def GetOVFImportStepForArgs(self, args, zone=''):
    return self.cloudbuild_v1_messages.BuildStep(
        args=args,
        name=self.GetBuilder(zone=zone, region='my-region'),
    )

  def GetBuilder(self,
                 zone='',
                 region='',
                 tag=daisy_utils._DEFAULT_BUILDER_VERSION):
    if self.ovf_builder:
      return self.ovf_builder
    return daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
        executable=daisy_utils._OVF_IMPORT_BUILDER_EXECUTABLE,
        docker_image_tag=tag)

  def PrepareMocks(self,
                   step,
                   async_flag=False,
                   permissions=None,
                   timeout='7200s',
                   log_location=None,
                   zone=''):
    self.PrepareDaisyMocks(
        step,
        async_flag=async_flag,
        permissions=permissions,
        timeout=timeout,
        log_location=log_location)
    self.prepareArtifactRegistryMocks(
        expect_source_file_bucket_check=False if zone else True,
        expected_builder_location=daisy_utils
        .GetRegionFromZone(zone) if zone else '')

  def testCommonCase(self):
    self.PrepareMocks(self.GetOVFImportStep())
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             """.format(self.machine_image_name, self.source_uri, self.os))

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
               """.format(self.machine_image_name, http_url, self.os))

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "http(s)://" URLs that point to GCS are accepted."""
    with self.assertRaises(InvalidResourceException):
      self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(self.machine_image_name,
                          'https://example.com/not-a-gcs-bucket/va.ova',
                          self.os))

  def testAsync(self):
    self.PrepareMocks(self.GetOVFImportStep(), async_flag=True)
    self.Run("""
               compute machine-images import {0}
               --source-uri {1} --os {2} --async
               """.format(self.machine_image_name, self.source_uri, self.os))
    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testTimeoutFlag(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-timeout=59s',  # OVF import timeout 2% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])
    self.PrepareMocks(ovf_import_step, timeout='60s')
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --timeout 1m
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testLongTimeoutFlag(self):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-timeout=21300s',  # OVF import timeout 5min sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])
    self.PrepareMocks(ovf_import_step, timeout='21600s')
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --timeout 6h
               """.format(self.machine_image_name, self.source_uri, self.os))

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
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testOVFImportUsesZoneArg(self):
    self.doZoneFlagTest()

  def testOVFImportUsesZoneConfigProperty(self):
    properties.VALUES.compute.zone.Set('us-west1-c')
    self.doZoneFlagTest(add_zone_cli_arg=False, zone='us-west1-c')
    properties.VALUES.compute.zone.Set('')

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
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-zone={0}'.format(zone_arg),
        '-timeout={0}'.format(_DEFAULT_TIMEOUT),
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ], zone=zone)

    # Setting up mocks
    if is_valid_zone:
      self.PrepareZonalMocksForValidZone(zone)
      self.PrepareMocks(ovf_import_step_with_zone, zone=zone)
    else:
      # No standard mocks are needed for invalid zone as the logic terminates
      # before any of the mocks are called.
      self.PrepareZonalMocksForInvalidZone()

    if is_valid_zone:
      self._RunAndAssertSuccess(
          flags.format(self.machine_image_name, self.source_uri, self.os))
    else:
      # Assertion to be done by calling function
      self._RunFlags(
          flags.format(self.machine_image_name, self.source_uri, self.os))

  def testMissingSourceUri(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source-uri: Must be specified.'):
      self._RunFlags('{0} --os {1}'.format(self.machine_image_name, self.os))

  def testMissingMachineImageName(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument IMAGE: Must be specified.'):
      self._RunFlags('--source-uri {0} --os {1}'.format(self.source_uri,
                                                        self.os))

  def testNoGuestEnvironment(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-no-guest-environment',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))

    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --no-guest-environment
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testCanIPForward(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-can-ip-forward',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --can-ip-forward
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testDescription(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-description=a_desc',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --description=a_desc
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testLabels(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-labels=lk1=lv1,lk2=lv2',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --labels=lk1=lv1,lk2=lv2
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testMachineType(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=n2-standard-4',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --machine-type=n2-standard-4
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testCustomMachineNoExtendedMemory(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=custom-2-5120',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --custom-cpu=2 --custom-memory=5242880KB
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testCustomMachineExtendedMemory(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-machine-type=n1-custom-2-5120-ext',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --custom-vm-type n1 --custom-cpu=2 --custom-memory=5242880KB --custom-extensions
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testCustomMemoryWithoutCPU(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-memory: --custom-cpu must be specified.'):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-memory=5242880KB
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testCustomCPUWithoutMemory(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-cpu: --custom-memory must be specified.'):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-cpu=2
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testCustomExtensionWithoutCPUOrMemory(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --custom-extensions: --custom-cpu --custom-memory must be specified.'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --custom-extensions
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testMachineTypeAndCustomCPUMachineSet(self):
    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',),
        response=self.project,
    )
    self._ExpectServiceUsage()
    self._ExpectIamRolesGet(is_import=True)
    get_request = self.crm_v1_messages \
      .CloudresourcemanagerProjectsGetIamPolicyRequest(
          getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(
              options=self.crm_v1_messages.GetPolicyOptions(
                  requestedPolicyVersion=
                  iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)),
          resource='my-project')
    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        request=get_request,
        response=self.permissions,
    )

    with self.assertRaisesRegex(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--machine-type\]: Cannot set both '
        r'\[--machine-type\] and \[--custom-cpu\]/\[--custom-memory\]'
        r' for the same instance.'):
      self._RunFlags("""
                 {0} --source-uri {1} --os {2} --machine-type=n1-standard-2
                 --custom-cpu=2 --custom-memory=2048MB
                 """.format(self.machine_image_name, self.source_uri, self.os))

  def testNetwork(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-network=anetwork']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network=anetwork
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testNetworkAndSubnet(self):
    self.PrepareMocks(
        self.GetOVFNetworkStep(['-network=anetwork', '-subnet=asubnet']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network=anetwork --subnet=asubnet
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testSubnetWithoutNetwork(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-subnet=asubnet']))
    self._RunFlags("""
             {0} --source-uri {1} --os {2} --subnet=asubnet
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testNetworkTier(self):
    self.PrepareMocks(self.GetOVFNetworkStep(['-network-tier=PREMIUM']))
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --network-tier=PREMIUM
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testInvalidNetworkTier(self):
    with self.AssertRaisesExceptionRegexp(
        exceptions.InvalidArgumentException,
        r'Invalid value for \[--network-tier\]: Invalid network tier \[NOT_A_TIER\]'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2} --network-tier=NOT_A_TIER
               """.format(self.machine_image_name, self.source_uri, self.os))

  def testNoRestartOnFailure(self):
    self.PrepareMocks(
        self.GetOVFImportStepForArgs([
            '-machine-image-name={0}'.format(self.machine_image_name),
            '-client-id=gcloud',
            '-ovf-gcs-path={0}'.format(self.source_uri),
            '-no-restart-on-failure',
            '-os={0}'.format(self.os),
            '-timeout={0}'.format(_DEFAULT_TIMEOUT),
            '-release-track={0}'.format(self.track.id.lower()),
            '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
        ]))

    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2} --no-restart-on-failure
             """.format(self.machine_image_name, self.source_uri, self.os))

  def testTags(self):
    tags = 't1,t2,t3'
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format(self.source_uri),
        '-os={0}'.format(self.os),
        '-tags={0}'.format(tags),
        '-timeout=6984s',  # OVF import timeout 3% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --tags {3}
               """.format(self.machine_image_name, self.source_uri, self.os,
                          tags))

  def testSourceFileBucketOnlyGCSPath(self):
    self.doTestSourceFileBucketOnly('gs://31dd')

  def testSourceFileBucketOnlyWithTrailingSlashGCSPath(self):
    self.doTestSourceFileBucketOnly('gs://31dd/')

  def testSourceFileBucketOnlyHttpsGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'https://www.googleapis.com/storage/v1/b/31dd')

  def testSourceFileBucketOnlyWithTrailingSlashHttpsGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'https://www.googleapis.com/storage/v1/b/31dd/')

  def testSourceFileBucketOnlyHttpGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'http://www.googleapis.com/storage/v1/b/31dd')

  def testSourceFileBucketOnlyWithTrailingSlashHttpGcsPath(self):
    self.doTestSourceFileBucketOnly(
        'http://www.googleapis.com/storage/v1/b/31dd/')

  def doTestSourceFileBucketOnly(self, bucket_path):
    ovf_import_step = self.GetOVFImportStepForArgs([
        '-machine-image-name={0}'.format(self.machine_image_name),
        '-client-id=gcloud',
        '-ovf-gcs-path={0}'.format('gs://31dd/'),
        '-os={0}'.format(self.os),
        '-timeout=6984s',  # OVF import timeout 3% sooner than Argo.
        '-release-track={0}'.format(self.track.id.lower()),
        '-client-version={0}'.format(config.CLOUD_SDK_VERSION),
    ])
    self.PrepareMocks(ovf_import_step)
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             """.format(self.machine_image_name, bucket_path, self.os))

  def testSourceFileErrorOnInvalidGCSPath(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        r'Invalid value for [source-uri]: must be a path to an object or a directory in Cloud Storage'
    ):
      self._RunFlags("""
               {0} --source-uri {1} --os {2}
               """.format(self.machine_image_name, 'not-a-gcs-path', self.os))

  def testDockerImageTag(self):
    self.testCommonCase()

    self.ovf_builder = self.GetBuilder(tag='latest', region='my-region')
    self.PrepareMocks(self.GetOVFImportStep())
    self._RunAndAssertSuccess("""
             {0} --source-uri {1} --os {2}
             --docker-image-tag latest
             """.format(self.machine_image_name, self.source_uri, self.os))

  def _RunFlags(self, flags):
    self.Run('compute machine-images import {0}'.format(flags))

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

  def testLogLocationDir(self):
    self.doTestLogLocation('gs://foo/bar')
    self.doTestLogLocation('https://storage.googleapis.com/foo/bar')

  def testLogLocationDirTrailingSlash(self):
    self.doTestLogLocation('gs://foo/bar/')
    self.doTestLogLocation('https://storage.googleapis.com/foo/bar/')

  def testLogLocationBucketOnly(self):
    self.doTestLogLocation('gs://foo')
    self.doTestLogLocation('https://storage.googleapis.com/foo')

  def doTestLogLocation(self, log_location):
    self.PrepareMocks(self.GetOVFImportStep(), log_location=log_location)
    self._RunAndAssertSuccess("""
               {0} --source-uri {1} --os {2} --log-location {3}
               """.format(self.machine_image_name, self.source_uri, self.os,
                          log_location))


class MachineImageImportTestAlpha(MachineImageImportTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    super(MachineImageImportTestAlpha, self).SetUp()
    self.ovf_builder = ''

  def prepareArtifactRegistryMocks(self,
                                   expect_source_file_bucket_check=True,
                                   expected_builder_location='',
                                   regionalized=True):
    region = self.GetScratchBucketRegion().lower(
    ) if not expected_builder_location else expected_builder_location
    if expect_source_file_bucket_check:
      self.mocked_storage_v1.buckets.Get.Expect(
          self.storage_v1_messages.StorageBucketsGetRequest(bucket='31dd'),
          response=self.storage_v1_messages.Bucket(
              name='31dd', storageClass='REGIONAL', location=region),
      )
    if regionalized:
      location = 'projects/compute-image-tools/locations/{}'.format(region)
      repo_name = '{}/repositories/wrappers'.format(location)
      package_name = '{}/packages/gce_ovf_import'.format(repo_name)

      msgs = self.mocked_artifacts_v1beta2_messages
      self.mocked_artifacts_v1beta2.projects_locations.List.Expect(
          msgs.ArtifactregistryProjectsLocationsListRequest(
              name='projects/compute-image-tools'),
          response=msgs.ListLocationsResponse(
              locations=[msgs.Location(name=location, locationId=region)]))

      self.mocked_artifacts_v1beta2.projects_locations_repositories.Get.Expect(
          msgs.ArtifactregistryProjectsLocationsRepositoriesGetRequest(
              name=repo_name),
          response=msgs.Repository(
              name=repo_name,
              format=msgs.Repository.FormatValueValuesEnum.DOCKER))

      self.mocked_artifacts_v1beta2.projects_locations_repositories_packages.Get.Expect(
          msgs.ArtifactregistryProjectsLocationsRepositoriesPackagesGetRequest(
              name=package_name),
          response=msgs.Package(name=package_name))

  def GetBuilder(self,
                 zone='',
                 region='',
                 tag=daisy_utils._DEFAULT_BUILDER_VERSION):
    if self.ovf_builder:
      return self.ovf_builder
    builder_region = ''
    if zone:
      builder_region = daisy_utils.GetRegionFromZone(zone).lower()
    elif region:
      builder_region = region.lower()

    if builder_region:
      return daisy_utils._REGIONALIZED_BUILDER_DOCKER_PATTERN.format(
          executable=daisy_utils._OVF_IMPORT_BUILDER_EXECUTABLE,
          region=builder_region,
          docker_image_tag=tag)
    else:
      return daisy_utils._DEFAULT_BUILDER_DOCKER_PATTERN.format(
          executable=daisy_utils._OVF_IMPORT_BUILDER_EXECUTABLE,
          docker_image_tag=tag)


if __name__ == '__main__':
  test_case.main()
