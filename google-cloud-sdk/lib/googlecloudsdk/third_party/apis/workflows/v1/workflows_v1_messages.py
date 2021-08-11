"""Generated message classes for workflows version v1.

Manage workflow definitions. To execute workflows and manage executions, see
the Workflows Executions API.
"""
# NOTE: This file is autogenerated and should not be edited by hand.

from __future__ import absolute_import

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from apitools.base.py import extra_types


package = 'workflows'


class Empty(_messages.Message):
  r"""A generic empty message that you can re-use to avoid defining duplicated
  empty messages in your APIs. A typical example is to use it as the request
  or the response type of an API method. For instance: service Foo { rpc
  Bar(google.protobuf.Empty) returns (google.protobuf.Empty); } The JSON
  representation for `Empty` is empty JSON object `{}`.
  """



class ListLocationsResponse(_messages.Message):
  r"""The response message for Locations.ListLocations.

  Fields:
    locations: A list of locations that matches the specified filter in the
      request.
    nextPageToken: The standard List next-page token.
  """

  locations = _messages.MessageField('Location', 1, repeated=True)
  nextPageToken = _messages.StringField(2)


class ListOperationsResponse(_messages.Message):
  r"""The response message for Operations.ListOperations.

  Fields:
    nextPageToken: The standard List next-page token.
    operations: A list of operations that matches the specified filter in the
      request.
  """

  nextPageToken = _messages.StringField(1)
  operations = _messages.MessageField('Operation', 2, repeated=True)


class ListWorkflowsResponse(_messages.Message):
  r"""Response for the ListWorkflows method.

  Fields:
    nextPageToken: A token, which can be sent as `page_token` to retrieve the
      next page. If this field is omitted, there are no subsequent pages.
    unreachable: Unreachable resources.
    workflows: The workflows which match the request.
  """

  nextPageToken = _messages.StringField(1)
  unreachable = _messages.StringField(2, repeated=True)
  workflows = _messages.MessageField('Workflow', 3, repeated=True)


class Location(_messages.Message):
  r"""A resource that represents Google Cloud Platform location.

  Messages:
    LabelsValue: Cross-service attributes for the location. For example
      {"cloud.googleapis.com/region": "us-east1"}
    MetadataValue: Service-specific metadata. For example the available
      capacity at the given location.

  Fields:
    displayName: The friendly name for this location, typically a nearby city
      name. For example, "Tokyo".
    labels: Cross-service attributes for the location. For example
      {"cloud.googleapis.com/region": "us-east1"}
    locationId: The canonical id for this location. For example: `"us-east1"`.
    metadata: Service-specific metadata. For example the available capacity at
      the given location.
    name: Resource name for the location, which may vary between
      implementations. For example: `"projects/example-project/locations/us-
      east1"`
  """

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    r"""Cross-service attributes for the location. For example
    {"cloud.googleapis.com/region": "us-east1"}

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

  @encoding.MapUnrecognizedFields('additionalProperties')
  class MetadataValue(_messages.Message):
    r"""Service-specific metadata. For example the available capacity at the
    given location.

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

  displayName = _messages.StringField(1)
  labels = _messages.MessageField('LabelsValue', 2)
  locationId = _messages.StringField(3)
  metadata = _messages.MessageField('MetadataValue', 4)
  name = _messages.StringField(5)


class Operation(_messages.Message):
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
  error = _messages.MessageField('Status', 2)
  metadata = _messages.MessageField('MetadataValue', 3)
  name = _messages.StringField(4)
  response = _messages.MessageField('ResponseValue', 5)


class OperationMetadata(_messages.Message):
  r"""Represents the metadata of the long-running operation.

  Fields:
    apiVersion: API version used to start the operation.
    createTime: The time the operation was created.
    endTime: The time the operation finished running.
    target: Server-defined resource path for the target of the operation.
    verb: Name of the verb executed by the operation.
  """

  apiVersion = _messages.StringField(1)
  createTime = _messages.StringField(2)
  endTime = _messages.StringField(3)
  target = _messages.StringField(4)
  verb = _messages.StringField(5)


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


