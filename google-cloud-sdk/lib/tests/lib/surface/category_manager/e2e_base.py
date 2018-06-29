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
"""Category Manager E2e test base."""

from __future__ import absolute_import
from __future__ import unicode_literals
import contextlib
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import e2e_utils


class CategoryManagerE2eBase(e2e_base.WithServiceAuth):
  """Base class for category manager e2e tests."""

  # Unique resource prefix used to tag all category manager resources so they
  # can easily be cleaned up by hourly Kokoro job.
  _RESOURCE_PREFIX = 'category-manager'

  # Length of the hash suffix appended to the randomly generated resource names.
  _HASH_LEN = 32

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  @contextlib.contextmanager
  def CreateAnnotationResource(self, taxonomy, description):
    """Create an annotation resource that is automatically cleaned up."""
    annotation_display_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix=self._RESOURCE_PREFIX, hash_len=self._HASH_LEN))
    try:
      args = '--taxonomy "{}" --display-name "{}" --description "{}"'.format(
          taxonomy.name, annotation_display_name, description)
      annotation = self.Run('category-manager taxonomies annotations create ' +
                            args)
      yield annotation
    finally:
      annotation = self._ListAnnotationsAndReturnMatch(taxonomy,
                                                       annotation_display_name)
      if annotation is not None:
        self.Run('category-manager taxonomies annotations delete --quiet ' +
                 annotation.name)

  @contextlib.contextmanager
  def CreateTaxonomyResource(self, description):
    """Create a taxonomy resource that is automatically cleaned up."""
    taxonomy_display_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix=self._RESOURCE_PREFIX, hash_len=self._HASH_LEN))
    try:
      args = '--display-name "{}" --description "{}"'.format(
          taxonomy_display_name, description)
      taxonomy = self.Run('category-manager taxonomies create ' + args)
      yield taxonomy
    finally:
      taxonomy = self._ListTaxonomiesAndReturnMatch(taxonomy_display_name)
      if taxonomy is not None:
        self.Run('category-manager taxonomies delete --quiet ' + taxonomy.name)

  def _ListTaxonomiesAndReturnMatch(self, display_name):
    """Finds a created taxonomy with a display name using the list command."""
    taxonomies = self.Run('category-manager taxonomies list --format=disable')
    for taxonomy in taxonomies:
      if taxonomy.displayName == display_name:
        return taxonomy

  def _ListAnnotationsAndReturnMatch(self, taxonomy, display_name):
    """Finds a created annotation with a display name using the list command."""
    args = '--taxonomy {} --format=disable'.format(taxonomy.name)
    annotations = self.Run('category-manager taxonomies annotations list ' +
                           args)
    for annotation in annotations:
      if annotation.displayName == display_name:
        return annotation

  def _ListAssetAnnotationTagsAndReturnMatch(self, asset, display_name):
    """Finds an annotation tagged to an asset with a given display name."""
    args = '{} --format=disable'.format(asset)
    annotation_tags = self.Run('category-manager assets list-annotations ' +
                               args)
    for annotation_tag in annotation_tags.tags:
      if annotation_tag.annotationDisplayName == display_name:
        return annotation_tag
