"""Generated client library for servicemanagement version v1."""
# NOTE: This file is autogenerated and should not be edited by hand.

from __future__ import absolute_import

from apitools.base.py import base_api
from googlecloudsdk.third_party.apis.servicemanagement.v1 import servicemanagement_v1_messages as messages


class ServicemanagementV1(base_api.BaseApiClient):
  """Generated client library for service servicemanagement version v1."""

  MESSAGES_MODULE = messages
  BASE_URL = 'https://servicemanagement.googleapis.com/'
  MTLS_BASE_URL = 'https://servicemanagement.mtls.googleapis.com/'

  _PACKAGE = 'servicemanagement'
  _SCOPES = ['https://www.googleapis.com/auth/cloud-platform', 'https://www.googleapis.com/auth/cloud-platform.read-only', 'https://www.googleapis.com/auth/service.management', 'https://www.googleapis.com/auth/service.management.readonly']
  _VERSION = 'v1'
  _CLIENT_ID = '1042881264118.apps.googleusercontent.com'
  _CLIENT_SECRET = 'x_Tw5K8nnjoRAqULM9PFAC2b'
  _USER_AGENT = 'google-cloud-sdk'
  _CLIENT_CLASS_NAME = 'ServicemanagementV1'
  _URL_VERSION = 'v1'
  _API_KEY = None

  def __init__(self, url='', credentials=None,
               get_credentials=True, http=None, model=None,
               log_request=False, log_response=False,
               credentials_args=None, default_global_params=None,
               additional_http_headers=None, response_encoding=None):
    """Create a new servicemanagement handle."""
    url = url or self.BASE_URL
    super(ServicemanagementV1, self).__init__(
        url, credentials=credentials,
        get_credentials=get_credentials, http=http, model=model,
        log_request=log_request, log_response=log_response,
        credentials_args=credentials_args,
        default_global_params=default_global_params,
        additional_http_headers=additional_http_headers,
        response_encoding=response_encoding)
    self.operations = self.OperationsService(self)
    self.services_accessPolicy = self.ServicesAccessPolicyService(self)
    self.services_configs = self.ServicesConfigsService(self)
    self.services_consumers = self.ServicesConsumersService(self)
    self.services_customerSettings = self.ServicesCustomerSettingsService(self)
    self.services_projectSettings = self.ServicesProjectSettingsService(self)
    self.services_rollouts = self.ServicesRolloutsService(self)
    self.services = self.ServicesService(self)

  class OperationsService(base_api.BaseApiService):
    """Service class for the operations resource."""

    _NAME = 'operations'

    def __init__(self, client):
      super(ServicemanagementV1.OperationsService, self).__init__(client)
      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      r"""Gets the latest state of a long-running operation. Clients can use this method to poll the operation result at intervals as recommended by the API service.

      Args:
        request: (ServicemanagementOperationsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.operations.get',
        ordered_params=['operationsId'],
        path_params=['operationsId'],
        query_params=[],
        relative_path='v1/operations/{operationsId}',
        request_field='',
        request_type_name='ServicemanagementOperationsGetRequest',
        response_type_name='Operation',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Lists service operations that match the specified filter in the request.

      Args:
        request: (ServicemanagementOperationsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ListOperationsResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.operations.list',
        ordered_params=[],
        path_params=[],
        query_params=['filter', 'name', 'pageSize', 'pageToken'],
        relative_path='v1/operations',
        request_field='',
        request_type_name='ServicemanagementOperationsListRequest',
        response_type_name='ListOperationsResponse',
        supports_download=False,
    )

  class ServicesAccessPolicyService(base_api.BaseApiService):
    """Service class for the services_accessPolicy resource."""

    _NAME = 'services_accessPolicy'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesAccessPolicyService, self).__init__(client)
      self._upload_configs = {
          }

    def Query(self, request, global_params=None):
      r"""Method to query the accessibility of a service and any associated visibility labels for a specified user. Members of the producer project may call this method and specify any user. Any user may call this method, but must specify their own email address. In this case the method will return NOT_FOUND if the user has no access to the service.

      Args:
        request: (ServicemanagementServicesAccessPolicyQueryRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (QueryUserAccessResponse) The response message.
      """
      config = self.GetMethodConfig('Query')
      return self._RunMethod(
          config, request, global_params=global_params)

    Query.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.accessPolicy.query',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['userEmail'],
        relative_path='v1/services/{serviceName}/accessPolicy:query',
        request_field='',
        request_type_name='ServicemanagementServicesAccessPolicyQueryRequest',
        response_type_name='QueryUserAccessResponse',
        supports_download=False,
    )

  class ServicesConfigsService(base_api.BaseApiService):
    """Service class for the services_configs resource."""

    _NAME = 'services_configs'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesConfigsService, self).__init__(client)
      self._upload_configs = {
          }

    def Create(self, request, global_params=None):
      r"""Creates a new service configuration (version) for a managed service. This method only stores the service configuration. To roll out the service configuration to backend systems please call CreateServiceRollout. Only the 100 most recent service configurations and ones referenced by existing rollouts are kept for each service. The rest will be deleted eventually.

      Args:
        request: (ServicemanagementServicesConfigsCreateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Service) The response message.
      """
      config = self.GetMethodConfig('Create')
      return self._RunMethod(
          config, request, global_params=global_params)

    Create.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.configs.create',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=[],
        relative_path='v1/services/{serviceName}/configs',
        request_field='service',
        request_type_name='ServicemanagementServicesConfigsCreateRequest',
        response_type_name='Service',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Gets a service configuration (version) for a managed service.

      Args:
        request: (ServicemanagementServicesConfigsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Service) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.configs.get',
        ordered_params=['serviceName', 'configId'],
        path_params=['configId', 'serviceName'],
        query_params=['view'],
        relative_path='v1/services/{serviceName}/configs/{configId}',
        request_field='',
        request_type_name='ServicemanagementServicesConfigsGetRequest',
        response_type_name='Service',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Lists the history of the service configuration for a managed service, from the newest to the oldest.

      Args:
        request: (ServicemanagementServicesConfigsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ListServiceConfigsResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.configs.list',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['pageSize', 'pageToken'],
        relative_path='v1/services/{serviceName}/configs',
        request_field='',
        request_type_name='ServicemanagementServicesConfigsListRequest',
        response_type_name='ListServiceConfigsResponse',
        supports_download=False,
    )

    def Submit(self, request, global_params=None):
      r"""Creates a new service configuration (version) for a managed service based on user-supplied configuration source files (for example: OpenAPI Specification). This method stores the source configurations as well as the generated service configuration. To rollout the service configuration to other services, please call CreateServiceRollout. Only the 100 most recent configuration sources and ones referenced by existing service configurtions are kept for each service. The rest will be deleted eventually. Operation.

      Args:
        request: (ServicemanagementServicesConfigsSubmitRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Submit')
      return self._RunMethod(
          config, request, global_params=global_params)

    Submit.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.configs.submit',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=[],
        relative_path='v1/services/{serviceName}/configs:submit',
        request_field='submitConfigSourceRequest',
        request_type_name='ServicemanagementServicesConfigsSubmitRequest',
        response_type_name='Operation',
        supports_download=False,
    )

  class ServicesConsumersService(base_api.BaseApiService):
    """Service class for the services_consumers resource."""

    _NAME = 'services_consumers'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesConsumersService, self).__init__(client)
      self._upload_configs = {
          }

    def GetIamPolicy(self, request, global_params=None):
      r"""Gets the access control policy for a resource. Returns an empty policy if the resource exists and does not have a policy set.

      Args:
        request: (ServicemanagementServicesConsumersGetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('GetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    GetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.consumers.getIamPolicy',
        ordered_params=['servicesId', 'consumersId'],
        path_params=['consumersId', 'servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}/consumers/{consumersId}:getIamPolicy',
        request_field='getIamPolicyRequest',
        request_type_name='ServicemanagementServicesConsumersGetIamPolicyRequest',
        response_type_name='Policy',
        supports_download=False,
    )

    def SetIamPolicy(self, request, global_params=None):
      r"""Sets the access control policy on the specified resource. Replaces any existing policy. Can return `NOT_FOUND`, `INVALID_ARGUMENT`, and `PERMISSION_DENIED` errors.

      Args:
        request: (ServicemanagementServicesConsumersSetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('SetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    SetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.consumers.setIamPolicy',
        ordered_params=['servicesId', 'consumersId'],
        path_params=['consumersId', 'servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}/consumers/{consumersId}:setIamPolicy',
        request_field='setIamPolicyRequest',
        request_type_name='ServicemanagementServicesConsumersSetIamPolicyRequest',
        response_type_name='Policy',
        supports_download=False,
    )

    def TestIamPermissions(self, request, global_params=None):
      r"""Returns permissions that a caller has on the specified resource. If the resource does not exist, this will return an empty set of permissions, not a `NOT_FOUND` error. Note: This operation is designed to be used for building permission-aware UIs and command-line tools, not for authorization checking. This operation may "fail open" without warning.

      Args:
        request: (ServicemanagementServicesConsumersTestIamPermissionsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TestIamPermissionsResponse) The response message.
      """
      config = self.GetMethodConfig('TestIamPermissions')
      return self._RunMethod(
          config, request, global_params=global_params)

    TestIamPermissions.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.consumers.testIamPermissions',
        ordered_params=['servicesId', 'consumersId'],
        path_params=['consumersId', 'servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}/consumers/{consumersId}:testIamPermissions',
        request_field='testIamPermissionsRequest',
        request_type_name='ServicemanagementServicesConsumersTestIamPermissionsRequest',
        response_type_name='TestIamPermissionsResponse',
        supports_download=False,
    )

  class ServicesCustomerSettingsService(base_api.BaseApiService):
    """Service class for the services_customerSettings resource."""

    _NAME = 'services_customerSettings'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesCustomerSettingsService, self).__init__(client)
      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      r"""Retrieves the settings that control the specified customer's usage of the service.

      Args:
        request: (ServicemanagementServicesCustomerSettingsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (CustomerSettings) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.customerSettings.get',
        ordered_params=['serviceName', 'customerId'],
        path_params=['customerId', 'serviceName'],
        query_params=['expand', 'view'],
        relative_path='v1/services/{serviceName}/customerSettings/{customerId}',
        request_field='',
        request_type_name='ServicemanagementServicesCustomerSettingsGetRequest',
        response_type_name='CustomerSettings',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches specified subset of the settings that control the specified customer's usage of the service. Attempts to update a field not controlled by the caller will result in an access denied error. Operation.

      Args:
        request: (ServicemanagementServicesCustomerSettingsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method='PATCH',
        method_id='servicemanagement.services.customerSettings.patch',
        ordered_params=['serviceName', 'customerId'],
        path_params=['customerId', 'serviceName'],
        query_params=['updateMask'],
        relative_path='v1/services/{serviceName}/customerSettings/{customerId}',
        request_field='customerSettings',
        request_type_name='ServicemanagementServicesCustomerSettingsPatchRequest',
        response_type_name='Operation',
        supports_download=False,
    )

  class ServicesProjectSettingsService(base_api.BaseApiService):
    """Service class for the services_projectSettings resource."""

    _NAME = 'services_projectSettings'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesProjectSettingsService, self).__init__(client)
      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      r"""Retrieves the settings that control the specified consumer project's usage of the service.

      Args:
        request: (ServicemanagementServicesProjectSettingsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ProjectSettings) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.projectSettings.get',
        ordered_params=['serviceName', 'consumerProjectId'],
        path_params=['consumerProjectId', 'serviceName'],
        query_params=['expand', 'view'],
        relative_path='v1/services/{serviceName}/projectSettings/{consumerProjectId}',
        request_field='',
        request_type_name='ServicemanagementServicesProjectSettingsGetRequest',
        response_type_name='ProjectSettings',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Updates specified subset of the settings that control the specified consumer project's usage of the service. Attempts to update a field not controlled by the caller will result in an access denied error. Operation The metadata field of the Operation will be a CompositeOperationMetadata object.

      Args:
        request: (ServicemanagementServicesProjectSettingsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method='PATCH',
        method_id='servicemanagement.services.projectSettings.patch',
        ordered_params=['serviceName', 'consumerProjectId'],
        path_params=['consumerProjectId', 'serviceName'],
        query_params=['excludeFinalQuotaSettingsInResponse', 'updateMask'],
        relative_path='v1/services/{serviceName}/projectSettings/{consumerProjectId}',
        request_field='projectSettings',
        request_type_name='ServicemanagementServicesProjectSettingsPatchRequest',
        response_type_name='Operation',
        supports_download=False,
    )

  class ServicesRolloutsService(base_api.BaseApiService):
    """Service class for the services_rollouts resource."""

    _NAME = 'services_rollouts'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesRolloutsService, self).__init__(client)
      self._upload_configs = {
          }

    def Create(self, request, global_params=None):
      r"""Creates a new service configuration rollout. Based on rollout, the Google Service Management will roll out the service configurations to different backend services. For example, the logging configuration will be pushed to Google Cloud Logging. Please note that any previous pending and running Rollouts and associated Operations will be automatically cancelled so that the latest Rollout will not be blocked by previous Rollouts. Only the 100 most recent (in any state) and the last 10 successful (if not already part of the set of 100 most recent) rollouts are kept for each service. The rest will be deleted eventually. Operation.

      Args:
        request: (ServicemanagementServicesRolloutsCreateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Create')
      return self._RunMethod(
          config, request, global_params=global_params)

    Create.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.rollouts.create',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['force'],
        relative_path='v1/services/{serviceName}/rollouts',
        request_field='rollout',
        request_type_name='ServicemanagementServicesRolloutsCreateRequest',
        response_type_name='Operation',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Gets a service configuration rollout.

      Args:
        request: (ServicemanagementServicesRolloutsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Rollout) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.rollouts.get',
        ordered_params=['serviceName', 'rolloutId'],
        path_params=['rolloutId', 'serviceName'],
        query_params=[],
        relative_path='v1/services/{serviceName}/rollouts/{rolloutId}',
        request_field='',
        request_type_name='ServicemanagementServicesRolloutsGetRequest',
        response_type_name='Rollout',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Lists the history of the service configuration rollouts for a managed service, from the newest to the oldest.

      Args:
        request: (ServicemanagementServicesRolloutsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ListServiceRolloutsResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.rollouts.list',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['filter', 'pageSize', 'pageToken'],
        relative_path='v1/services/{serviceName}/rollouts',
        request_field='',
        request_type_name='ServicemanagementServicesRolloutsListRequest',
        response_type_name='ListServiceRolloutsResponse',
        supports_download=False,
    )

  class ServicesService(base_api.BaseApiService):
    """Service class for the services resource."""

    _NAME = 'services'

    def __init__(self, client):
      super(ServicemanagementV1.ServicesService, self).__init__(client)
      self._upload_configs = {
          }

    def Create(self, request, global_params=None):
      r"""Creates a new managed service. A managed service is immutable, and is subject to mandatory 30-day data retention. You cannot move a service or recreate it within 30 days after deletion. One producer project can own no more than 500 services. For security and reliability purposes, a production service should be hosted in a dedicated producer project. Operation.

      Args:
        request: (ManagedService) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Create')
      return self._RunMethod(
          config, request, global_params=global_params)

    Create.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.create',
        ordered_params=[],
        path_params=[],
        query_params=[],
        relative_path='v1/services',
        request_field='<request>',
        request_type_name='ManagedService',
        response_type_name='Operation',
        supports_download=False,
    )

    def Delete(self, request, global_params=None):
      r"""Deletes a managed service. This method will change the service to the `Soft-Delete` state for 30 days. Within this period, service producers may call UndeleteService to restore the service. After 30 days, the service will be permanently deleted. Operation.

      Args:
        request: (ServicemanagementServicesDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method='DELETE',
        method_id='servicemanagement.services.delete',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=[],
        relative_path='v1/services/{serviceName}',
        request_field='',
        request_type_name='ServicemanagementServicesDeleteRequest',
        response_type_name='Operation',
        supports_download=False,
    )

    def GenerateConfigReport(self, request, global_params=None):
      r"""Generates and returns a report (errors, warnings and changes from existing configurations) associated with GenerateConfigReportRequest.new_value If GenerateConfigReportRequest.old_value is specified, GenerateConfigReportRequest will contain a single ChangeReport based on the comparison between GenerateConfigReportRequest.new_value and GenerateConfigReportRequest.old_value. If GenerateConfigReportRequest.old_value is not specified, this method will compare GenerateConfigReportRequest.new_value with the last pushed service configuration.

      Args:
        request: (GenerateConfigReportRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (GenerateConfigReportResponse) The response message.
      """
      config = self.GetMethodConfig('GenerateConfigReport')
      return self._RunMethod(
          config, request, global_params=global_params)

    GenerateConfigReport.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.generateConfigReport',
        ordered_params=[],
        path_params=[],
        query_params=[],
        relative_path='v1/services:generateConfigReport',
        request_field='<request>',
        request_type_name='GenerateConfigReportRequest',
        response_type_name='GenerateConfigReportResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Gets a managed service. Authentication is required unless the service is public.

      Args:
        request: (ServicemanagementServicesGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ManagedService) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.get',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['consumerProjectId', 'expand', 'view'],
        relative_path='v1/services/{serviceName}',
        request_field='',
        request_type_name='ServicemanagementServicesGetRequest',
        response_type_name='ManagedService',
        supports_download=False,
    )

    def GetConfig(self, request, global_params=None):
      r"""Gets a service configuration (version) for a managed service.

      Args:
        request: (ServicemanagementServicesGetConfigRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Service) The response message.
      """
      config = self.GetMethodConfig('GetConfig')
      return self._RunMethod(
          config, request, global_params=global_params)

    GetConfig.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.getConfig',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=['configId', 'view'],
        relative_path='v1/services/{serviceName}/config',
        request_field='',
        request_type_name='ServicemanagementServicesGetConfigRequest',
        response_type_name='Service',
        supports_download=False,
    )

    def GetIamPolicy(self, request, global_params=None):
      r"""Gets the access control policy for a resource. Returns an empty policy if the resource exists and does not have a policy set.

      Args:
        request: (ServicemanagementServicesGetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('GetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    GetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.getIamPolicy',
        ordered_params=['servicesId'],
        path_params=['servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}:getIamPolicy',
        request_field='getIamPolicyRequest',
        request_type_name='ServicemanagementServicesGetIamPolicyRequest',
        response_type_name='Policy',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Lists managed services. Returns all public services. For authenticated users, also returns all services the calling user has "servicemanagement.services.get" permission for.

      Args:
        request: (ServicemanagementServicesListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ListServicesResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method='GET',
        method_id='servicemanagement.services.list',
        ordered_params=[],
        path_params=[],
        query_params=['category', 'consumerId', 'consumerProjectId', 'pageSize', 'pageToken', 'producerProjectId'],
        relative_path='v1/services',
        request_field='',
        request_type_name='ServicemanagementServicesListRequest',
        response_type_name='ListServicesResponse',
        supports_download=False,
    )

    def SetIamPolicy(self, request, global_params=None):
      r"""Sets the access control policy on the specified resource. Replaces any existing policy. Can return `NOT_FOUND`, `INVALID_ARGUMENT`, and `PERMISSION_DENIED` errors.

      Args:
        request: (ServicemanagementServicesSetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('SetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    SetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.setIamPolicy',
        ordered_params=['servicesId'],
        path_params=['servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}:setIamPolicy',
        request_field='setIamPolicyRequest',
        request_type_name='ServicemanagementServicesSetIamPolicyRequest',
        response_type_name='Policy',
        supports_download=False,
    )

    def TestIamPermissions(self, request, global_params=None):
      r"""Returns permissions that a caller has on the specified resource. If the resource does not exist, this will return an empty set of permissions, not a `NOT_FOUND` error. Note: This operation is designed to be used for building permission-aware UIs and command-line tools, not for authorization checking. This operation may "fail open" without warning.

      Args:
        request: (ServicemanagementServicesTestIamPermissionsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TestIamPermissionsResponse) The response message.
      """
      config = self.GetMethodConfig('TestIamPermissions')
      return self._RunMethod(
          config, request, global_params=global_params)

    TestIamPermissions.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.testIamPermissions',
        ordered_params=['servicesId'],
        path_params=['servicesId'],
        query_params=[],
        relative_path='v1/services/{servicesId}:testIamPermissions',
        request_field='testIamPermissionsRequest',
        request_type_name='ServicemanagementServicesTestIamPermissionsRequest',
        response_type_name='TestIamPermissionsResponse',
        supports_download=False,
    )

    def Undelete(self, request, global_params=None):
      r"""Revives a previously deleted managed service. The method restores the service using the configuration at the time the service was deleted. The target service must exist and must have been deleted within the last 30 days. Operation.

      Args:
        request: (ServicemanagementServicesUndeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Operation) The response message.
      """
      config = self.GetMethodConfig('Undelete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Undelete.method_config = lambda: base_api.ApiMethodInfo(
        http_method='POST',
        method_id='servicemanagement.services.undelete',
        ordered_params=['serviceName'],
        path_params=['serviceName'],
        query_params=[],
        relative_path='v1/services/{serviceName}:undelete',
        request_field='',
        request_type_name='ServicemanagementServicesUndeleteRequest',
        response_type_name='Operation',
        supports_download=False,
    )
