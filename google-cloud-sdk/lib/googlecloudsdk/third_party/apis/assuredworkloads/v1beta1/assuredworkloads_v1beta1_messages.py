"""Generated message classes for assuredworkloads version v1beta1.

"""
# NOTE: This file is autogenerated and should not be edited by hand.

from __future__ import absolute_import

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from apitools.base.py import extra_types


package = 'assuredworkloads'


class AssuredworkloadsOrganizationsLocationsOperationsGetRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsOperationsGetRequest object.

  Fields:
    name: The name of the operation resource.
  """

  name = _messages.StringField(1, required=True)


class AssuredworkloadsOrganizationsLocationsOperationsListRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsOperationsListRequest object.

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


class AssuredworkloadsOrganizationsLocationsWorkloadsCreateRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsWorkloadsCreateRequest object.

  Fields:
    externalId: Optional. A identifier associated with the workload and
      underlying projects which allows for the break down of billing costs for
      a workload. The value provided for the identifier will add a label to
      the workload and contained projects with the identifier as the value.
    googleCloudAssuredworkloadsV1beta1Workload: A
      GoogleCloudAssuredworkloadsV1beta1Workload resource to be passed as the
      request body.
    parent: Required. The resource name of the new Workload's parent. Must be
      of the form `organizations/{org_id}/locations/{location_id}`.
  """

  externalId = _messages.StringField(1)
  googleCloudAssuredworkloadsV1beta1Workload = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1Workload', 2)
  parent = _messages.StringField(3, required=True)


class AssuredworkloadsOrganizationsLocationsWorkloadsDeleteRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsWorkloadsDeleteRequest object.

  Fields:
    etag: Optional. The etag of the workload. If this is provided, it must
      match the server's etag.
    name: Required. The `name` field is used to identify the workload. Format:
      organizations/{org_id}/locations/{location_id}/workloads/{workload_id}
  """

  etag = _messages.StringField(1)
  name = _messages.StringField(2, required=True)


class AssuredworkloadsOrganizationsLocationsWorkloadsGetRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsWorkloadsGetRequest object.

  Fields:
    name: Required. The resource name of the Workload to fetch. This is the
      workloads's relative path in the API, formatted as "organizations/{organ
      ization_id}/locations/{location_id}/workloads/{workload_id}". For
      example, "organizations/123/locations/us-east1/workloads/assured-
      workload-1".
  """

  name = _messages.StringField(1, required=True)


