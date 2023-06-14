"""Generated message classes for iam version v1beta.

Manages identity and access control for Google Cloud Platform resources,
including the creation of service accounts, which you can use to authenticate
to Google and make API calls.
"""
# NOTE: This file is autogenerated and should not be edited by hand.

from __future__ import absolute_import

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from apitools.base.py import extra_types


package = 'iam'


class GoogleIamAdminV1AuditData(_messages.Message):
  r"""Audit log information specific to Cloud IAM admin APIs. This message is
  serialized as an `Any` type in the `ServiceData` message of an `AuditLog`
  message.

  Fields:
    permissionDelta: The permission_delta when when creating or updating a
      Role.
  """

  permissionDelta = _messages.MessageField('GoogleIamAdminV1AuditDataPermissionDelta', 1)


class GoogleIamAdminV1AuditDataPermissionDelta(_messages.Message):
  r"""A PermissionDelta message to record the added_permissions and
  removed_permissions inside a role.

  Fields:
    addedPermissions: Added permissions.
    removedPermissions: Removed permissions.
  """

  addedPermissions = _messages.StringField(1, repeated=True)
  removedPermissions = _messages.StringField(2, repeated=True)


class GoogleIamV1BindingDelta(_messages.Message):
  r"""One delta entry for Binding. Each individual change (only one member in
  each entry) to a binding will be a separate entry.

  Enums:
    ActionValueValuesEnum: The action that was performed on a Binding.
      Required

  Fields:
    action: The action that was performed on a Binding. Required
    condition: The condition that is associated with this binding.
    member: A single identity requesting access for a Google Cloud resource.
      Follows the same format of Binding.members. Required
    role: Role that is assigned to `members`. For example, `roles/viewer`,
      `roles/editor`, or `roles/owner`. Required
  """

  class ActionValueValuesEnum(_messages.Enum):
    r"""The action that was performed on a Binding. Required

    Values:
      ACTION_UNSPECIFIED: Unspecified.
      ADD: Addition of a Binding.
      REMOVE: Removal of a Binding.
    """
    ACTION_UNSPECIFIED = 0
    ADD = 1
    REMOVE = 2

  action = _messages.EnumField('ActionValueValuesEnum', 1)
  condition = _messages.MessageField('GoogleTypeExpr', 2)
  member = _messages.StringField(3)
  role = _messages.StringField(4)


class GoogleIamV1LoggingAuditData(_messages.Message):
  r"""Audit log information specific to Cloud IAM. This message is serialized
  as an `Any` type in the `ServiceData` message of an `AuditLog` message.

  Fields:
    policyDelta: Policy delta between the original policy and the newly set
      policy.
  """

  policyDelta = _messages.MessageField('GoogleIamV1PolicyDelta', 1)


class GoogleIamV1PolicyDelta(_messages.Message):
  r"""The difference delta between two policies.

  Fields:
    bindingDeltas: The delta for Bindings between two policies.
  """

  bindingDeltas = _messages.MessageField('GoogleIamV1BindingDelta', 1, repeated=True)


class GoogleIamV1betaListWorkloadIdentityPoolProvidersResponse(_messages.Message):
  r"""Response message for ListWorkloadIdentityPoolProviders.

  Fields:
    nextPageToken: A token, which can be sent as `page_token` to retrieve the
      next page. If this field is omitted, there are no subsequent pages.
    workloadIdentityPoolProviders: A list of providers.
  """

  nextPageToken = _messages.StringField(1)
  workloadIdentityPoolProviders = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPoolProvider', 2, repeated=True)


class GoogleIamV1betaListWorkloadIdentityPoolsResponse(_messages.Message):
  r"""Response message for ListWorkloadIdentityPools.

  Fields:
    nextPageToken: A token, which can be sent as `page_token` to retrieve the
      next page. If this field is omitted, there are no subsequent pages.
    workloadIdentityPools: A list of pools.
  """

  nextPageToken = _messages.StringField(1)
  workloadIdentityPools = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPool', 2, repeated=True)


class GoogleIamV1betaUndeleteWorkloadIdentityPoolProviderRequest(_messages.Message):
  r"""Request message for UndeleteWorkloadIdentityPoolProvider."""


class GoogleIamV1betaUndeleteWorkloadIdentityPoolRequest(_messages.Message):
  r"""Request message for UndeleteWorkloadIdentityPool."""


