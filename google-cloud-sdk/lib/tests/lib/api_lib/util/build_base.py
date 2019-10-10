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
"""Base class for Cloud Builder tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class BuildBase(sdk_test_base.WithFakeAuth,
                cli_test_base.CliTestBase):
  """Base class for all Cloud Builder tests."""

  def SetUp(self):
    self.messages = core_apis.GetMessagesModule('cloudbuild', 'v1')
    build_meta = self.messages.Operation.MetadataValue.AdditionalProperty(
        key='build',
        value=extra_types.JsonValue(
            object_value=extra_types.JsonObject(
                properties=[
                    extra_types.JsonObject.Property(
                        key='id',
                        value=extra_types.JsonValue(string_value='build-id'),),
                    extra_types.JsonObject.Property(
                        key='source',
                        value=extra_types.JsonValue(
                            object_value=extra_types.
                            JsonObject(properties=[
                                extra_types.JsonObject.Property(
                                    key='storageSource',
                                    value=extra_types.JsonValue(
                                        object_value=extra_types.
                                        JsonObject(properties=[
                                            extra_types.JsonObject.Property(
                                                key='object',
                                                value=extra_types.JsonValue(
                                                    string_value='image-name'))
                                        ])))
                            ]))),
                ],),),)
    build_op = self.messages.Operation(
        metadata=self.messages.Operation.MetadataValue(
            additionalProperties=[
                build_meta,
            ],),
        name='fake-buildop')
    self.build_op = build_op
