# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Testing resources for Cloud Filestore Instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
import six


def GetTestCloudFilestoreInstancesList():
  messages = filestore_client.GetMessages(filestore_client.ALPHA_API_VERSION)
  return [
      messages.Instance(name='Instance1'),
      messages.Instance(name='Instance2'),
  ]


def GetTestCloudFilestoreInstance():
  messages = filestore_client.GetMessages(filestore_client.ALPHA_API_VERSION)
  return messages.Instance(name='My Cloud Filestore Instance')


def GetFlagsFileFullPath(resource, args):
  """Returns the flags file in full path notation, for test purposes only.

  Args:
    resource:  An SdkBase.Resource test object used for getting the code
      executed path.
    args: A list of strings.

  Returns:
    The full path to the json/yaml flags file as a string.
    Updates the args flags file running full path (Run time varied).
  """

  testdata_dir = resource('tests', 'unit', 'surface', 'filestore', 'instances',
                          'testdata')
  for arg in args:
    if arg is None:
      continue
    index = arg.find('flags-file')
    if index > 0:
      flags_file_name = arg[(index + len('flags-file') + 1):]
      test_data_file = os.path.join(testdata_dir, flags_file_name)
      # modifying the args list with the expectation that the loop will exit.
      args.remove(arg)
      args.append('--flags-file={}'.format(test_data_file))
      return test_data_file


def LoadFlagsFile(flags_file):
  """Loads a Flagsfile test file, either JSON or YAML.

  Args:
      flags_file: string, flags file full path.

  Returns:
      Decoded object from JSON or YAML.
  """
  file_share = LoadJson(flags_file)
  if file_share is None:
    file_share = LoadYaml(flags_file)
    if file_share is None:
      return None
  return file_share


def ReturnTier(args):
  tier = 'BASIC_HDD'
  for arg in args:
    index = arg.find('tier')
    if index > 0:
      tier = arg[index + len('tier') + 1:]
  return tier


def ReturnDescription(args):
  description = None
  for arg in args:
    index = arg.find('description')
    if index > 0:
      description = arg[index + len('description') + 1:]
  return description


def ReturnLabels(args):
  labels = None
  for arg in args:
    index = arg.find('labels')
    if index > 0:
      labels = arg[index + len('labels') + 1:]
  return labels


def LoadJson(file_name):
  """Loads a JSON file.

  Args:
      file_name: string, flags file full path.

  Returns:
      Decoded object from JSON.
  """
  data = None
  try:
    json_parse_exception = json.decoder.JSONDecodeError
  except AttributeError:  # Python 2
    json_parse_exception = ValueError
  try:
    with open(file_name) as json_file:
      data = json.load(json_file)
  except json_parse_exception as err:
    log.error('Json File {} decode failed: {}'.format(json_file, err))
    return None
  return data


def LoadYaml(file_name):
  """Loads a YAML file.

  Args:
      file_name: string, flags file full path.

  Returns:
      Decoded object from YAML.
  """
  data = None
  try:
    with open(file_name) as yaml_file:
      data = yaml.load(yaml_file)
  except yaml.YAMLError as err:
    log.error('YAML File {} decode failed: {}'.format(yaml_file, err))
    return None
  return data


def MakeFileShareConfigMsg(messages, config):
  """Creates a Fileshare configuration message.

  Args:
      messages: The messages module.
      config: Dict, Fileshare config.

  Returns:
      File share config message populate with values.
  """
  if config.get('source-snapshot', None):
    return messages.FileShareConfig(
        capacityGb=config.get('capacity', None),
        name=config.get('name', None),
        sourceSnapshot=config.get('source-snapshot', None),
        nfsExportOptions=config.get('nfs-export-options', None))
  return messages.FileShareConfig(
      capacityGb=config.get('capacity', None),
      name=config.get('name', None),
      nfsExportOptions=config.get('nfs-export-options', None))


def MakeFileShareConfig(messages, name, capacity, source_snapshot,
                        nfs_export_options):
  """Creates a Fileshare configuration.

  Args:
      messages: The messages module.
      name: String, the FileShare name.
      capacity: Int, The Fileshare size in GB units.
      source_snapshot: String, A snapshot path reflecting a backup of the source
        instance.
      nfs_export_options: list, containing NfsExportOptions dictionaries.

  Returns:
      File share config message populate with values.
  """

  message_args = dict(
      capacityGb=capacity,
      name=name,
      sourceSnapshot=source_snapshot,
      nfsExportOptions=nfs_export_options)

  return [messages.FileShareConfig(**message_args)]


def MakeNFSExportOptionsMsg(messages, nfs_export_options):
  """Creates an NfsExportOptions message.

  Args:
      messages: The messages module.
      nfs_export_options: list, containing NfsExportOptions dictionaries.

  Returns:
      File share message populate with values, filled with defaults.
      In case no nfs export options are provided we rely on the API to apply a
      default.
  """
  client = filestore_client.FilestoreClient
  args = dict(messages=messages, nfs_export_options=nfs_export_options)
  return client.MakeNFSExportOptionsMsg(**args)


