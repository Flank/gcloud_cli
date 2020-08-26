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
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages as _messages


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
  """A SecretmanagerProjectsSecretsSetIamPolicyRequest object.

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
  r"""A SecretmanagerProjectsSecretsGetRequest object.

  Fields:
    name: Required. The resource name of the Secret, in the format
      `projects/*/secrets/*`.
  """

  name = _messages.StringField(1, required=True)


class FakeapiProjectsIcecreamsListRequest(_messages.Message):
  r"""A FakeapiProjectsIcecreamsListRequest object.

  Fields:
    pageSize: Optional. The maximum number of results to be returned in a
      single page. If set to 0, the server decides the number of results to
      return. If the number is greater than 25000, it is capped at 25000.
    pageToken: Optional. Pagination token, returned earlier via
      ListSecretsResponse.next_page_token.
    parent: Required. The resource name of the project associated with the
      Secrets, in the format `projects/*`.
  """

  pageSize = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(2)
  parent = _messages.StringField(3, required=True)


class FakeapiProjectsIcecreamsCreateRequest(_messages.Message):
  r"""A SecretmanagerProjectsSecretsCreateRequest object.

  Fields:
    parent: Required. The resource name of the project to associate with the
      Secret, in the format `projects/*`.
    secret: A Secret resource to be passed as the request body.
    secretId: Required. This must be unique within the project.  A secret ID
      is a string with a maximum length of 255 characters and can contain
      uppercase and lowercase letters, numerals, and the hyphen (`-`) and
      underscore (`_`) characters.
  """

  parent = _messages.StringField(1, required=True)
  secret = _messages.MessageField('Secret', 2)
  secretId = _messages.StringField(3)


class FakeapiProjectsIcecreamsDeleteRequest(_messages.Message):
  r"""A SecretmanagerProjectsSecretsDeleteRequest object.

  Fields:
    name: Required. The resource name of the Secret to delete in the format
      `projects/*/secrets/*`.
  """

  name = _messages.StringField(1, required=True)


class SecretmanagerProjectsSecretsGetRequest(_messages.Message):
  r"""A SecretmanagerProjectsSecretsGetRequest object.

  Fields:
    name: Required. The resource name of the Secret, in the format
      `projects/*/secrets/*`.
  """

  name = _messages.StringField(1, required=True)

# pylint: enable=invalid-name