class AssuredworkloadsOrganizationsLocationsWorkloadsListRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsWorkloadsListRequest object.

  Fields:
    filter: A custom filter for filtering by properties of a workload. At this
      time, only filtering by labels is supported.
    pageSize: Page size.
    pageToken: Page token returned from previous request. Page token contains
      context from previous request. Page token needs to be passed in the
      second and following requests.
    parent: Required. Parent Resource to list workloads from. Must be of the
      form `organizations/{org_id}/locations/{location}`.
  """

  filter = _messages.StringField(1)
  pageSize = _messages.IntegerField(2, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(3)
  parent = _messages.StringField(4, required=True)


class AssuredworkloadsOrganizationsLocationsWorkloadsPatchRequest(_messages.Message):
  r"""A AssuredworkloadsOrganizationsLocationsWorkloadsPatchRequest object.

  Fields:
    googleCloudAssuredworkloadsV1beta1Workload: A
      GoogleCloudAssuredworkloadsV1beta1Workload resource to be passed as the
      request body.
    name: Optional. The resource name of the workload. Format:
      organizations/{organization}/locations/{location}/workloads/{workload}
      Read-only.
    updateMask: Required. The list of fields to be updated.
  """

  googleCloudAssuredworkloadsV1beta1Workload = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1Workload', 1)
  name = _messages.StringField(2, required=True)
  updateMask = _messages.StringField(3)


class GoogleCloudAssuredworkloadsV1CreateWorkloadOperationMetadata(_messages.Message):
  r"""Operation metadata to give request details of CreateWorkload.

  Enums:
    ComplianceRegimeValueValuesEnum: Optional. Compliance controls that should
      be applied to the resources managed by the workload.

  Fields:
    complianceRegime: Optional. Compliance controls that should be applied to
      the resources managed by the workload.
    createTime: Optional. Time when the operation was created.
    displayName: Optional. The display name of the workload.
    parent: Optional. The parent of the workload.
  """

  class ComplianceRegimeValueValuesEnum(_messages.Enum):
    r"""Optional. Compliance controls that should be applied to the resources
    managed by the workload.

    Values:
      COMPLIANCE_REGIME_UNSPECIFIED: Unknown compliance regime.
      IL4: Information protection as per DoD IL4 requirements.
      CJIS: Criminal Justice Information Services (CJIS) Security policies.
      FEDRAMP_HIGH: FedRAMP High data protection controls
      FEDRAMP_MODERATE: FedRAMP Moderate data protection controls
      US_REGIONAL_ACCESS: Assured Workloads For US Regions data protection
        controls
    """
    COMPLIANCE_REGIME_UNSPECIFIED = 0
    IL4 = 1
    CJIS = 2
    FEDRAMP_HIGH = 3
    FEDRAMP_MODERATE = 4
    US_REGIONAL_ACCESS = 5

  complianceRegime = _messages.EnumField('ComplianceRegimeValueValuesEnum', 1)
  createTime = _messages.StringField(2)
  displayName = _messages.StringField(3)
  parent = _messages.StringField(4)


class GoogleCloudAssuredworkloadsV1Workload(_messages.Message):
  r"""An Workload object for managing highly regulated workloads of cloud
  customers.

  Enums:
    ComplianceRegimeValueValuesEnum: Required. Immutable. Compliance Regime
      associated with this workload.

  Messages:
    LabelsValue: Optional. Labels applied to the workload.

  Fields:
    billingAccount: Required. Input only. The billing account used for the
      resources which are direct children of workload. This billing account is
      initially associated with the resources created as part of Workload
      creation. After the initial creation of these resources, the customer
      can change the assigned billing account. The resource name has the form
      `billingAccounts/{billing_account_id}`. For example,
      `billingAccounts/012345-567890-ABCDEF`.
    complianceRegime: Required. Immutable. Compliance Regime associated with
      this workload.
    createTime: Output only. Immutable. The Workload creation timestamp.
    displayName: Required. The user-assigned display name of the Workload.
      When present it must be between 4 to 30 characters. Allowed characters
      are: lowercase and uppercase letters, numbers, hyphen, and spaces.
      Example: My Workload
    etag: Optional. ETag of the workload, it is calculated on the basis of the
      Workload contents. It will be used in Update & Delete operations.
    kmsSettings: Input only. Settings used to create a CMEK crypto key. When
      set a project with a KMS CMEK key is provisioned. This field is
      mandatory for a subset of Compliance Regimes.
    labels: Optional. Labels applied to the workload.
    name: Optional. The resource name of the workload. Format:
      organizations/{organization}/locations/{location}/workloads/{workload}
      Read-only.
    provisionedResourcesParent: Input only. The parent resource for the
      resources managed by this Assured Workload. May be either an
      organization or a folder. Must be the same or a child of the Workload
      parent. If not specified all resources are created under the Workload
      parent. Formats: folders/{folder_id} organizations/{organization_id}
    resourceSettings: Input only. Resource properties that are used to
      customize workload resources. These properties (such as custom project
      id) will be used to create workload resources if possible. This field is
      optional.
    resources: Output only. The resources associated with this workload. These
      resources will be created when creating the workload. If any of the
      projects already exist, the workload creation will fail. Always read
      only.
  """

  class ComplianceRegimeValueValuesEnum(_messages.Enum):
    r"""Required. Immutable. Compliance Regime associated with this workload.

    Values:
      COMPLIANCE_REGIME_UNSPECIFIED: Unknown compliance regime.
      IL4: Information protection as per DoD IL4 requirements.
      CJIS: Criminal Justice Information Services (CJIS) Security policies.
      FEDRAMP_HIGH: FedRAMP High data protection controls
      FEDRAMP_MODERATE: FedRAMP Moderate data protection controls
      US_REGIONAL_ACCESS: Assured Workloads For US Regions data protection
        controls
    """
    COMPLIANCE_REGIME_UNSPECIFIED = 0
    IL4 = 1
    CJIS = 2
    FEDRAMP_HIGH = 3
    FEDRAMP_MODERATE = 4
    US_REGIONAL_ACCESS = 5

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    r"""Optional. Labels applied to the workload.

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

  billingAccount = _messages.StringField(1)
  complianceRegime = _messages.EnumField('ComplianceRegimeValueValuesEnum', 2)
  createTime = _messages.StringField(3)
  displayName = _messages.StringField(4)
  etag = _messages.StringField(5)
  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1WorkloadKMSSettings', 6)
  labels = _messages.MessageField('LabelsValue', 7)
  name = _messages.StringField(8)
  provisionedResourcesParent = _messages.StringField(9)
  resourceSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1WorkloadResourceSettings', 10, repeated=True)
  resources = _messages.MessageField('GoogleCloudAssuredworkloadsV1WorkloadResourceInfo', 11, repeated=True)


