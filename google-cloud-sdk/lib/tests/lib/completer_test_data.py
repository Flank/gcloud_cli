# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Shared completer test data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def FolderUri(folder_id):
  return ('https://cloudresourcemanager.googleapis.com/v2beta1/'
          'folders/{folder_id}').format(
              folder_id=folder_id)


def OrganizationUri(organization_id):
  return ('https://cloudresourcemanager.googleapis.com/v1/'
          'organizations/{organization_id}').format(
              organization_id=organization_id)


def ProjectUri(project):
  return ('https://cloudresourcemanager.googleapis.com/v1/'
          'projects/{project}').format(
              project=project)


PROJECT_NAMES = [
    'my-project',
    'my_x_project',
    'their_y_project',
    'your_z_project',
]

PROJECT_URIS = [ProjectUri(p) for p in PROJECT_NAMES]


def RegionUri(project, region):
  return ('https://www.googleapis.com/compute/v1/'
          'projects/{project}/regions/{region}').format(
              project=project, region=region)


REGION_NAMES = [
    'asia-east1',
    'asia-northeast1',
    'europe-west1',
    'us-central1',
    'us-central2',
    'us-east1',
    'us-west1',
]

REGION_URIS = [RegionUri(PROJECT_NAMES[0], r) for r in REGION_NAMES]


def ZoneUri(project, zone):
  return ('https://www.googleapis.com/compute/v1/'
          'projects/{project}/zones/{zone}').format(
              project=project, zone=zone)


ZONE_NAMES = [
    'asia-east1-a',
    'asia-east1-b',
    'asia-east1-c',
    'asia-northeast1-a',
    'asia-northeast1-b',
    'asia-northeast1-c',
    'europe-west1-b',
    'europe-west1-c',
    'europe-west1-d',
    'us-central1-a',
    'us-central1-b',
    'us-central1-c',
    'us-central1-f',
    'us-central2-a',
    'us-east1-b',
    'us-east1-c',
    'us-east1-d',
    'us-west1-a',
    'us-west1-b',
]

ZONE_URIS = [ZoneUri(PROJECT_NAMES[0], z) for z in ZONE_NAMES]


def _Instance(project, zone, instance):
  return ('https://www.googleapis.com/compute/v1/'
          'projects/{project}/zones/{zone}/instances/{instance}').format(
              project=project, zone=zone, instance=instance)


INSTANCE_NAMES = [
    'my_a_instance',
    'my_b_instance',
    'my_c_instance',
]

INSTANCE_URIS = [
    _Instance(p, z, i)
    for p in PROJECT_NAMES
    for z in ZONE_NAMES
    for i in INSTANCE_NAMES
]


class _IamGrantableRole(object):

  def __init__(self, name, title, description):
    self.name = name
    self.title = title
    self.description = description


IAM_GRANTABLE_ROLES = [
    _IamGrantableRole(
        'roles/compute.admin',
        'Compute Admin (alpha)',
        'Full control of all Compute Engine resources.',
    ),
    _IamGrantableRole(
        'roles/compute.instanceAdmin',
        'Compute Instance Admin (beta)',
        'Full control of Compute Engine instance resources.',
    ),
    _IamGrantableRole(
        'roles/compute.instanceAdmin.v1',
        'Compute Instance Admin (v1)',
        'Full control of Compute Engine instances, instance groups, disks, '
        'snapshots, and images. Read access to all Compute Engine networking '
        'resources.',
    ),
    _IamGrantableRole(
        'roles/compute.networkAdmin',
        'Compute Network Admin',
        'Full control of Compute Engine networking resources.',
    ),
    _IamGrantableRole(
        'roles/compute.networkViewer',
        'Compute Network Viewer',
        'Read-only access to Compute Engine networking resources.',
    ),
    _IamGrantableRole(
        'roles/compute.securityAdmin',
        'Compute Security Admin',
        'Full control of Compute Engine security resources.',
    ),
    _IamGrantableRole(
        'roles/editor',
        'Editor',
        'Edit access to all resources.',
    ),
    _IamGrantableRole(
        'roles/iam.securityReviewer',
        'Security Reviewer',
        'Security reviewer role, with permissions to get any IAM policy.',
    ),
    _IamGrantableRole(
        'roles/owner',
        'Owner',
        'Full access to all resources.',
    ),
    _IamGrantableRole(
        'roles/viewer',
        'Viewer',
        'Read access to all resources.',
    )
]
