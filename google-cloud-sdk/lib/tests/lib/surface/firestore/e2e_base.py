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
"""Base class for all Firestore Command e2e tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.core import properties
from tests.lib import e2e_base


class FirestoreE2ETestBase(e2e_base.WithServiceAuth):
  """Base class for Firestore surface E2E tests."""

  # Use a fixed bucket. This bucket lives in the Cloud Datastore test
  # application das-us-c-a. This bucket can be managed by anyone on the Cloud
  # Datastore team. It has a TTL of 1 day to delete resources. This is used
  # instead of temporary buckets to avoid export errors due to missing buckets,
  # which clutter the production logs.

  GSUTIL_BUCKET_PREFIX = 'gs://cloud-datastore-backups/'

  # We use a different project because datastore and firestore cannot both be
  # enabled for the same project.
  _GCLOUD_PROJECT_PROD = 'das-fs-us-c-gcloud'
  _GCLOUD_PROJECT_NIGHTLY = 'das-fs-us-c-gcloud-nightly'

  _VALID_PROJECTS = [_GCLOUD_PROJECT_NIGHTLY, _GCLOUD_PROJECT_PROD]

  def GetAnyField(self, any_field, path):
    """Gets a property from an any field.

    Args:
      any_field: The proto any field.
      path: A '.' separated path to the desired element.
    Returns:
      A JsonObject for the requested field, or None if not found.
    """

    def _Helper(props, path_elements):
      path_element = path_elements.pop(0)
      for prop in props:
        print('Looking at prop: %s for %s' % (prop.key, path_element),
              sys.stdout)
        if path_element == prop.key:
          return prop.value if not path_elements else _Helper(
              prop.value.object_value.properties, path_elements)
      return None

    return _Helper(any_field.additionalProperties, path.split('.'))

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    if super(e2e_base.WithServiceAccountFile,
             self).Project() not in self._VALID_PROJECTS:
      self.Run(['config', 'set', 'project', self._GCLOUD_PROJECT_PROD])

  def Project(self):
    super_project = super(e2e_base.WithServiceAccountFile, self).Project()
    if super_project not in self._VALID_PROJECTS:
      return self._GCLOUD_PROJECT_PROD
    else:
      return super_project

  def GetGcsBucket(self):
    """Gets the test GCS bucket."""
    return self.GSUTIL_BUCKET_PREFIX

  def RunFirestoreTest(self, command):
    """Helper to run command with appropriate flags set."""
    return self.Run('alpha firestore %s --format=disable' % command)