class GoogleCloudAssuredworkloadsV1WorkloadKMSSettings(_messages.Message):
  r"""Settings specific to the Key Management Service.

  Fields:
    nextRotationTime: Required. Input only. Immutable. The time at which the
      Key Management Service will automatically create a new version of the
      crypto key and mark it as the primary.
    rotationPeriod: Required. Input only. Immutable. [next_rotation_time] will
      be advanced by this period when the Key Management Service automatically
      rotates a key. Must be at least 24 hours and at most 876,000 hours.
  """

  nextRotationTime = _messages.StringField(1)
  rotationPeriod = _messages.StringField(2)


class GoogleCloudAssuredworkloadsV1WorkloadResourceInfo(_messages.Message):
  r"""Represent the resources that are children of this Workload.

  Enums:
    ResourceTypeValueValuesEnum: Indicates the type of resource.

  Fields:
    resourceId: Resource identifier. For a project this represents
      project_number.
    resourceType: Indicates the type of resource.
  """

  class ResourceTypeValueValuesEnum(_messages.Enum):
    r"""Indicates the type of resource.

    Values:
      RESOURCE_TYPE_UNSPECIFIED: Unknown resource type.
      CONSUMER_PROJECT: Consumer project.
      ENCRYPTION_KEYS_PROJECT: Consumer project containing encryption keys.
    """
    RESOURCE_TYPE_UNSPECIFIED = 0
    CONSUMER_PROJECT = 1
    ENCRYPTION_KEYS_PROJECT = 2

  resourceId = _messages.IntegerField(1)
  resourceType = _messages.EnumField('ResourceTypeValueValuesEnum', 2)


class GoogleCloudAssuredworkloadsV1WorkloadResourceSettings(_messages.Message):
  r"""Represent the custom settings for the resources to be created.

  Enums:
    ResourceTypeValueValuesEnum: Indicates the type of resource. This field
      should be specified to correspond the id to the right project type
      (CONSUMER_PROJECT or ENCRYPTION_KEYS_PROJECT)

  Fields:
    resourceId: Resource identifier. For a project this represents project_id.
      If the project is already taken, the workload creation will fail.
    resourceType: Indicates the type of resource. This field should be
      specified to correspond the id to the right project type
      (CONSUMER_PROJECT or ENCRYPTION_KEYS_PROJECT)
  """

  class ResourceTypeValueValuesEnum(_messages.Enum):
    r"""Indicates the type of resource. This field should be specified to
    correspond the id to the right project type (CONSUMER_PROJECT or
    ENCRYPTION_KEYS_PROJECT)

    Values:
      RESOURCE_TYPE_UNSPECIFIED: Unknown resource type.
      CONSUMER_PROJECT: Consumer project.
      ENCRYPTION_KEYS_PROJECT: Consumer project containing encryption keys.
    """
    RESOURCE_TYPE_UNSPECIFIED = 0
    CONSUMER_PROJECT = 1
    ENCRYPTION_KEYS_PROJECT = 2

  resourceId = _messages.StringField(1)
  resourceType = _messages.EnumField('ResourceTypeValueValuesEnum', 2)