def CreateFileShareConfig(messages, flags_file, expected_vol_name,
                          expected_capacity, expected_source_snapshot,
                          expected_nfs_export_options):
  """Creates a Filestore instance skeleton .

  Args:
    messages: The messages module.
    flags_file: string, flags file name.
    expected_vol_name: string, test result expected volume name.
    expected_capacity: int, test result expected capacity.
    expected_source_snapshot: string, test result expected source snapshot.
    expected_nfs_export_options: list, test result expected NfsExportOptions.

  Returns:
    File share configuration.
  """
  flags_file_data = None
  file_share_data = {}
  if flags_file:
    flags_file_data = LoadFlagsFile(flags_file)
    flags_file_nfs_export_options = ReturnNfsExportOptions(flags_file_data)
    CleanFileShare(flags_file_data)
  if flags_file_data and '--file-share' in flags_file_data:
    file_share_data = flags_file_data['--file-share']
    nfs_export_configs = MakeNFSExportOptionsMsg(
        messages, nfs_export_options=flags_file_nfs_export_options)
  else:
    nfs_export_configs = MakeNFSExportOptionsMsg(
        messages, nfs_export_options=expected_nfs_export_options)
  FillFileShare(
      file_share_data=file_share_data,
      expected_vol_name=expected_vol_name,
      expected_capacity=expected_capacity,
      expected_source_snapshot=expected_source_snapshot,
      nfs_export_configs=nfs_export_configs)

  return file_share_data


def FillFileShare(file_share_data, expected_vol_name, expected_capacity,
                  expected_source_snapshot, nfs_export_configs):
  """Fill an expected file share result with config from the file_share_data.

  or manually from expected_* expected test result values.

  Args:
    file_share_data: string, flags file name.
    expected_vol_name: string, test result expected volume name.
    expected_capacity: int, test result expected capacity.
    expected_source_snapshot: string, test result expected source snapshot.
    nfs_export_configs: list, test result  NfsExportOptions.
  """
  if file_share_data.get('name', None) is None:
    file_share_data['name'] = expected_vol_name
  if file_share_data.get('capacity', None) is None:
    file_share_data['capacity'] = expected_capacity
  else:
    file_share_data['capacity'] = int(file_share_data['capacity'])
  file_share_data['source-snapshot'] = expected_source_snapshot
  if file_share_data.get('nfs-export-options', None) is None:
    file_share_data['nfs-export-options'] = nfs_export_configs


def ExpectCreateInstance(messages, mock_client, parent, name, op_name, config):
  mock_client.projects_locations_instances.Create.Expect(
      messages.FileProjectsLocationsInstancesCreateRequest(
          parent=parent, instanceId=name, instance=config),
      messages.Operation(name=op_name))


def CreateFileShareInstance(messages, tier, expected_network, expected_labels,
                            expected_range, expected_description):
  """Creates a Filestore instance skeleton .

  Args:
    messages: The messages module.
    tier: enum, File store tier.
    expected_network: string, test result expected network.
    expected_labels: dict, test result expected labels.
    expected_range: list, test result expected ip-range.
    expected_description: string, test result test description.

  Returns:
    File store instance message.
  """
  if expected_labels:
    return messages.Instance(
        tier=messages.Instance.TierValueValuesEnum.lookup_by_name(tier),
        description=expected_description,
        labels=MakeLabels(messages, expected_labels),
        networks=MakeNetworkConfig(messages, expected_network, expected_range))
  else:
    return messages.Instance(
        tier=messages.Instance.TierValueValuesEnum.lookup_by_name(tier),
        description=expected_description,
        networks=MakeNetworkConfig(messages, expected_network, expected_range))


def ReturnNfsExportOptions(flags_file_data):
  nfs_export_options = []
  if flags_file_data.get('--file-share', None):
    if flags_file_data['--file-share'].get('nfs-export-options', None):
      nfs_export_options = flags_file_data['--file-share']['nfs-export-options']
  return nfs_export_options


def CleanFileShare(flags_file_data):
  if flags_file_data.get('--file-share', None):
    if flags_file_data['--file-share'].get('nfs-export-options', None):
      flags_file_data['--file-share'].pop('nfs-export-options')


def MakeLabels(messages, labels_dict):
  return messages.Instance.LabelsValue(additionalProperties=[
      messages.Instance.LabelsValue.AdditionalProperty(key=key, value=value)
      for (key, value) in six.iteritems(labels_dict)
  ])


def MakeNetworkConfig(messages, network, range_=None):
  return [messages.NetworkConfig(network=network, reservedIpRange=range_)]


def AddInstanceFileShare(instance, file_shares):
  instance.fileShares = file_shares


def InstanceAddFileShareConfig(messages, instance, file_share_config):
  """Populates a Filestore instance with Fileshare message."""

  if isinstance(file_share_config, list):
    file_shares = []
    for instance_file_share_config in file_share_config:
      file_shares.add(
          MakeFileShareConfigMsg(messages, instance_file_share_config))
    AddInstanceFileShare(instance, file_shares)
  else:
    AddInstanceFileShare(instance,
                         [MakeFileShareConfigMsg(messages, file_share_config)])