class GoogleIamV1betaWorkloadIdentityPool(_messages.Message):
  r"""Represents a collection of external workload identities. You can define
  IAM policies to grant these identities access to Google Cloud resources.

  Enums:
    StateValueValuesEnum: Output only. The state of the pool.

  Fields:
    description: A description of the pool. Cannot exceed 256 characters.
    disabled: Whether the pool is disabled. You cannot use a disabled pool to
      exchange tokens, or use existing tokens to access resources. If the pool
      is re-enabled, existing tokens grant access again.
    displayName: A display name for the pool. Cannot exceed 32 characters.
    name: Output only. The resource name of the pool.
    state: Output only. The state of the pool.
  """

  class StateValueValuesEnum(_messages.Enum):
    r"""Output only. The state of the pool.

    Values:
      STATE_UNSPECIFIED: State unspecified.
      ACTIVE: The pool is active, and may be used in Google Cloud policies.
      DELETED: The pool is soft-deleted. Soft-deleted pools are permanently
        deleted after approximately 30 days. You can restore a soft-deleted
        pool using UndeleteWorkloadIdentityPool. You cannot reuse the ID of a
        soft-deleted pool until it is permanently deleted. While a pool is
        deleted, you cannot use it to exchange tokens, or use existing tokens
        to access resources. If the pool is undeleted, existing tokens grant
        access again.
    """
    STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DELETED = 2

  description = _messages.StringField(1)
  disabled = _messages.BooleanField(2)
  displayName = _messages.StringField(3)
  name = _messages.StringField(4)
  state = _messages.EnumField('StateValueValuesEnum', 5)


class GoogleIamV1betaWorkloadIdentityPoolOperationMetadata(_messages.Message):
  r"""Metadata for long-running WorkloadIdentityPool operations."""