class GoogleCloudAssuredworkloadsV1beta1CreateWorkloadOperationMetadata(_messages.Message):
  r"""Operation metadata to give request details of CreateWorkload.

  Enums:
    ComplianceRegimeValueValuesEnum: Optional. Compliance controls that should
      be applied to the resources managed by the workload.

  Fields:
    complianceRegime: Optional. Compliance controls that should be applied to
      the resources managed by the workload.
    createTime: Optional. Time when the operation was created.
    displayName: Optional. The display name of the workload.
    parent: Optional. The parent of the workload.
  """

  class ComplianceRegimeValueValuesEnum(_messages.Enum):
    r"""Optional. Compliance controls that should be applied to the resources
    managed by the workload.

    Values:
      COMPLIANCE_REGIME_UNSPECIFIED: Unknown compliance regime.
      IL4: Information protection as per DoD IL4 requirements.
      CJIS: Criminal Justice Information Services (CJIS) Security policies.
      FEDRAMP_HIGH: FedRAMP High data protection controls
      FEDRAMP_MODERATE: FedRAMP Moderate data protection controls
      US_REGIONAL_ACCESS: Assured Workloads For US Regions data protection
        controls
      HIPAA: Health Insurance Portability and Accountability Act controls
      HITRUST: Health Information Trust Alliance controls
    """
    COMPLIANCE_REGIME_UNSPECIFIED = 0
    IL4 = 1
    CJIS = 2
    FEDRAMP_HIGH = 3
    FEDRAMP_MODERATE = 4
    US_REGIONAL_ACCESS = 5
    HIPAA = 6
    HITRUST = 7

  complianceRegime = _messages.EnumField('ComplianceRegimeValueValuesEnum', 1)
  createTime = _messages.StringField(2)
  displayName = _messages.StringField(3)
  parent = _messages.StringField(4)


class GoogleCloudAssuredworkloadsV1beta1ListWorkloadsResponse(_messages.Message):
  r"""Response of ListWorkloads endpoint.

  Fields:
    nextPageToken: The next page token. Return empty if reached the last page.
    workloads: List of Workloads under a given parent.
  """

  nextPageToken = _messages.StringField(1)
  workloads = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1Workload', 2, repeated=True)


