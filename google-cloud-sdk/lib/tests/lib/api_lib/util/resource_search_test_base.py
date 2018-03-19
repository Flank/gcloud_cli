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

from apitools.base.py import extra_types
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


def _MakeScheduling():
  return extra_types.JsonValue(
      object_value=extra_types.JsonObject(
          properties=[
              extra_types.JsonObject.Property(
                  key=u'automaticRestart',
                  value=extra_types.JsonValue(
                      boolean_value=True,
                  ),
              ),
              extra_types.JsonObject.Property(
                  key=u'preemptible',
                  value=extra_types.JsonValue(
                      boolean_value=False,
                  ),
              ),
              extra_types.JsonObject.Property(
                  key=u'onHostMaintenance',
                  value=extra_types.JsonValue(
                      string_value=u'MIGRATE',
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
                              key=u'index',
                              value=extra_types.JsonValue(
                                  integer_value=0,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'license',
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
                              key=u'autoDelete',
                              value=extra_types.JsonValue(
                                  boolean_value=True,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'deviceName',
                              value=extra_types.JsonValue(
                                  string_value=u'persistent-disk-0',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'boot',
                              value=extra_types.JsonValue(
                                  boolean_value=True,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'source',
                              value=extra_types.JsonValue(
                                  string_value=disk_url,
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'mode',
                              value=extra_types.JsonValue(
                                  string_value=u'READ_WRITE',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'interface',
                              value=extra_types.JsonValue(
                                  string_value=u'SCSI',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'type',
                              value=extra_types.JsonValue(
                                  string_value=u'PERSISTENT',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'diskSizeGb',
                              value=extra_types.JsonValue(
                                  string_value=u'0',
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
          string_value=(
              'https://www.googleapis.com/auth/cloud.useraccounts.readonly'),
      ),
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
                              key=u'scope',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=_MakeServiceAccountScopes(),
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'email',
                              value=extra_types.JsonValue(
                                  string_value=u'bozo@big.top',
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
                      key=u'externalIp',
                      value=extra_types.JsonValue(
                          string_value=u'',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'name',
                      value=extra_types.JsonValue(
                          string_value=u'external-nat',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'publicDnsName',
                      value=extra_types.JsonValue(
                          string_value=u'',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'setPublicDns',
                      value=extra_types.JsonValue(
                          boolean_value=False,
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'networkTier',
                      value=extra_types.JsonValue(
                          string_value=u'INVALID_NETWORK_TIER',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'setPublicPtr',
                      value=extra_types.JsonValue(
                          boolean_value=False,
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'type',
                      value=extra_types.JsonValue(
                          string_value=u'ONE_TO_ONE_NAT',
                      ),
                  ),
                  extra_types.JsonObject.Property(
                      key=u'publicPtrDomainName',
                      value=extra_types.JsonValue(
                          string_value=u''),
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
                              key=u'network',
                              value=extra_types.JsonValue(
                                  string_value=(
                                      'https://www.googleapis.com/compute'
                                      '/{track}/projects/{project}/global'
                                      '/networks/default'.format(**parameters)),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'accessConfig',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=_MakeAccessConfigEntries(),
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'aliasIpRange',
                              value=extra_types.JsonValue(
                                  array_value=extra_types.JsonArray(
                                      entries=[],
                                  ),
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'fingerprint',
                              value=extra_types.JsonValue(
                                  string_value=u'',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'subnetwork',
                              value=extra_types.JsonValue(
                                  string_value=u'',),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'ipAddress',
                              value=extra_types.JsonValue(
                                  string_value=u'',
                              ),
                          ),
                          extra_types.JsonObject.Property(
                              key=u'name',
                              value=extra_types.JsonValue(
                                  string_value=u'nic0',
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
          key=u'status',
          value=extra_types.JsonValue(
              string_value=u'PROVISIONING',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'labels',
          value=extra_types.JsonValue(
              object_value=extra_types.JsonObject(
                  properties=[],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'minCpuPlatform',
          value=extra_types.JsonValue(
              string_value=u'',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'scheduling',
          value=_MakeScheduling(),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'canIpForward',
          value=extra_types.JsonValue(
              boolean_value=False,
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'disk',
          value=_MakeDisk(parameters),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'creationTimestamp',
          value=extra_types.JsonValue(
              string_value=u'2017-05-10T10:56:17.853-07:00',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'id',
          value=extra_types.JsonValue(
              string_value=u'6131310587503635118',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'startRestricted',
          value=extra_types.JsonValue(
              boolean_value=False,
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'zone',
          value=extra_types.JsonValue(
              string_value=(
                  'https://www.googleapis.com/compute/{track}/projects'
                  '/{project}/zones/{zone}'.format(**parameters)),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'serviceAccount',
          value=_MakeServiceAccount(),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'networkInterface',
          value=_MakeNetworkInterface(parameters),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'statusMessage',
          value=extra_types.JsonValue(
              string_value=u'',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'cpuPlatform',
          value=extra_types.JsonValue(
              string_value=u'Unknown CPU Platform',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'machineType',
          value=extra_types.JsonValue(
              string_value=(
                  'https://www.googleapis.com/compute{track}beta/projects'
                  '/{project}/zones/{zone}/machineTypes/n1-standard-1'
                  .format(**parameters)),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'description',
          value=extra_types.JsonValue(
              string_value=u'',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'tags',
          value=extra_types.JsonValue(
              object_value=extra_types.JsonObject(
                  properties=[
                      extra_types.JsonObject.Property(
                          key=u'tag',
                          value=extra_types.JsonValue(
                              array_value=extra_types.JsonArray(
                                  entries=[],
                              ),
                          ),
                      ),
                      extra_types.JsonObject.Property(
                          key=u'fingerprint',
                          value=extra_types.JsonValue(
                              string_value=u'42WmSpB8rSM=',
                          ),
                      ),
                  ],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'labelFingerprint',
          value=extra_types.JsonValue(
              string_value=u'42WmSpB8rSM=',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'host',
          value=extra_types.JsonValue(
              string_value=u'',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'guestAccelerator',
          value=extra_types.JsonValue(
              array_value=extra_types.JsonArray(
                  entries=[],
              ),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'name',
          value=extra_types.JsonValue(
              string_value=u'{name}'.format(**parameters),
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'@type',
          value=extra_types.JsonValue(
              string_value=u'type.googleapis.com/compute.Instance',
          ),
      ),
      messages.SearchResult.ResourceValue.AdditionalProperty(
          key=u'selfLink',
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
      discoveryType=u'Instance',
      discoveryUrl=(
          'https://www.googleapis.com/discovery/v1/apis/compute'
          '/{track}/rest'.format(**parameters)),
      resource=messages.SearchResult.ResourceValue(
          additionalProperties=_MakeAdditionalProperties(messages, parameters)),
      resourceName=(
          '//compute.googleapis.com/projects/{project}/zones/{zone}'
          '/instances/{name}'.format(**parameters)),
      resourceType=u'type.googleapis.com/compute.Instance',
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
