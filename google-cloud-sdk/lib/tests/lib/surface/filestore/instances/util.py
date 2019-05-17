# -*- coding: utf-8 -*- #
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
"""Testing resources for Cloud Filestore Instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client


def GetTestCloudFilestoreInstancesList():
  messages = filestore_client.GetMessages(filestore_client.ALPHA_API_VERSION)
  return [
      messages.Instance(name='Instance1'),
      messages.Instance(name='Instance2'),
  ]


def GetTestCloudFilestoreInstance():
  messages = filestore_client.GetMessages(filestore_client.ALPHA_API_VERSION)
  return messages.Instance(name='My Cloud Filestore Instance')
