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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import logging
import re

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core.util import retry
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import e2e_test_base

_UPLOAD_TIMEOUT = 300
_WINDOWS_IMAGE_ALIAS = 'windows-2012-r2'
_SERVICE_ACCOUNT = ('462803083913-lak0k1ette3muh3o3kb3pp2im3urj3e9@'
                    'developer.gserviceaccount.com')
_START_SCRIPT = (
    r'& C:\ProgramData\GooGet\googet.exe addrepo unstable '
    'https://packages.cloud.google.com/yuck/repos/google-compute-'
    'engine-windows-unstable;'
    r'& C:\ProgramData\GooGet\googet.exe addrepo '
    'diagnostics https://packages.cloud.google.com/yuck/repos/'
    'google-compute-engine-diagnostics-unstable;'
    r'& C:\ProgramData\GooGet\googet.exe -noconfirm update;'
    r'& C:\ProgramData\GooGet\googet.exe -noconfirm '
    'install google-compute-engine-diagnostics')
_GS_UTIL_REGEX = r'gs://.*?/.*?\.zip'
_PROJECT_NAME = r'cloud-sdk-integration-testing'


@sdk_test_base.Filters.RunOnlyOnWindows
class WindowsDiagnostcisTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.instance_names_used = []
    self.bucket_ref = None

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    for name in self.instance_names_used:
      self.CleanUpResource(name, 'instances')
    if self.bucket_ref:
      storage_api.StorageClient().DeleteBucket(self.bucket_ref)

  def GetInstanceName(self):
    # Make sure the name used is different on each retry, and make sure all
    # names used are cleaned up.
    self.instance_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-windows'))
    self.instance_names_used.append(self.instance_name)

  @test_case.Filters.skip('Failing', 'b/138801142')
  def testInstances(self):
    self.GetInstanceName()
    self._CreateInstance()
    self._ResetWindowsPassword()
    self._DownloadDiagnosticsTool()

  def _ResetWindowsPassword(self):
    user = 'test-user'
    message = 'Instance setup finished.'
    booted = self.WaitForBoot(self.instance_name, message, retries=10,
                              polling_interval=60)
    self.assertTrue(booted, msg='GCE Agent not started before timeout')
    self.Run('compute reset-windows-password {0} --zone {1} --user {2} '
             '--format json'.format(self.instance_name, self.zone, user))

  def _CreateInstance(self):
    self.Run('compute instances create {0} --zone {1} --image {2} '
             '--metadata windows-startup-script-ps1=\"{3}\"'
             .format(self.instance_name, self.zone,
                     _WINDOWS_IMAGE_ALIAS, _START_SCRIPT))
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances list')
    self.AssertNewOutputContains(self.instance_name)
    self.Run('compute instances describe {0} --zone {1} --format json'
             .format(self.instance_name, self.zone))
    self.Run('compute instances add-metadata {0} '
             '--metadata enable-diagnostics=true'
             ' --zone {1}'.format(self.instance_name, self.zone))

    instance_json = self.GetNewOutput()
    instance_dict = json.loads(instance_json)
    self.assertEqual(instance_dict['name'], self.instance_name)

  def _ReadDiagnosticsFileUpload(self, object_ref):
    """Try read an object for a given gcs path.

    Args:
      object_ref: An object reference to the file to read.
    """
    storage_api.StorageClient().ReadObject(object_ref)

  def _DownloadDiagnosticsTool(self):
    self.Run('projects add-iam-policy-binding {0} '
             '--member serviceAccount:{1} --role roles'
             '/iam.serviceAccountTokenCreator'.format(
                 _PROJECT_NAME,
                 _SERVICE_ACCOUNT))
    self.Run('alpha compute diagnose export-logs {0} '
             '--zone {1}'.format(self.instance_name, self.zone))

    connection_info = self.GetNewOutput()
    match_group = re.findall(_GS_UTIL_REGEX, connection_info)
    self.assertTrue(len(match_group))
    gsutil_url = match_group[0]
    self.bucket_ref = storage_util.ObjectReference.FromUrl(
        gsutil_url).bucket_ref

    object_ref = storage_util.ObjectReference.FromUrl(gsutil_url)
    # keep trying to read the object until it does not throw exception.
    retry.Retryer().RetryOnException(
        self._ReadDiagnosticsFileUpload,
        args=[object_ref], sleep_ms=[5000 for _ in range(_UPLOAD_TIMEOUT//5)])
    storage_api.StorageClient().DeleteObject(object_ref)

if __name__ == '__main__':
  e2e_test_base.main()
