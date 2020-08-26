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
"""Generated message classes for fakeapi version v1.

"""

from __future__ import absolute_import

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding


package = 'fakeapi'

# pylint: disable=invalid-name (auto-generated message format has invalid names)


class FakeapiProjectsIcecreamsGetIamPolicyRequest(_messages.Message):
  r"""A FakeapiProjectsIcecreamsGetIamPolicyRequest object.

  Fields:
    options_requestedPolicyVersion: Optional. The policy format version to be
      returned.  Valid values are 0, 1, and 3. Requests specifying an invalid
      value will be rejected.  Requests for policies with any conditional
      bindings must specify version 3. Policies without any conditional
      bindings may specify any valid value or leave the field unset.  To learn
      which resources support conditions in their IAM policies, see the [IAM
      documentation](https://cloud.google.com/iam/help/conditions/resource-
      policies).
    resource: REQUIRED: The resource for which the policy is being requested.
      See the operation documentation for the appropriate value for this
      field.
  """

  options_requestedPolicyVersion = _messages.IntegerField(
      1, variant=_messages.Variant.INT32)
  resource = _messages.StringField(2, required=True)


class FakeapiProjectsIcecreamsSetIamPolicyRequest(_messages.Message):
  """A IcecreammanagerProjectsIcecreamsSetIamPolicyRequest object.

  Fields:
    resource: REQUIRED: The resource for which the policy is being specified.
      See the operation documentation for the appropriate value for this
      field.
    setIamPolicyRequest: A SetIamPolicyRequest resource to be passed as the
      request body.
  """

  resource = _messages.StringField(1, required=True)
  setIamPolicyRequest = _messages.MessageField('SetIamPolicyRequest', 2)


class FakeapiProjectsIcecreamsGetRequest(_messages.Message):
  r"""A IcecreammanagerProjectsIcecreamsGetRequest object.

  Fields:
    name: Required. The resource name of the Icecream, in the format
      `projects/*/icecreams/*`.
  """

  name = _messages.StringField(1, required=True)


class FakeapiProjectsIcecreamsListRequest(_messages.Message):
  r"""A FakeapiProjectsIcecreamsListRequest object.

  Fields:
    pageSize: Optional. The maximum number of results to be returned in a
      single page. If set to 0, the server decides the number of results to
      return. If the number is greater than 25000, it is capped at 25000.
    pageToken: Optional. Pagination token, returned earlier via
      ListIcecreamsResponse.next_page_token.
    parent: Required. The resource name of the project associated with the
      Icecreams, in the format `projects/*`.
  """

  pageSize = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(2)
  parent = _messages.StringField(3, required=True)


class FakeapiProjectsIcecreamsCreateRequest(_messages.Message):
  r"""A IcecreammanagerProjectsIcecreamsCreateRequest object.

  Fields:
    parent: Required. The resource name of the project to associate with the
      Icecream, in the format `projects/*`.
    icecream: A Icecream resource to be passed as the request body.
    icecreamId: Required. This must be unique within the project.  A icecream ID
      is a string with a maximum length of 255 characters and can contain
      uppercase and lowercase letters, numerals, and the hyphen (`-`) and
      underscore (`_`) characters.
  """

  parent = _messages.StringField(1, required=True)
  icecream = _messages.MessageField('Icecream', 2)
  icecreamId = _messages.StringField(3)


class FakeapiProjectsIcecreamsDeleteRequest(_messages.Message):
  r"""A IcecreammanagerProjectsIcecreamsDeleteRequest object.

  Fields:
    name: Required. The resource name of the Icecream to delete in the format
      `projects/*/icecreams/*`.
  """

  name = _messages.StringField(1, required=True)


class IcecreammanagerProjectsIcecreamsGetRequest(_messages.Message):
  r"""A IcecreammanagerProjectsIcecreamsGetRequest object.

  Fields:
    name: Required. The resource name of the Icecream, in the format
      `projects/*/icecreams/*`.
  """

  name = _messages.StringField(1, required=True)


class Icecream(_messages.Message):
  r"""A Icecream is a logical Icecream whose value and versions can be accessed.

  A Icecream is made up of zero or more IcecreamVersions that represent the
  Icecream data.

  Messages:
    LabelsValue: The labels assigned to this Icecream.  Label keys must be
      between 1 and 63 characters long, have a UTF-8 encoding of maximum 128
      bytes, and must conform to the following PCRE regular expression:
      `\p{Ll}\p{Lo}{0,62}`  Label values must be between 0 and 63 characters
      long, have a UTF-8 encoding of maximum 128 bytes, and must conform to
      the following PCRE regular expression: `[\p{Ll}\p{Lo}\p{N}_-]{0,63}`  No
      more than 64 labels can be assigned to a given resource.

  Fields:
    createTime: Output only. The time at which the Icecream was created.
    labels: The labels assigned to this Icecream.  Label keys must be between 1
      and 63 characters long, have a UTF-8 encoding of maximum 128 bytes, and
      must conform to the following PCRE regular expression:
      `\p{Ll}\p{Lo}{0,62}`  Label values must be between 0 and 63 characters
      long, have a UTF-8 encoding of maximum 128 bytes, and must conform to
      the following PCRE regular expression: `[\p{Ll}\p{Lo}\p{N}_-]{0,63}`  No
      more than 64 labels can be assigned to a given resource.
    name: Output only. The resource name of the Icecream in the format
      `projects/*/icecreams/*`.
    replication: Required. Immutable. The replication policy of the icecream
      data attached to the Icecream.  The replication policy cannot be changed
      after the Icecream has been created.
  """

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    r"""The labels assigned to this Icecream.

    Label keys must be between 1 and 63 characters long, have a UTF-8 encoding
    of maximum 128 bytes, and must conform to the following PCRE
    regular expression: `\p{Ll}\p{Lo}{0,62}` Label values must be
    between 0 and 63 characters long, have a UTF-8
    encoding of maximum 128 bytes, and must conform to the following PCRE
    regular expression: `[\p{Ll}\p{Lo}\p{N}_-]{0,63}`  No more than 64 labels
    can be assigned to a given resource.

    Messages:
      AdditionalProperty: An additional property for a LabelsValue object.

    Fields:
      additionalProperties: Additional properties of type LabelsValue
    """

    class AdditionalProperty(_messages.Message):
      r"""An additional property for a LabelsValue object.

      Fields:
        key: Name of the additional property.
        value: A string attribute.
      """

      key = _messages.StringField(1)
      value = _messages.StringField(2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  createTime = _messages.StringField(1)
  labels = _messages.MessageField('LabelsValue', 2)
  name = _messages.StringField(3)
  replication = _messages.MessageField('Replication', 4)
# pylint: enable=invalid-name
