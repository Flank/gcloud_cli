# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Resource definitions for cloud platform apis."""

import enum


BASE_URL = 'https://apigee.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/apigee-api-management/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  ORGANIZATIONS = (
      'organizations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIPRODUCTS = (
      'organizations.apiproducts',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apiproducts/{apiproductsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIPRODUCTS_ATTRIBUTES = (
      'organizations.apiproducts.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apiproducts/{apiproductsId}/'
              'attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIS = (
      'organizations.apis',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apis/{apisId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APIS_REVISIONS = (
      'organizations.apis.revisions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apis/{apisId}/revisions/'
              '{revisionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_APPS = (
      'organizations.apps',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/apps/{appsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS = (
      'organizations.developers',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS = (
      'organizations.developers.apps',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS_ATTRIBUTES = (
      'organizations.developers.apps.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}/attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_APPS_KEYS = (
      'organizations.developers.apps.keys',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'apps/{appsId}/keys/{keysId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_DEVELOPERS_ATTRIBUTES = (
      'organizations.developers.attributes',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/developers/{developersId}/'
              'attributes/{attributesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS = (
      'organizations.environments',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS = (
      'organizations.environments.apis',
      'organizations/{organizationsId}/environments/{environmentsId}/apis/'
      '{apisId}',
      {},
      ['organizationsId', 'environmentsId', 'apisId'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS = (
      'organizations.environments.apis.revisions',
      'organizations/{organizationsId}/environments/{environmentsId}/apis/'
      '{apisId}/revisions/{revisionsId}',
      {},
      ['organizationsId', 'environmentsId', 'apisId', 'revisionsId'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS_DEBUGSESSIONS = (
      'organizations.environments.apis.revisions.debugsessions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'apis/{apisId}/revisions/{revisionsId}/debugsessions/'
              '{debugsessionsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_APIS_REVISIONS_DEBUGSESSIONS_DATA = (
      'organizations.environments.apis.revisions.debugsessions.data',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'apis/{apisId}/revisions/{revisionsId}/debugsessions/'
              '{debugsessionsId}/data/{dataId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_FLOWHOOKS = (
      'organizations.environments.flowhooks',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'flowhooks/{flowhooksId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYSTORES = (
      'organizations.environments.keystores',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'keystores/{keystoresId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_KEYSTORES_ALIASES = (
      'organizations.environments.keystores.aliases',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'keystores/{keystoresId}/aliases/{aliasesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_OPTIMIZEDSTATS = (
      'organizations.environments.optimizedStats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'optimizedStats/{optimizedStatsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_QUERIES = (
      'organizations.environments.queries',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'queries/{queriesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_REFERENCES = (
      'organizations.environments.references',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'references/{referencesId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_RESOURCEFILES = (
      'organizations.environments.resourcefiles',
      '{+parent}/resourcefiles/{type}/{name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'resourcefiles/{type}/{name}',
      },
      ['parent', 'type', 'name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_STATS = (
      'organizations.environments.stats',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'stats/{statsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_ENVIRONMENTS_TARGETSERVERS = (
      'organizations.environments.targetservers',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/environments/{environmentsId}/'
              'targetservers/{targetserversId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_OPERATIONS = (
      'organizations.operations',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_REPORTS = (
      'organizations.reports',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/reports/{reportsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SHAREDFLOWS = (
      'organizations.sharedflows',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sharedflows/{sharedflowsId}',
      },
      ['name'],
      True
  )
  ORGANIZATIONS_SHAREDFLOWS_REVISIONS = (
      'organizations.sharedflows.revisions',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/sharedflows/{sharedflowsId}/'
              'revisions/{revisionsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
