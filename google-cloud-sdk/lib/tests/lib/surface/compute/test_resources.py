# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

alpha_messages = core_apis.GetMessagesModule('compute', 'alpha')
beta_messages = core_apis.GetMessagesModule('compute', 'beta')
messages = core_apis.GetMessagesModule('compute', 'v1')


def MakeOsloginClient(version, use_extended_profile=False):
  """Return a dummy oslogin API client."""
  oslogin_messages = core_apis.GetMessagesModule('oslogin', version)

  ssh_public_keys_value = oslogin_messages.LoginProfile.SshPublicKeysValue
  profile_basic = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[
          oslogin_messages.PosixAccount(
              primary=True,
              username='user_google_com',
              uid=123456,
              gid=123456,
              homeDirectory='/home/user_google_com',
              shell='/bin/bash')
      ],
      sshPublicKeys=ssh_public_keys_value(additionalProperties=[
          ssh_public_keys_value.AdditionalProperty(
              key='qwertyuiop',
              value=oslogin_messages.SshPublicKey(
                  fingerprint=b'asdfasdf',
                  key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))
      ]),
  )

  profile_extended = oslogin_messages.LoginProfile(
      name='user@google.com',
      posixAccounts=[
          oslogin_messages.PosixAccount(
              primary=False,
              username='user_google_com',
              uid=123456,
              gid=123456,
              homeDirectory='/home/user_google_com',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=False,
              username='testaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/testaccount',
              shell='/bin/bash'),
          oslogin_messages.PosixAccount(
              primary=True,
              username='myaccount',
              uid=123456,
              gid=123456,
              homeDirectory='/home/myaccount',
              shell='/bin/bash'),
      ],
      sshPublicKeys=ssh_public_keys_value(additionalProperties=[
          ssh_public_keys_value.AdditionalProperty(
              key='qwertyuiop',
              value=oslogin_messages.SshPublicKey(
                  fingerprint=b'asdfasdf',
                  key='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCks0aWrx'))
      ]),
  )

  if use_extended_profile:
    login_profile = profile_extended
  else:
    login_profile = profile_basic

  import_public_key_response = oslogin_messages.ImportSshPublicKeyResponse(
      loginProfile=login_profile)

  class _OsloginUsers(object):
    """Mock OS Login Users class."""

    @classmethod
    def ImportSshPublicKey(cls, message):
      del cls, message  # Unused
      return import_public_key_response

    @classmethod
    def GetLoginProfile(cls, message):
      del cls, message  # Unused
      return login_profile

  class _OsloginClient(object):
    users = _OsloginUsers
    MESSAGES_MODULE = oslogin_messages

  return _OsloginClient()


PROJECTS = [
    messages.Project(
        name='my-project',
        creationTimestamp='2013-09-06T17:54:10.636-07:00',
        commonInstanceMetadata=messages.Metadata(items=[
            messages.Metadata.ItemsValueListEntry(key='a', value='b'),
            messages.Metadata.ItemsValueListEntry(key='c', value='d'),
        ]),
        selfLink='https://compute.googleapis.com/compute/v1/projects/my-project/'
    )
]

REGIONS = [
    messages.Region(
        name='region-1',
        quotas=[
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=5120.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=30.0),
            messages.Quota(
                limit=7.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=1.0),
            messages.Quota(
                limit=24.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=2.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-1'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/regions/region-2'))),
    messages.Region(
        name='region-2',
        quotas=[
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            messages.Quota(
                limit=51200.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=300.0),
            messages.Quota(
                limit=70.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=10.0),
            messages.Quota(
                limit=240.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=20.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-2')),
    messages.Region(
        name='region-3',
        quotas=[
            messages.Quota(
                limit=4800.0,
                metric=messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            messages.Quota(
                limit=102400.0,
                metric=messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=600.0),
            messages.Quota(
                limit=140.0,
                metric=messages.Quota.MetricValueValuesEnum.STATIC_ADDRESSES,
                usage=20.0),
            messages.Quota(
                limit=480.0,
                metric=messages.Quota.MetricValueValuesEnum.IN_USE_ADDRESSES,
                usage=40.0),
        ],
        status=messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'regions/region-3')),
]

BETA_REGIONS = [
    beta_messages.Region(
        name='region-1',
        quotas=[
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=5120.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=30.0),
            beta_messages.Quota(
                limit=7.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=1.0),
            beta_messages.Quota(
                limit=24.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=2.0)
        ],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-1'),
        deprecated=beta_messages.DeprecationStatus(
            state=beta_messages.DeprecationStatus.StateValueValuesEnum
            .DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/beta/projects/'
                         'my-project/regions/region-2'))),
    beta_messages.Region(
        name='region-2',
        quotas=[
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=0.0),
            beta_messages.Quota(
                limit=51200.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=300.0),
            beta_messages.Quota(
                limit=70.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=10.0),
            beta_messages.Quota(
                limit=240.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=20.0)
        ],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-2')),
    beta_messages.Region(
        name='region-3',
        quotas=[
            beta_messages.Quota(
                limit=4800.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.CPUS,
                usage=2000.0),
            beta_messages.Quota(
                limit=102400.0,
                metric=beta_messages.Quota.MetricValueValuesEnum.DISKS_TOTAL_GB,
                usage=600.0),
            beta_messages.Quota(
                limit=140.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .STATIC_ADDRESSES,
                usage=20.0),
            beta_messages.Quota(
                limit=480.0,
                metric=beta_messages.Quota.MetricValueValuesEnum
                .IN_USE_ADDRESSES,
                usage=40.0)
        ],
        status=beta_messages.Region.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/region-3'))
]

ZONES = [
    messages.Zone(
        name='us-central1-a',
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        status=messages.Zone.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/us-central1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DEPRECATED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/zones/us-central1-b'))),
    messages.Zone(
        name='us-central1-b',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/us-central1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/us-central1-b')),
    messages.Zone(
        name='europe-west1-a',
        status=messages.Zone.StatusValueValuesEnum.UP,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/europe-west1-a')),
    messages.Zone(
        name='europe-west1-b',
        status=messages.Zone.StatusValueValuesEnum.DOWN,
        region=('https://compute.googleapis.com/compute/v1/projects/my-project/'
                'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/v1/projects/my-project/'
            'zones/europe-west1-a'),
        deprecated=messages.DeprecationStatus(
            state=messages.DeprecationStatus.StateValueValuesEnum.DELETED,
            deleted='2015-03-29T00:00:00.000-07:00',
            replacement=('https://compute.googleapis.com/compute/v1/projects/'
                         'my-project/zones/europe-west1-a'))),
]

BETA_ZONES = [
    beta_messages.Zone(
        name='us-central1-a',
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-a')),
    beta_messages.Zone(
        name='us-central1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/us-central1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/us-central1-b')),
    beta_messages.Zone(
        name='europe-west1-a',
        status=beta_messages.Zone.StatusValueValuesEnum.UP,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-a')),
    beta_messages.Zone(
        name='europe-west1-b',
        status=beta_messages.Zone.StatusValueValuesEnum.DOWN,
        region=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'regions/europe-west1'),
        selfLink=(
            'https://compute.googleapis.com/compute/beta/projects/my-project/'
            'zones/europe-west1-b')),
]