class GoogleCloudAssuredworkloadsV1beta1Workload(_messages.Message):
  r"""An Workload object for managing highly regulated workloads of cloud
  customers.

  Enums:
    ComplianceRegimeValueValuesEnum: Required. Immutable. Compliance Regime
      associated with this workload.

  Messages:
    LabelsValue: Optional. Labels applied to the workload.

  Fields:
    billingAccount: Required. Input only. The billing account used for the
      resources which are direct children of workload. This billing account is
      initially associated with the resources created as part of Workload
      creation. After the initial creation of these resources, the customer
      can change the assigned billing account. The resource name has the form
      `billingAccounts/{billing_account_id}`. For example,
      `billingAccounts/012345-567890-ABCDEF`.
    cjisSettings: Required. Input only. Immutable. Settings specific to
      resources needed for CJIS.
    complianceRegime: Required. Immutable. Compliance Regime associated with
      this workload.
    createTime: Output only. Immutable. The Workload creation timestamp.
    displayName: Required. The user-assigned display name of the Workload.
      When present it must be between 4 to 30 characters. Allowed characters
      are: lowercase and uppercase letters, numbers, hyphen, and spaces.
      Example: My Workload
    etag: Optional. ETag of the workload, it is calculated on the basis of the
      Workload contents. It will be used in Update & Delete operations.
    fedrampHighSettings: Required. Input only. Immutable. Settings specific to
      resources needed for FedRAMP High.
    fedrampModerateSettings: Required. Input only. Immutable. Settings
      specific to resources needed for FedRAMP Moderate.
    il4Settings: Required. Input only. Immutable. Settings specific to
      resources needed for IL4.
    kmsSettings: Input only. Settings used to create a CMEK crypto key. When
      set a project with a KMS CMEK key is provisioned. This field is
      mandatory for a subset of Compliance Regimes.
    labels: Optional. Labels applied to the workload.
    name: Optional. The resource name of the workload. Format:
      organizations/{organization}/locations/{location}/workloads/{workload}
      Read-only.
    provisionedResourcesParent: Input only. The parent resource for the
      resources managed by this Assured Workload. May be either an
      organization or a folder. Must be the same or a child of the Workload
      parent. If not specified all resources are created under the Workload
      parent. Formats: folders/{folder_id} organizations/{organization_id}
    resourceSettings: Input only. Resource properties that are used to
      customize workload resources. These properties (such as custom project
      id) will be used to create workload resources if possible. This field is
      optional.
    resources: Output only. The resources associated with this workload. These
      resources will be created when creating the workload. If any of the
      projects already exist, the workload creation will fail. Always read
      only.
  """

  class ComplianceRegimeValueValuesEnum(_messages.Enum):
    r"""Required. Immutable. Compliance Regime associated with this workload.

    Values:
      COMPLIANCE_REGIME_UNSPECIFIED: Unknown compliance regime.
      IL4: Information protection as per DoD IL4 requirements.
      CJIS: Criminal Justice Information Services (CJIS) Security policies.
      FEDRAMP_HIGH: FedRAMP High data protection controls
      FEDRAMP_MODERATE: FedRAMP Moderate data protection controls
      US_REGIONAL_ACCESS: Assured Workloads For US Regions data protection
        controls
      HIPAA: Health Insurance Portability and Accountability Act controls
      HITRUST: Health Information Trust Alliance controls
    """
    COMPLIANCE_REGIME_UNSPECIFIED = 0
    IL4 = 1
    CJIS = 2
    FEDRAMP_HIGH = 3
    FEDRAMP_MODERATE = 4
    US_REGIONAL_ACCESS = 5
    HIPAA = 6
    HITRUST = 7

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    r"""Optional. Labels applied to the workload.

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

  billingAccount = _messages.StringField(1)
  cjisSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadCJISSettings', 2)
  complianceRegime = _messages.EnumField('ComplianceRegimeValueValuesEnum', 3)
  createTime = _messages.StringField(4)
  displayName = _messages.StringField(5)
  etag = _messages.StringField(6)
  fedrampHighSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadFedrampHighSettings', 7)
  fedrampModerateSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadFedrampModerateSettings', 8)
  il4Settings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadIL4Settings', 9)
  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings', 10)
  labels = _messages.MessageField('LabelsValue', 11)
  name = _messages.StringField(12)
  provisionedResourcesParent = _messages.StringField(13)
  resourceSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadResourceSettings', 14, repeated=True)
  resources = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadResourceInfo', 15, repeated=True)


class GoogleCloudAssuredworkloadsV1beta1WorkloadCJISSettings(_messages.Message):
  r"""Settings specific to resources needed for CJIS.

  Fields:
    kmsSettings: Required. Input only. Immutable. Settings used to create a
      CMEK crypto key.
  """

  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings', 1)


class GoogleCloudAssuredworkloadsV1beta1WorkloadFedrampHighSettings(_messages.Message):
  r"""Settings specific to resources needed for FedRAMP High.

  Fields:
    kmsSettings: Required. Input only. Immutable. Settings used to create a
      CMEK crypto key.
  """

  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings', 1)


class GoogleCloudAssuredworkloadsV1beta1WorkloadFedrampModerateSettings(_messages.Message):
  r"""Settings specific to resources needed for FedRAMP Moderate.

  Fields:
    kmsSettings: Required. Input only. Immutable. Settings used to create a
      CMEK crypto key.
  """

  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings', 1)


class GoogleCloudAssuredworkloadsV1beta1WorkloadIL4Settings(_messages.Message):
  r"""Settings specific to resources needed for IL4.

  Fields:
    kmsSettings: Required. Input only. Immutable. Settings used to create a
      CMEK crypto key.
  """

  kmsSettings = _messages.MessageField('GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings', 1)


class GoogleCloudAssuredworkloadsV1beta1WorkloadKMSSettings(_messages.Message):
  r"""Settings specific to the Key Management Service.

  Fields:
    nextRotationTime: Required. Input only. Immutable. The time at which the
      Key Management Service will automatically create a new version of the
      crypto key and mark it as the primary.
    rotationPeriod: Required. Input only. Immutable. [next_rotation_time] will
      be advanced by this period when the Key Management Service automatically
      rotates a key. Must be at least 24 hours and at most 876,000 hours.
  """

  nextRotationTime = _messages.StringField(1)
  rotationPeriod = _messages.StringField(2)


class GoogleCloudAssuredworkloadsV1beta1WorkloadResourceInfo(_messages.Message):
  r"""Represent the resources that are children of this Workload.

  Enums:
    ResourceTypeValueValuesEnum: Indicates the type of resource.

  Fields:
    resourceId: Resource identifier. For a project this represents
      project_number.
    resourceType: Indicates the type of resource.
  """

  class ResourceTypeValueValuesEnum(_messages.Enum):
    r"""Indicates the type of resource.

    Values:
      RESOURCE_TYPE_UNSPECIFIED: Unknown resource type.
      CONSUMER_PROJECT: Consumer project.
      ENCRYPTION_KEYS_PROJECT: Consumer project containing encryption keys.
    """
    RESOURCE_TYPE_UNSPECIFIED = 0
    CONSUMER_PROJECT = 1
    ENCRYPTION_KEYS_PROJECT = 2

  resourceId = _messages.IntegerField(1)
  resourceType = _messages.EnumField('ResourceTypeValueValuesEnum', 2)


class GoogleCloudAssuredworkloadsV1beta1WorkloadResourceSettings(_messages.Message):
  r"""Represent the custom settings for the resources to be created.

  Enums:
    ResourceTypeValueValuesEnum: Indicates the type of resource. This field
      should be specified to correspond the id to the right project type
      (CONSUMER_PROJECT or ENCRYPTION_KEYS_PROJECT)

  Fields:
    resourceId: Resource identifier. For a project this represents project_id.
      If the project is already taken, the workload creation will fail.
    resourceType: Indicates the type of resource. This field should be
      specified to correspond the id to the right project type
      (CONSUMER_PROJECT or ENCRYPTION_KEYS_PROJECT)
  """

  class ResourceTypeValueValuesEnum(_messages.Enum):
    r"""Indicates the type of resource. This field should be specified to
    correspond the id to the right project type (CONSUMER_PROJECT or
    ENCRYPTION_KEYS_PROJECT)

    Values:
      RESOURCE_TYPE_UNSPECIFIED: Unknown resource type.
      CONSUMER_PROJECT: Consumer project.
      ENCRYPTION_KEYS_PROJECT: Consumer project containing encryption keys.
    """
    RESOURCE_TYPE_UNSPECIFIED = 0
    CONSUMER_PROJECT = 1
    ENCRYPTION_KEYS_PROJECT = 2

  resourceId = _messages.StringField(1)
  resourceType = _messages.EnumField('ResourceTypeValueValuesEnum', 2)


class GoogleLongrunningListOperationsResponse(_messages.Message):
  r"""The response message for Operations.ListOperations.

  Fields:
    nextPageToken: The standard List next-page token.
    operations: A list of operations that matches the specified filter in the
      request.
  """

  nextPageToken = _messages.StringField(1)
  operations = _messages.MessageField('GoogleLongrunningOperation', 2, repeated=True)


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


class GoogleProtobufEmpty(_messages.Message):
  r"""A generic empty message that you can re-use to avoid defining duplicated
  empty messages in your APIs. A typical example is to use it as the request
  or the response type of an API method. For instance: service Foo { rpc
  Bar(google.protobuf.Empty) returns (google.protobuf.Empty); } The JSON
  representation for `Empty` is empty JSON object `{}`.
  """



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
