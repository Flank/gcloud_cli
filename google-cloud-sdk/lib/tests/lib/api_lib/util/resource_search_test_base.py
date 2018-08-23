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

"""Base class for CloudResourceSearch unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base

from six.moves import range  # pylint: disable=redefined-builtin


def _MakeScheduling():
  return extra_types.JsonValue(
      object_value=extra_types.JsonObject(
          properties=[
              extra_types.JsonObject.Property(
                  key='automaticRestart',
                  value=extra_types.JsonValue(
                      boolean_value=True,
                  ),
              ),
              extra_types.JsonObject.Property(
                  key='preemptible',
                  value=extra_types.JsonValue(
                      boolean_value=False,
                  ),
              ),
              extra_types.JsonObject.Property(
                  key='onHostMaintenance',
                  value=extra_types.JsonValue(
                      string_value='MIGRATE',
                  ),
              ),
          ],
      ),
  )


def _MakeDisk(parameters):
  disk_url = (
      'https://www.googleapis.com/compute/{track}/projects/{project}'
      '/zones/{zone}/disks/{name}'.format(**parameters))
  license_url = (
      'https://www.googleapis.com/compute/{track}/projects/debian-cloud'
      '/global/licenses/debian-8-jessie'.format(**parameters))

  return extra_types.JsonValue(
      array_value=extra_types.JsonArray(
          entries=[
              extra_types.JsonValue(
                  object_value=extra_types.JsonObject(
                      properties=[
                          extra_types.JsonObject.Property(
                              key='index',
                              value=extra_types.JsonValue(
                                  integer_value=0,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='license',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=[
                                          extra_types.JsonValue(
                                              string_value=license_url,
                                          ),
                                      ],
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='autoDelete',
                              value=extra_types.JsonValue(
                                  boolean_value=True,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='deviceName',
                              value=extra_types.JsonValue(
                                  string_value='persistent-disk-0',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='boot',
                              value=extra_types.JsonValue(
                                  boolean_value=True,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='source',
                              value=extra_types.JsonValue(
                                  string_value=disk_url,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='mode',
                              value=extra_types.JsonValue(
                                  string_value='READ_WRITE',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='interface',
                              value=extra_types.JsonValue(
                                  string_value='SCSI',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='type',
                              value=extra_types.JsonValue(
                                  string_value='PERSISTENT',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='diskSizeGb',
                              value=extra_types.JsonValue(
                                  string_value='0',
                              ),
                          ),
                      ],
                  ),
              ),
          ],
      ),
  )


def _MakeServiceAccountScopes():
  return [
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/devstorage.read_only',
      ),
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/logging.write',
      ),
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/monitoring.write',
      ),
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/pubsub',
      ),
      extra_types.JsonValue(
          string_value=(
              'https://www.googleapis.com/auth/service.management.readonly'),
      ),
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/servicecontrol',
      ),
      extra_types.JsonValue(
          string_value='https://www.googleapis.com/auth/trace.append',
      ),
  ]


def _MakeServiceAccount():
  return extra_types.JsonValue(
      array_value=extra_types.JsonArray(
          entries=[
              extra_types.JsonValue(
                  object_value=extra_types.JsonObject(
                      properties=[
                          extra_types.JsonObject.Property(
                              key='scope',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=_MakeServiceAccountScopes(),
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='email',
                              value=extra_types.JsonValue(
                                  string_value='bozo@big.top',
                              ),
                          ),
                      ],
                  ),
              ),
          ],
      ),
  )


def _MakeAccessConfigEntries():
  return [
      extra_types.JsonValue(
          object_value=extra_types.JsonObject(
              properties=[
                  extra_types.JsonObject.Property(
                      key='externalIp',
                      value=extra_types.JsonValue(
                          string_value='',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='name',
                      value=extra_types.JsonValue(
                          string_value='external-nat',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='publicDnsName',
                      value=extra_types.JsonValue(
                          string_value='',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='setPublicDns',
                      value=extra_types.JsonValue(
                          boolean_value=False,
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='networkTier',
                      value=extra_types.JsonValue(
                          string_value='INVALID_NETWORK_TIER',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='setPublicPtr',
                      value=extra_types.JsonValue(
                          boolean_value=False,
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='type',
                      value=extra_types.JsonValue(
                          string_value='ONE_TO_ONE_NAT',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key='publicPtrDomainName',
                      value=extra_types.JsonValue(
                          string_value=''),
                  ),
              ],
          ),
      ),
  ]


def _MakeNetworkInterface(parameters):
  return extra_types.JsonValue(
      array_value=extra_types.JsonArray(
          entries=[
              extra_types.JsonValue(
                  object_value=extra_types.JsonObject(
                      properties=[
                          extra_types.JsonObject.Property(
                              key='network',
                              value=extra_types.JsonValue(
                                  string_value=(
                                      'https://www.googleapis.com/compute'
                                      '/{track}/projects/{project}/global'
                                      '/networks/default'.format(**parameters)),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='accessConfig',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=_MakeAccessConfigEntries(),
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='aliasIpRange',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=[],
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='fingerprint',
                              value=extra_types.JsonValue(
                                  string_value='',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='subnetwork',
                              value=extra_types.JsonValue(
                                  string_value='',),
                          ),
                          extra_types.JsonObject.Property(
                              key='ipAddress',
                              value=extra_types.JsonValue(
                                  string_value='',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key='name',
                              value=extra_types.JsonValue(
                                  string_value='nic0',
                              ),
                          ),
                      ],
                  ),
              ),
          ],
      ),
  )


def _MakeAdditionalProperties(messages, parameters):
  return [
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='status',
          value=extra_types.JsonValue(
              string_value='PROVISIONING',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='labels',
          value=extra_types.JsonValue(
              object_value=extra_types.JsonObject(
                  properties=[],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='minCpuPlatform',
          value=extra_types.JsonValue(
              string_value='',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='scheduling',
          value=_MakeScheduling(),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='canIpForward',
          value=extra_types.JsonValue(
              boolean_value=False,
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='disk',
          value=_MakeDisk(parameters),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='creationTimestamp',
          value=extra_types.JsonValue(
              string_value='2017-05-10T10:56:17.853-07:00',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='id',
          value=extra_types.JsonValue(
              string_value='6131310587503635118',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='startRestricted',
          value=extra_types.JsonValue(
              boolean_value=False,
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='zone',
          value=extra_types.JsonValue(
              string_value=(
                  'https://www.googleapis.com/compute/{track}/projects'
                  '/{project}/zones/{zone}'.format(**parameters)),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='serviceAccount',
          value=_MakeServiceAccount(),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='networkInterface',
          value=_MakeNetworkInterface(parameters),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='statusMessage',
          value=extra_types.JsonValue(
              string_value='',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='cpuPlatform',
          value=extra_types.JsonValue(
              string_value='Unknown CPU Platform',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='machineType',
          value=extra_types.JsonValue(
              string_value=(
                  'https://www.googleapis.com/compute{track}beta/projects'
                  '/{project}/zones/{zone}/machineTypes/n1-standard-1'
                  .format(**parameters)),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='description',
          value=extra_types.JsonValue(
              string_value='',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='tags',
          value=extra_types.JsonValue(
              object_value=extra_types.JsonObject(
                  properties=[
                      extra_types.JsonObject.Property(
                          key='tag',
                          value=extra_types.JsonValue(
                              array_value=extra_types.JsonArray(
                                  entries=[],
                              ),
                          ),
                      ),
                      extra_types.JsonObject.Property(
                          key='fingerprint',
                          value=extra_types.JsonValue(
                              string_value='42WmSpB8rSM=',
                          ),
                      ),
                  ],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='labelFingerprint',
          value=extra_types.JsonValue(
              string_value='42WmSpB8rSM=',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='host',
          value=extra_types.JsonValue(
              string_value='',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='guestAccelerator',
          value=extra_types.JsonValue(
              array_value=extra_types.JsonArray(
                  entries=[],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='name',
          value=extra_types.JsonValue(
              string_value='{name}'.format(**parameters),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='@type',
          value=extra_types.JsonValue(
              string_value='type.googleapis.com/compute.Instance',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key='selfLink',
          value=extra_types.JsonValue(
              string_value=(
                  'https://www.googleapis.com/compute/{track}/projects'
                  '/{project}/zones/{zone}/instances/{name}'
                  .format(**parameters)),
          ),
      ),
  ]


def _MakeResourceSearchResult(messages, prefix='test', suffix='1', track='beta',
                              version='v1'):
  """Creates and returns a single CloudResourceSearch result item."""
  parameters = {
      'name': '{prefix}-name-{suffix}'.format(prefix=prefix, suffix=suffix),
      'project': '{prefix}-project-{suffix}'.format(
          prefix=prefix, suffix=suffix),
      'region': '{prefix}-region-{suffix}'.format(prefix=prefix, suffix=suffix),
      'track': track,
      'version': version,
      'zone': '{prefix}-zone-{suffix}'.format(prefix=prefix, suffix=suffix),
  }
  # pylint: disable=line-too-long
  return messages.SearchResult(
      discoveryType='Instance',
      discoveryUrl=(
          'https://www.googleapis.com/discovery/v1/apis/compute'
          '/{track}/rest'.format(**parameters)),
      resource=messages.SearchResult.ResourceValue(
          additionalProperties=_MakeAdditionalProperties(messages, parameters)),
      resourceName=(
          '//compute.googleapis.com/projects/{project}/zones/{zone}'
          '/instances/{name}'.format(**parameters)),
      resourceType='type.googleapis.com/compute.Instance',
      resourceUrl=(
          'https://www.googleapis.com/compute/{track}/projects'
          '/{project}/zones/{zone}/instances/{name}'.format(**parameters)),
  )


class ResourceSearchTestBase(cli_test_base.CliTestBase,
                             sdk_test_base.WithFakeAuth):
  """A base class for CloudResourceSearch unit tests."""

  def SetUp(self):
    self.client = mock.Client(apis.GetClientClass('cloudresourcesearch', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = self.client.MESSAGES_MODULE

  def ResourceSearchResult(self, prefix='test', suffix='1', track='beta',
                           version='v1'):
    return _MakeResourceSearchResult(
        self.messages, prefix=prefix, suffix=suffix, track=track)

  def ResourceSearchResults(self, count=1, prefix='test', suffix='1',
                            track='beta', version='v1'):
    return [_MakeResourceSearchResult(self.messages, prefix=prefix,
                                      suffix=index, track=track,
                                      version=version)
            for index in range(0, count)]