class Status(_messages.Message):
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


class Workflow(_messages.Message):
  r"""Workflow program to be executed by Workflows.

  Enums:
    StateValueValuesEnum: Output only. State of the workflow deployment.

  Messages:
    LabelsValue: Labels associated with this workflow. Labels can contain at
      most 64 entries. Keys and values can be no longer than 63 characters and
      can only contain lowercase letters, numeric characters, underscores and
      dashes. Label keys must start with a letter. International characters
      are allowed.

  Fields:
    createTime: Output only. The timestamp of when the workflow was created.
    description: Description of the workflow provided by the user. Must be at
      most 1000 unicode characters long.
    labels: Labels associated with this workflow. Labels can contain at most
      64 entries. Keys and values can be no longer than 63 characters and can
      only contain lowercase letters, numeric characters, underscores and
      dashes. Label keys must start with a letter. International characters
      are allowed.
    name: The resource name of the workflow. Format:
      projects/{project}/locations/{location}/workflows/{workflow}
    revisionCreateTime: Output only. The timestamp that the latest revision of
      the workflow was created.
    revisionId: Output only. The revision of the workflow. A new revision of a
      workflow is created as a result of updating the following properties of
      a workflow: - Service account - Workflow code to be executed The format
      is "000001-a4d", where the first 6 characters define the zero-padded
      revision ordinal number. They are followed by a hyphen and 3 hexadecimal
      random characters.
    serviceAccount: The service account associated with the latest workflow
      version. This service account represents the identity of the workflow
      and determines what permissions the workflow has. Format:
      projects/{project}/serviceAccounts/{account} or {account} Using `-` as a
      wildcard for the `{project}` or not providing one at all will infer the
      project from the account. The `{account}` value can be the `email`
      address or the `unique_id` of the service account. If not provided,
      workflow will use the project's default service account. Modifying this
      field for an existing workflow results in a new workflow revision.
    sourceContents: Workflow code to be executed. The size limit is 128KB.
    state: Output only. State of the workflow deployment.
    updateTime: Output only. The last update timestamp of the workflow.
  """

  class StateValueValuesEnum(_messages.Enum):
    r"""Output only. State of the workflow deployment.

    Values:
      STATE_UNSPECIFIED: Invalid state.
      ACTIVE: The workflow has been deployed successfully and is serving.
    """
    STATE_UNSPECIFIED = 0
    ACTIVE = 1

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    r"""Labels associated with this workflow. Labels can contain at most 64
    entries. Keys and values can be no longer than 63 characters and can only
    contain lowercase letters, numeric characters, underscores and dashes.
    Label keys must start with a letter. International characters are allowed.

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
  description = _messages.StringField(2)
  labels = _messages.MessageField('LabelsValue', 3)
  name = _messages.StringField(4)
  revisionCreateTime = _messages.StringField(5)
  revisionId = _messages.StringField(6)
  serviceAccount = _messages.StringField(7)
  sourceContents = _messages.StringField(8)
  state = _messages.EnumField('StateValueValuesEnum', 9)
  updateTime = _messages.StringField(10)


class WorkflowsProjectsLocationsGetRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsGetRequest object.

  Fields:
    name: Resource name for the location.
  """

  name = _messages.StringField(1, required=True)


class WorkflowsProjectsLocationsListRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsListRequest object.

  Fields:
    filter: A filter to narrow down results to a preferred subset. The
      filtering language accepts strings like "displayName=tokyo", and is
      documented in more detail in [AIP-160](https://google.aip.dev/160).
    name: The resource that owns the locations collection, if applicable.
    pageSize: The maximum number of results to return. If not set, the service
      selects a default.
    pageToken: A page token received from the `next_page_token` field in the
      response. Send that page token to receive the subsequent page.
  """

  filter = _messages.StringField(1)
  name = _messages.StringField(2, required=True)
  pageSize = _messages.IntegerField(3, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(4)


class WorkflowsProjectsLocationsOperationsDeleteRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsOperationsDeleteRequest object.

  Fields:
    name: The name of the operation resource to be deleted.
  """

  name = _messages.StringField(1, required=True)


class WorkflowsProjectsLocationsOperationsGetRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsOperationsGetRequest object.

  Fields:
    name: The name of the operation resource.
  """

  name = _messages.StringField(1, required=True)


class WorkflowsProjectsLocationsOperationsListRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsOperationsListRequest object.

  Fields:
    filter: The standard list filter.
    name: The name of the operation's parent resource.
    pageSize: The standard list page size.
    pageToken: The standard list page token.
  """

  filter = _messages.StringField(1)
  name = _messages.StringField(2, required=True)
  pageSize = _messages.IntegerField(3, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(4)


class WorkflowsProjectsLocationsWorkflowsCreateRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsWorkflowsCreateRequest object.

  Fields:
    parent: Required. Project and location in which the workflow should be
      created. Format: projects/{project}/locations/{location}
    workflow: A Workflow resource to be passed as the request body.
    workflowId: Required. The ID of the workflow to be created. It has to
      fulfill the following requirements: * Must contain only letters,
      numbers, underscores and hyphens. * Must start with a letter. * Must be
      between 1-64 characters. * Must end with a number or a letter. * Must be
      unique within the customer project and location.
  """

  parent = _messages.StringField(1, required=True)
  workflow = _messages.MessageField('Workflow', 2)
  workflowId = _messages.StringField(3)


class WorkflowsProjectsLocationsWorkflowsDeleteRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsWorkflowsDeleteRequest object.

  Fields:
    name: Required. Name of the workflow to be deleted. Format:
      projects/{project}/locations/{location}/workflows/{workflow}
  """

  name = _messages.StringField(1, required=True)


class WorkflowsProjectsLocationsWorkflowsGetRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsWorkflowsGetRequest object.

  Fields:
    name: Required. Name of the workflow which information should be
      retrieved. Format:
      projects/{project}/locations/{location}/workflows/{workflow}
  """

  name = _messages.StringField(1, required=True)


class WorkflowsProjectsLocationsWorkflowsListRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsWorkflowsListRequest object.

  Fields:
    filter: Filter to restrict results to specific workflows.
    orderBy: Comma-separated list of fields that that specify the order of the
      results. Default sorting order for a field is ascending. To specify
      descending order for a field, append a " desc" suffix. If not specified,
      the results will be returned in an unspecified order.
    pageSize: Maximum number of workflows to return per call. The service may
      return fewer than this value. If the value is not specified, a default
      value of 500 will be used. The maximum permitted value is 1000 and
      values greater than 1000 will be coerced down to 1000.
    pageToken: A page token, received from a previous `ListWorkflows` call.
      Provide this to retrieve the subsequent page. When paginating, all other
      parameters provided to `ListWorkflows` must match the call that provided
      the page token.
    parent: Required. Project and location from which the workflows should be
      listed. Format: projects/{project}/locations/{location}
  """

  filter = _messages.StringField(1)
  orderBy = _messages.StringField(2)
  pageSize = _messages.IntegerField(3, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(4)
  parent = _messages.StringField(5, required=True)


class WorkflowsProjectsLocationsWorkflowsPatchRequest(_messages.Message):
  r"""A WorkflowsProjectsLocationsWorkflowsPatchRequest object.

  Fields:
    name: The resource name of the workflow. Format:
      projects/{project}/locations/{location}/workflows/{workflow}
    updateMask: List of fields to be updated. If not present, the entire
      workflow will be updated.
    workflow: A Workflow resource to be passed as the request body.
  """

  name = _messages.StringField(1, required=True)
  updateMask = _messages.StringField(2)
  workflow = _messages.MessageField('Workflow', 3)


encoding.AddCustomJsonFieldMapping(
    StandardQueryParameters, 'f__xgafv', '$.xgafv')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_1', '1')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_2', '2')
