# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Helpers for tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages
from apitools.base.py import base_api

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import resource
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base
from googlecloudsdk.third_party.apis import apis_map
import mock


class Base(sdk_test_base.SdkBase):
  """Base class for tests of gcloud meta apis."""

  def MockAPIs(self, *mock_apis):
    """Mocks out the API list."""
    api_list = []
    api_map = {}
    for x in mock_apis:
      name, version, default = x
      client_mock = mock.MagicMock()
      client_mock.BASE_URL = 'https://{}.googleapis.com/'.format(name)
      api_list.append(registry.API(name, version, default, client_mock))
      api_map.setdefault(name, {})[version] = apis_map.APIDef(
          '', '', '', default)
      resources.REGISTRY.registered_apis[name] = [version]
    self.StartObjectPatch(registry, 'GetAllAPIs').return_value = api_list
    self.StartDictPatch('googlecloudsdk.third_party.apis.apis_map.MAP', api_map)

  def _FlatPath(self, collection_name, parent=False):
    parts = collection_name.split('.')
    if parent:
      parts = parts[:-1]
    flat_params = [p + 'Id' for p in parts]
    flat_path = '/'.join(['{p}/{{{p}Id}}'.format(p=p) for p in parts])
    return flat_params, flat_path

  def MockCollections(self, *collections):
    """Mocks out the foo v1 API to have mock collections."""
    mock_collections = {}
    all_collections = []
    for c in collections:
      full_collection_name, is_relative = c
      # pylint:disable=protected-access
      api_name, collection_name = registry._SplitFullCollectionName(
          full_collection_name)
      api_version = 'v1'
      base_url = 'https://{0}.googleapis.com/{1}/'.format(api_name, api_version)
      flat_params, flat_path = self._FlatPath(collection_name)

      if is_relative:
        collection = resource.CollectionInfo(
            api_name, api_version, base_url, 'https://cloud.google.com/docs',
            name=collection_name,
            path='{+name}',
            flat_paths={'': flat_path},
            params=['name'])
      else:
        collection = resource.CollectionInfo(
            api_name, api_version, base_url, 'https://cloud.google.com/docs',
            name=collection_name,
            path=flat_path,
            flat_paths={},
            params=flat_params)
      mock_collections.setdefault(api_name, {})
      mock_collections[api_name].setdefault(api_version, [])
      mock_collections[api_name][api_version].append(collection)
      all_collections.append(collection)
      # pylint:disable=protected-access
      try:
        resources.REGISTRY._RegisterCollection(collection)
      # It's OK if it's already registered.
      except resources.AmbiguousAPIException:
        pass
    self.MockAPIs(*[(c.api_name, c.api_version, True) for c in all_collections])
    collection_mock = self.StartObjectPatch(apis_internal, '_GetApiCollections')
    collection_mock.side_effect = lambda n, v: mock_collections[n][v]

  def MockGetListCreateMethods(self, *collections):
    """Mocks out the foo.projects.clusters to have get and list methods."""
    parent_collections = list(collections)
    for c in collections:
      full_collection_name, is_relative = c
      while full_collection_name.count('.') > 1:
        full_collection_name = full_collection_name.rsplit('.', 1)[0]
        parent_collections.append((full_collection_name, is_relative))
    self.MockCollections(*parent_collections)
    methods = {}
    for c in collections:
      full_collection_name, is_relative = c
      # pylint:disable=protected-access
      _, collection_name = registry._SplitFullCollectionName(
          full_collection_name)

      if is_relative:
        flat_params, flat_path = self._FlatPath(collection_name)
        get_method = base_api.ApiMethodInfo(
            flat_path='v1/' + flat_path,
            http_method='GET',
            method_id=full_collection_name + '.get',
            ordered_params=['name'],
            path_params=['name'],
            query_params=[],
            relative_path='v1/{+name}',
            request_field='',
            request_type_name='GetRequest',
            response_type_name='GetResponse',
            supports_download=False,
        )
        flat_params, flat_path = self._FlatPath(collection_name, parent=True)
        last_part = full_collection_name.split('.')[-1]
        create_method = base_api.ApiMethodInfo(
            flat_path='v1/' + flat_path + '/' + last_part,
            http_method='POST',
            method_id=full_collection_name + '.create',
            ordered_params=['parent'],
            path_params=['parent'],
            query_params=[],
            relative_path='v1/{+parent}/' + last_part,
            request_field=last_part[:-1],
            request_type_name='CreateRequest',
            response_type_name='CreateResponse',
            supports_download=False,
        )
        list_method = base_api.ApiMethodInfo(
            flat_path='v1/' + flat_path + '/' + last_part,
            http_method='GET',
            method_id=full_collection_name + '.list',
            ordered_params=['parent'],
            path_params=['parent'],
            query_params=['pageSize', 'pageToken'],
            relative_path='v1/{+parent}/' + last_part,
            request_field='',
            request_type_name='ListRequest',
            response_type_name='ListResponse',
            supports_download=False,
        )

      else:
        flat_params, flat_path = self._FlatPath(collection_name)
        get_method = base_api.ApiMethodInfo(
            http_method='GET',
            method_id=full_collection_name + '.get',
            ordered_params=flat_params,
            path_params=flat_params,
            query_params=[],
            relative_path=flat_path,
            request_field='',
            request_type_name='GetRequest',
            response_type_name='GetResponse',
            supports_download=False,
        )
        flat_params, flat_path = self._FlatPath(collection_name,
                                                parent=True)
        last_part = full_collection_name.split('.')[-1]
        create_method = base_api.ApiMethodInfo(
            http_method='POST',
            method_id=full_collection_name + '.create',
            ordered_params=flat_params,
            path_params=flat_params,
            query_params=[],
            relative_path=flat_path + '/' + last_part,
            request_field=last_part[:-1],
            request_type_name='CreateRequest',
            response_type_name='CreateResponse',
            supports_download=False,
        )
        list_method = base_api.ApiMethodInfo(
            http_method='GET',
            method_id=full_collection_name + '.list',
            ordered_params=flat_params,
            path_params=flat_params,
            query_params=['pageSize', 'pageToken'],
            relative_path=flat_path + '/' + last_part,
            request_field='',
            request_type_name='GetRequest',
            response_type_name='GetResponse',
            supports_download=False,
        )

      collection = registry.GetAPICollection(full_collection_name, 'v1')
      methods[full_collection_name] = [
          registry.APIMethod(self._CreateMockService(get_method), 'Get',
                             collection, get_method),
          registry.APIMethod(self._CreateMockService(get_method), 'Create',
                             collection, create_method),
          registry.APIMethod(self._CreateMockService(list_method), 'List',
                             collection, list_method),
      ]

    methods_mock = self.StartObjectPatch(registry, 'GetMethods')
    methods_mock.side_effect = lambda n, **kwargs: methods.get(n, [])

  def _CreateMockService(self, method_info):
    mock_service = mock.MagicMock()
    mock_service.GetRequestType.return_value = self.CreateRequestType(
        method_info.ordered_params + method_info.query_params)
    mock_service.GetResponseType.return_value = self._CreateResponseType(
        method_info)
    return mock_service

  def CreateRequestType(self, params):
    mock_fields = []
    message_object = mock.MagicMock()
    for p in params:
      setattr(message_object, p, None)
      mock_field = mock.MagicMock()
      mock_field.name = p
      mock_field.repeated = False
      mock_field.variant = messages.Variant.STRING
      mock_fields.append(mock_field)

    mock_type = mock.MagicMock()
    mock_type.return_value = message_object
    mock_type.all_fields.return_value = mock_fields
    message_object.all_fields.return_value = mock_fields
    fields_by_name = {f.name: f for f in mock_fields}
    def FieldsByName(name):
      return fields_by_name[name]
    mock_type.field_by_name.side_effect = FieldsByName
    message_object.field_by_name.side_effect = FieldsByName

    return mock_type

  def _CreateResponseType(self, method_info):
    mock_fields = []
    if method_info.method_id.endswith('.list'):
      mock_field = mock.MagicMock()
      mock_field.name = 'nextPageToken'
      mock_field.repeated = False
      mock_fields.append(mock_field)

      mock_field = mock.MagicMock()
      mock_field.name = 'items'
      mock_field.variant = messages.Variant.MESSAGE
      mock_field.repeated = True
      mock_fields.append(mock_field)
    mock_type = mock.MagicMock()
    mock_type.all_fields.return_value = mock_fields
    return mock_type


def main():
  return sdk_test_base.main()