class GoogleIamV1betaWorkloadIdentityPoolProvider(_messages.Message):
  r"""A configuration for an external identity provider.

  Enums:
    StateValueValuesEnum: Output only. The state of the provider.

  Messages:
    AttributeMappingValue: Maps attributes from authentication credentials
      issued by an external identity provider to Google Cloud attributes, such
      as `subject` and `segment`. Each key must be a string specifying the
      Google Cloud IAM attribute to map to. The following keys are supported:
      * `google.subject`: The principal IAM is authenticating. You can
      reference this value in IAM bindings. This is also the subject that
      appears in Cloud Logging logs. Cannot exceed 127 bytes. *
      `google.groups`: Groups the external identity belongs to. You can grant
      groups access to resources using an IAM `principalSet` binding; access
      applies to all members of the group. You can also provide custom
      attributes by specifying `attribute.{custom_attribute}`, where
      `{custom_attribute}` is the name of the custom attribute to be mapped.
      You can define a maximum of 50 custom attributes. The maximum length of
      a mapped attribute key is 100 characters, and the key may only contain
      the characters [a-z0-9_]. You can reference these attributes in IAM
      policies to define fine-grained access for a workload to Google Cloud
      resources. For example: * `google.subject`: `principal://iam.googleapis.
      com/projects/{project}/locations/{location}/workloadIdentityPools/{pool}
      /subject/{value}` * `google.groups`: `principalSet://iam.googleapis.com/
      projects/{project}/locations/{location}/workloadIdentityPools/{pool}/gro
      up/{value}` * `attribute.{custom_attribute}`: `principalSet://iam.google
      apis.com/projects/{project}/locations/{location}/workloadIdentityPools/{
      pool}/attribute.{custom_attribute}/{value}` Each value must be a [Common
      Expression Language] (https://opensource.google/projects/cel) function
      that maps an identity provider credential to the normalized attribute
      specified by the corresponding map key. You can use the `assertion`
      keyword in the expression to access a JSON representation of the
      authentication credential issued by the provider. The maximum length of
      an attribute mapping expression is 2048 characters. When evaluated, the
      total size of all mapped attributes must not exceed 8KB. For AWS
      providers, if no attribute mapping is defined, the following default
      mapping applies: ``` { "google.subject":"assertion.arn",
      "attribute.aws_role": "assertion.arn.contains('assumed-role')" " ?
      assertion.arn.extract('{account_arn}assumed-role/')" " + 'assumed-
      role/'" " + assertion.arn.extract('assumed-role/{role_name}/')" " :
      assertion.arn", } ``` If any custom attribute mappings are defined, they
      must include a mapping to the `google.subject` attribute. For OIDC
      providers, you must supply a custom mapping, which must include the
      `google.subject` attribute. For example, the following maps the `sub`
      claim of the incoming credential to the `subject` attribute on a Google
      token: ``` {"google.subject": "assertion.sub"} ```

  Fields:
    attributeCondition: [A Common Expression
      Language](https://opensource.google/projects/cel) expression, in plain
      text, to restrict what otherwise valid authentication credentials issued
      by the provider should not be accepted. The expression must output a
      boolean representing whether to allow the federation. The following
      keywords may be referenced in the expressions: * `assertion`: JSON
      representing the authentication credential issued by the provider. *
      `google`: The Google attributes mapped from the assertion in the
      `attribute_mappings`. * `attribute`: The custom attributes mapped from
      the assertion in the `attribute_mappings`. The maximum length of the
      condition expression is 4096 characters. If unspecified, all valid
      authentication credentials are accepted. The following example shows how
      to only allow credentials with a mapped `google.groups` value of
      `admins`: ``` "'admins' in google.groups" ```
    attributeMapping: Maps attributes from authentication credentials issued
      by an external identity provider to Google Cloud attributes, such as
      `subject` and `segment`. Each key must be a string specifying the Google
      Cloud IAM attribute to map to. The following keys are supported: *
      `google.subject`: The principal IAM is authenticating. You can reference
      this value in IAM bindings. This is also the subject that appears in
      Cloud Logging logs. Cannot exceed 127 bytes. * `google.groups`: Groups
      the external identity belongs to. You can grant groups access to
      resources using an IAM `principalSet` binding; access applies to all
      members of the group. You can also provide custom attributes by
      specifying `attribute.{custom_attribute}`, where `{custom_attribute}` is
      the name of the custom attribute to be mapped. You can define a maximum
      of 50 custom attributes. The maximum length of a mapped attribute key is
      100 characters, and the key may only contain the characters [a-z0-9_].
      You can reference these attributes in IAM policies to define fine-
      grained access for a workload to Google Cloud resources. For example: *
      `google.subject`: `principal://iam.googleapis.com/projects/{project}/loc
      ations/{location}/workloadIdentityPools/{pool}/subject/{value}` *
      `google.groups`: `principalSet://iam.googleapis.com/projects/{project}/l
      ocations/{location}/workloadIdentityPools/{pool}/group/{value}` *
      `attribute.{custom_attribute}`: `principalSet://iam.googleapis.com/proje
      cts/{project}/locations/{location}/workloadIdentityPools/{pool}/attribut
      e.{custom_attribute}/{value}` Each value must be a [Common Expression
      Language] (https://opensource.google/projects/cel) function that maps an
      identity provider credential to the normalized attribute specified by
      the corresponding map key. You can use the `assertion` keyword in the
      expression to access a JSON representation of the authentication
      credential issued by the provider. The maximum length of an attribute
      mapping expression is 2048 characters. When evaluated, the total size of
      all mapped attributes must not exceed 8KB. For AWS providers, if no
      attribute mapping is defined, the following default mapping applies: ```
      { "google.subject":"assertion.arn", "attribute.aws_role":
      "assertion.arn.contains('assumed-role')" " ?
      assertion.arn.extract('{account_arn}assumed-role/')" " + 'assumed-
      role/'" " + assertion.arn.extract('assumed-role/{role_name}/')" " :
      assertion.arn", } ``` If any custom attribute mappings are defined, they
      must include a mapping to the `google.subject` attribute. For OIDC
      providers, you must supply a custom mapping, which must include the
      `google.subject` attribute. For example, the following maps the `sub`
      claim of the incoming credential to the `subject` attribute on a Google
      token: ``` {"google.subject": "assertion.sub"} ```
    aws: An Amazon Web Services identity provider.
    description: A description for the provider. Cannot exceed 256 characters.
    disabled: Whether the provider is disabled. You cannot use a disabled
      provider to exchange tokens. However, existing tokens still grant
      access.
    displayName: A display name for the provider. Cannot exceed 32 characters.
    name: Output only. The resource name of the provider.
    oidc: An OpenId Connect 1.0 identity provider.
    state: Output only. The state of the provider.
  """

  class StateValueValuesEnum(_messages.Enum):
    r"""Output only. The state of the provider.

    Values:
      STATE_UNSPECIFIED: State unspecified.
      ACTIVE: The provider is active, and may be used to validate
        authentication credentials.
      DELETED: The provider is soft-deleted. Soft-deleted providers are
        permanently deleted after approximately 30 days. You can restore a
        soft-deleted provider using UndeleteWorkloadIdentityPoolProvider. You
        cannot reuse the ID of a soft-deleted provider until it is permanently
        deleted.
    """
    STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DELETED = 2

  @encoding.MapUnrecognizedFields('additionalProperties')
  class AttributeMappingValue(_messages.Message):
    r"""Maps attributes from authentication credentials issued by an external
    identity provider to Google Cloud attributes, such as `subject` and
    `segment`. Each key must be a string specifying the Google Cloud IAM
    attribute to map to. The following keys are supported: * `google.subject`:
    The principal IAM is authenticating. You can reference this value in IAM
    bindings. This is also the subject that appears in Cloud Logging logs.
    Cannot exceed 127 bytes. * `google.groups`: Groups the external identity
    belongs to. You can grant groups access to resources using an IAM
    `principalSet` binding; access applies to all members of the group. You
    can also provide custom attributes by specifying
    `attribute.{custom_attribute}`, where `{custom_attribute}` is the name of
    the custom attribute to be mapped. You can define a maximum of 50 custom
    attributes. The maximum length of a mapped attribute key is 100
    characters, and the key may only contain the characters [a-z0-9_]. You can
    reference these attributes in IAM policies to define fine-grained access
    for a workload to Google Cloud resources. For example: * `google.subject`:
    `principal://iam.googleapis.com/projects/{project}/locations/{location}/wo
    rkloadIdentityPools/{pool}/subject/{value}` * `google.groups`: `principalS
    et://iam.googleapis.com/projects/{project}/locations/{location}/workloadId
    entityPools/{pool}/group/{value}` * `attribute.{custom_attribute}`: `princ
    ipalSet://iam.googleapis.com/projects/{project}/locations/{location}/workl
    oadIdentityPools/{pool}/attribute.{custom_attribute}/{value}` Each value
    must be a [Common Expression Language]
    (https://opensource.google/projects/cel) function that maps an identity
    provider credential to the normalized attribute specified by the
    corresponding map key. You can use the `assertion` keyword in the
    expression to access a JSON representation of the authentication
    credential issued by the provider. The maximum length of an attribute
    mapping expression is 2048 characters. When evaluated, the total size of
    all mapped attributes must not exceed 8KB. For AWS providers, if no
    attribute mapping is defined, the following default mapping applies: ``` {
    "google.subject":"assertion.arn", "attribute.aws_role":
    "assertion.arn.contains('assumed-role')" " ?
    assertion.arn.extract('{account_arn}assumed-role/')" " + 'assumed-role/'"
    " + assertion.arn.extract('assumed-role/{role_name}/')" " :
    assertion.arn", } ``` If any custom attribute mappings are defined, they
    must include a mapping to the `google.subject` attribute. For OIDC
    providers, you must supply a custom mapping, which must include the
    `google.subject` attribute. For example, the following maps the `sub`
    claim of the incoming credential to the `subject` attribute on a Google
    token: ``` {"google.subject": "assertion.sub"} ```

    Messages:
      AdditionalProperty: An additional property for a AttributeMappingValue
        object.

    Fields:
      additionalProperties: Additional properties of type
        AttributeMappingValue
    """

    class AdditionalProperty(_messages.Message):
      r"""An additional property for a AttributeMappingValue object.

      Fields:
        key: Name of the additional property.
        value: A string attribute.
      """

      key = _messages.StringField(1)
      value = _messages.StringField(2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  attributeCondition = _messages.StringField(1)
  attributeMapping = _messages.MessageField('AttributeMappingValue', 2)
  aws = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPoolProviderAws', 3)
  description = _messages.StringField(4)
  disabled = _messages.BooleanField(5)
  displayName = _messages.StringField(6)
  name = _messages.StringField(7)
  oidc = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPoolProviderOidc', 8)
  state = _messages.EnumField('StateValueValuesEnum', 9)


class GoogleIamV1betaWorkloadIdentityPoolProviderAws(_messages.Message):
  r"""Represents an Amazon Web Services identity provider.

  Fields:
    accountId: Required. The AWS account ID.
  """

  accountId = _messages.StringField(1)


class GoogleIamV1betaWorkloadIdentityPoolProviderOidc(_messages.Message):
  r"""Represents an OpenId Connect 1.0 identity provider.

  Fields:
    allowedAudiences: Acceptable values for the `aud` field (audience) in the
      OIDC token. Token exchange requests are rejected if the token audience
      does not match one of the configured values. Each audience may be at
      most 256 characters. A maximum of 10 audiences may be configured. If
      this list is empty, the OIDC token audience must be equal to the full
      canonical resource name of the WorkloadIdentityPoolProvider, with or
      without the HTTPS prefix. For example: ``` //iam.googleapis.com/projects
      //locations//workloadIdentityPools//providers/ https://iam.googleapis.co
      m/projects//locations//workloadIdentityPools//providers/ ```
    issuerUri: Required. The OIDC issuer URL. Must be an HTTPS endpoint.
    jwksJson: Optional. OIDC JWKs in JSON String format. For details on
      definition of a JWK, see https://tools.ietf.org/html/rfc7517. If not
      set, then we use the `jwks_uri` from the discovery document fetched from
      the .well-known path for the `issuer_uri`. Currently, RSA and EC
      asymmetric keys are supported. The JWK must use following format and
      include only the following fields: { "keys": [ { "kty": "RSA/EC", "alg":
      "", "use": "sig", "kid": "", "n": "", "e": "", "x": "", "y": "", "crv":
      "" } ] }
  """

  allowedAudiences = _messages.StringField(1, repeated=True)
  issuerUri = _messages.StringField(2)
  jwksJson = _messages.StringField(3)


class GoogleLongrunningOperation(_messages.Message):
  r"""This resource represents a long-running operation that is the result of
  a network API call.

  Messages:
    MetadataValue: Service-specific metadata associated with the operation. It
      typically contains progress information and common metadata such as
      create time. Some services might not provide such metadata. Any method
      that returns a long-running operation should document the metadata type,
      if any.
    ResponseValue: The normal response of the operation in case of success. If
      the original method returns no data on success, such as `Delete`, the
      response is `google.protobuf.Empty`. If the original method is standard
      `Get`/`Create`/`Update`, the response should be the resource. For other
      methods, the response should have the type `XxxResponse`, where `Xxx` is
      the original method name. For example, if the original method name is
      `TakeSnapshot()`, the inferred response type is `TakeSnapshotResponse`.

  Fields:
    done: If the value is `false`, it means the operation is still in
      progress. If `true`, the operation is completed, and either `error` or
      `response` is available.
    error: The error result of the operation in case of failure or
      cancellation.
    metadata: Service-specific metadata associated with the operation. It
      typically contains progress information and common metadata such as
      create time. Some services might not provide such metadata. Any method
      that returns a long-running operation should document the metadata type,
      if any.
    name: The server-assigned name, which is only unique within the same
      service that originally returns it. If you use the default HTTP mapping,
      the `name` should be a resource name ending with
      `operations/{unique_id}`.
    response: The normal response of the operation in case of success. If the
      original method returns no data on success, such as `Delete`, the
      response is `google.protobuf.Empty`. If the original method is standard
      `Get`/`Create`/`Update`, the response should be the resource. For other
      methods, the response should have the type `XxxResponse`, where `Xxx` is
      the original method name. For example, if the original method name is
      `TakeSnapshot()`, the inferred response type is `TakeSnapshotResponse`.
  """

  @encoding.MapUnrecognizedFields('additionalProperties')
  class MetadataValue(_messages.Message):
    r"""Service-specific metadata associated with the operation. It typically
    contains progress information and common metadata such as create time.
    Some services might not provide such metadata. Any method that returns a
    long-running operation should document the metadata type, if any.

    Messages:
      AdditionalProperty: An additional property for a MetadataValue object.

    Fields:
      additionalProperties: Properties of the object. Contains field @type
        with type URL.
    """

    class AdditionalProperty(_messages.Message):
      r"""An additional property for a MetadataValue object.

      Fields:
        key: Name of the additional property.
        value: A extra_types.JsonValue attribute.
      """

      key = _messages.StringField(1)
      value = _messages.MessageField('extra_types.JsonValue', 2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  @encoding.MapUnrecognizedFields('additionalProperties')
  class ResponseValue(_messages.Message):
    r"""The normal response of the operation in case of success. If the
    original method returns no data on success, such as `Delete`, the response
    is `google.protobuf.Empty`. If the original method is standard
    `Get`/`Create`/`Update`, the response should be the resource. For other
    methods, the response should have the type `XxxResponse`, where `Xxx` is
    the original method name. For example, if the original method name is
    `TakeSnapshot()`, the inferred response type is `TakeSnapshotResponse`.

    Messages:
      AdditionalProperty: An additional property for a ResponseValue object.

    Fields:
      additionalProperties: Properties of the object. Contains field @type
        with type URL.
    """

    class AdditionalProperty(_messages.Message):
      r"""An additional property for a ResponseValue object.

      Fields:
        key: Name of the additional property.
        value: A extra_types.JsonValue attribute.
      """

      key = _messages.StringField(1)
      value = _messages.MessageField('extra_types.JsonValue', 2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  done = _messages.BooleanField(1)
  error = _messages.MessageField('GoogleRpcStatus', 2)
  metadata = _messages.MessageField('MetadataValue', 3)
  name = _messages.StringField(4)
  response = _messages.MessageField('ResponseValue', 5)


class GoogleRpcStatus(_messages.Message):
  r"""The `Status` type defines a logical error model that is suitable for
  different programming environments, including REST APIs and RPC APIs. It is
  used by [gRPC](https://github.com/grpc). Each `Status` message contains
  three pieces of data: error code, error message, and error details. You can
  find out more about this error model and how to work with it in the [API
  Design Guide](https://cloud.google.com/apis/design/errors).

  Messages:
    DetailsValueListEntry: A DetailsValueListEntry object.

  Fields:
    code: The status code, which should be an enum value of google.rpc.Code.
    details: A list of messages that carry the error details. There is a
      common set of message types for APIs to use.
    message: A developer-facing error message, which should be in English. Any
      user-facing error message should be localized and sent in the
      google.rpc.Status.details field, or localized by the client.
  """

  @encoding.MapUnrecognizedFields('additionalProperties')
  class DetailsValueListEntry(_messages.Message):
    r"""A DetailsValueListEntry object.

    Messages:
      AdditionalProperty: An additional property for a DetailsValueListEntry
        object.

    Fields:
      additionalProperties: Properties of the object. Contains field @type
        with type URL.
    """

    class AdditionalProperty(_messages.Message):
      r"""An additional property for a DetailsValueListEntry object.

      Fields:
        key: Name of the additional property.
        value: A extra_types.JsonValue attribute.
      """

      key = _messages.StringField(1)
      value = _messages.MessageField('extra_types.JsonValue', 2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  code = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  details = _messages.MessageField('DetailsValueListEntry', 2, repeated=True)
  message = _messages.StringField(3)


class GoogleTypeExpr(_messages.Message):
  r"""Represents a textual expression in the Common Expression Language (CEL)
  syntax. CEL is a C-like expression language. The syntax and semantics of CEL
  are documented at https://github.com/google/cel-spec. Example (Comparison):
  title: "Summary size limit" description: "Determines if a summary is less
  than 100 chars" expression: "document.summary.size() < 100" Example
  (Equality): title: "Requestor is owner" description: "Determines if
  requestor is the document owner" expression: "document.owner ==
  request.auth.claims.email" Example (Logic): title: "Public documents"
  description: "Determine whether the document should be publicly visible"
  expression: "document.type != 'private' && document.type != 'internal'"
  Example (Data Manipulation): title: "Notification string" description:
  "Create a notification string with a timestamp." expression: "'New message
  received at ' + string(document.create_time)" The exact variables and
  functions that may be referenced within an expression are determined by the
  service that evaluates it. See the service documentation for additional
  information.

  Fields:
    description: Optional. Description of the expression. This is a longer
      text which describes the expression, e.g. when hovered over it in a UI.
    expression: Textual representation of an expression in Common Expression
      Language syntax.
    location: Optional. String indicating the location of the expression for
      error reporting, e.g. a file name and a position in the file.
    title: Optional. Title for the expression, i.e. a short string describing
      its purpose. This can be used e.g. in UIs which allow to enter the
      expression.
  """

  description = _messages.StringField(1)
  expression = _messages.StringField(2)
  location = _messages.StringField(3)
  title = _messages.StringField(4)


class IamProjectsLocationsWorkloadIdentityPoolsCreateRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsCreateRequest object.

  Fields:
    googleIamV1betaWorkloadIdentityPool: A GoogleIamV1betaWorkloadIdentityPool
      resource to be passed as the request body.
    parent: Required. The parent resource to create the pool in. The only
      supported location is `global`.
    workloadIdentityPoolId: Required. The ID to use for the pool, which
      becomes the final component of the resource name. This value should be
      4-32 characters, and may contain the characters [a-z0-9-]. The prefix
      `gcp-` is reserved for use by Google, and may not be specified.
  """

  googleIamV1betaWorkloadIdentityPool = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPool', 1)
  parent = _messages.StringField(2, required=True)
  workloadIdentityPoolId = _messages.StringField(3)


class IamProjectsLocationsWorkloadIdentityPoolsDeleteRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsDeleteRequest object.

  Fields:
    name: Required. The name of the pool to delete.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsGetRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsGetRequest object.

  Fields:
    name: Required. The name of the pool to retrieve.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsListRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsListRequest object.

  Fields:
    pageSize: The maximum number of pools to return. If unspecified, at most
      50 pools are returned. The maximum value is 1000; values above are 1000
      truncated to 1000.
    pageToken: A page token, received from a previous
      `ListWorkloadIdentityPools` call. Provide this to retrieve the
      subsequent page.
    parent: Required. The parent resource to list pools for.
    showDeleted: Whether to return soft-deleted pools.
  """

  pageSize = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(2)
  parent = _messages.StringField(3, required=True)
  showDeleted = _messages.BooleanField(4)


class IamProjectsLocationsWorkloadIdentityPoolsOperationsGetRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsOperationsGetRequest object.

  Fields:
    name: The name of the operation resource.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsPatchRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsPatchRequest object.

  Fields:
    googleIamV1betaWorkloadIdentityPool: A GoogleIamV1betaWorkloadIdentityPool
      resource to be passed as the request body.
    name: Output only. The resource name of the pool.
    updateMask: Required. The list of fields to update.
  """

  googleIamV1betaWorkloadIdentityPool = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPool', 1)
  name = _messages.StringField(2, required=True)
  updateMask = _messages.StringField(3)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersCreateRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersCreateRequest
  object.

  Fields:
    googleIamV1betaWorkloadIdentityPoolProvider: A
      GoogleIamV1betaWorkloadIdentityPoolProvider resource to be passed as the
      request body.
    parent: Required. The pool to create this provider in.
    workloadIdentityPoolProviderId: Required. The ID for the provider, which
      becomes the final component of the resource name. This value must be
      4-32 characters, and may contain the characters [a-z0-9-]. The prefix
      `gcp-` is reserved for use by Google, and may not be specified.
  """

  googleIamV1betaWorkloadIdentityPoolProvider = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPoolProvider', 1)
  parent = _messages.StringField(2, required=True)
  workloadIdentityPoolProviderId = _messages.StringField(3)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersDeleteRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersDeleteRequest
  object.

  Fields:
    name: Required. The name of the provider to delete.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersGetRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersGetRequest object.

  Fields:
    name: Required. The name of the provider to retrieve.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersListRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersListRequest object.

  Fields:
    pageSize: The maximum number of providers to return. If unspecified, at
      most 50 providers are returned. The maximum value is 100; values above
      100 are truncated to 100.
    pageToken: A page token, received from a previous
      `ListWorkloadIdentityPoolProviders` call. Provide this to retrieve the
      subsequent page.
    parent: Required. The pool to list providers for.
    showDeleted: Whether to return soft-deleted providers.
  """

  pageSize = _messages.IntegerField(1, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(2)
  parent = _messages.StringField(3, required=True)
  showDeleted = _messages.BooleanField(4)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersOperationsGetRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersOperationsGetRequest
  object.

  Fields:
    name: The name of the operation resource.
  """

  name = _messages.StringField(1, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersPatchRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersPatchRequest object.

  Fields:
    googleIamV1betaWorkloadIdentityPoolProvider: A
      GoogleIamV1betaWorkloadIdentityPoolProvider resource to be passed as the
      request body.
    name: Output only. The resource name of the provider.
    updateMask: Required. The list of fields to update.
  """

  googleIamV1betaWorkloadIdentityPoolProvider = _messages.MessageField('GoogleIamV1betaWorkloadIdentityPoolProvider', 1)
  name = _messages.StringField(2, required=True)
  updateMask = _messages.StringField(3)


class IamProjectsLocationsWorkloadIdentityPoolsProvidersUndeleteRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsProvidersUndeleteRequest
  object.

  Fields:
    googleIamV1betaUndeleteWorkloadIdentityPoolProviderRequest: A
      GoogleIamV1betaUndeleteWorkloadIdentityPoolProviderRequest resource to
      be passed as the request body.
    name: Required. The name of the provider to undelete.
  """

  googleIamV1betaUndeleteWorkloadIdentityPoolProviderRequest = _messages.MessageField('GoogleIamV1betaUndeleteWorkloadIdentityPoolProviderRequest', 1)
  name = _messages.StringField(2, required=True)


class IamProjectsLocationsWorkloadIdentityPoolsUndeleteRequest(_messages.Message):
  r"""A IamProjectsLocationsWorkloadIdentityPoolsUndeleteRequest object.

  Fields:
    googleIamV1betaUndeleteWorkloadIdentityPoolRequest: A
      GoogleIamV1betaUndeleteWorkloadIdentityPoolRequest resource to be passed
      as the request body.
    name: Required. The name of the pool to undelete.
  """

  googleIamV1betaUndeleteWorkloadIdentityPoolRequest = _messages.MessageField('GoogleIamV1betaUndeleteWorkloadIdentityPoolRequest', 1)
  name = _messages.StringField(2, required=True)


class StandardQueryParameters(_messages.Message):
  r"""Query parameters accepted by all methods.

  Enums:
    FXgafvValueValuesEnum: V1 error format.
    AltValueValuesEnum: Data format for response.

  Fields:
    f__xgafv: V1 error format.
    access_token: OAuth access token.
    alt: Data format for response.
    callback: JSONP
    fields: Selector specifying which fields to include in a partial response.
    key: API key. Your API key identifies your project and provides you with
      API access, quota, and reports. Required unless you provide an OAuth 2.0
      token.
    oauth_token: OAuth 2.0 token for the current user.
    prettyPrint: Returns response with indentations and line breaks.
    quotaUser: Available to use for quota purposes for server-side
      applications. Can be any arbitrary string assigned to a user, but should
      not exceed 40 characters.
    trace: A tracing token of the form "token:<tokenid>" to include in api
      requests.
    uploadType: Legacy upload protocol for media (e.g. "media", "multipart").
    upload_protocol: Upload protocol for media (e.g. "raw", "multipart").
  """

  class AltValueValuesEnum(_messages.Enum):
    r"""Data format for response.

    Values:
      json: Responses with Content-Type of application/json
      media: Media download with context-dependent Content-Type
      proto: Responses with Content-Type of application/x-protobuf
    """
    json = 0
    media = 1
    proto = 2

  class FXgafvValueValuesEnum(_messages.Enum):
    r"""V1 error format.

    Values:
      _1: v1 error format
      _2: v2 error format
    """
    _1 = 0
    _2 = 1

  f__xgafv = _messages.EnumField('FXgafvValueValuesEnum', 1)
  access_token = _messages.StringField(2)
  alt = _messages.EnumField('AltValueValuesEnum', 3, default='json')
  callback = _messages.StringField(4)
  fields = _messages.StringField(5)
  key = _messages.StringField(6)
  oauth_token = _messages.StringField(7)
  prettyPrint = _messages.BooleanField(8, default=True)
  quotaUser = _messages.StringField(9)
  trace = _messages.StringField(10)
  uploadType = _messages.StringField(11)
  upload_protocol = _messages.StringField(12)


encoding.AddCustomJsonFieldMapping(
    StandardQueryParameters, 'f__xgafv', '$.xgafv')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_1', '1')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_2', '2')
