# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Common utility functions for getting the alloydb API client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

# API version constants
API_VERSION_DEFAULT = 'v1alpha1'
VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha1',
    base.ReleaseTrack.BETA: 'v1beta'
}


class AlloyDBClient(object):
  """Wrapper for alloydb API client and associated resources."""

  def __init__(self, release_track):
    api_version = VERSION_MAP[release_track]
    self.release_track = release_track
    self.alloydb_client = apis.GetClientInstance('alloydb', api_version)
    self.alloydb_messages = self.alloydb_client.MESSAGES_MODULE
    self.resource_parser = resources.Registry()
    self.resource_parser.RegisterApiByName('alloydb', api_version)
