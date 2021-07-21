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

"""Helper methods for record-sets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dns import rdatatype
from googlecloudsdk.api_lib.dns import import_util
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions


class UnsupportedRecordType(exceptions.Error):
  """Unsupported record-set type."""


def CreateRecordSetFromArgs(args, api_version='v1'):
  """Creates and returns a record-set from the given args.

  Args:
    args: The arguments to use to create the record-set.
    api_version: [str], the api version to use for creating the RecordSet.

  Raises:
    UnsupportedRecordType: If given record-set type is not supported

  Returns:
    ResourceRecordSet, the record-set created from the given args.
  """
  messages = apis.GetMessagesModule('dns', api_version)
  rd_type = rdatatype.from_text(args.type)
  if import_util.GetRdataTranslation(rd_type) is None:
    raise UnsupportedRecordType(
        'Unsupported record-set type [{0}]'.format(args.type))

  record_set = messages.ResourceRecordSet()
  # Need to assign kind to default value for useful equals comparisons.
  record_set.kind = record_set.kind
  record_set.name = util.AppendTrailingDot(args.name)
  record_set.ttl = args.ttl
  record_set.type = args.type

  if args.rrdatas:
    record_set.rrdatas = args.rrdatas
    if rd_type is rdatatype.TXT or rd_type is rdatatype.SPF:
      record_set.rrdatas = [
          import_util.QuotedText(datum) for datum in args.rrdatas
      ]

  elif args.routing_policy_type == 'WRR':
    record_set.routingPolicy = messages.RRSetRoutingPolicy(
        wrr=messages.RRSetRoutingPolicyWrrPolicy(items=[]))
    for policy_item in args.routing_policy_data:
      if rd_type is rdatatype.TXT or rd_type is rdatatype.SPF:
        policy_item['rrdatas'] = [
            import_util.QuotedText(datum) for datum in policy_item['rrdatas']
        ]
      record_set.routingPolicy.wrr.items.append(
          messages.RRSetRoutingPolicyWrrPolicyWrrPolicyItem(
              weight=float(policy_item['key']), rrdatas=policy_item['rrdatas']))

  elif args.routing_policy_type == 'GEO':
    record_set.routingPolicy = messages.RRSetRoutingPolicy(
        geo=messages.RRSetRoutingPolicyGeoPolicy(items=[]))
    for policy_item in args.routing_policy_data:
      if rd_type is rdatatype.TXT or rd_type is rdatatype.SPF:
        policy_item['rrdatas'] = [
            import_util.QuotedText(datum) for datum in policy_item['rrdatas']
        ]
      record_set.routingPolicy.geo.items.append(
          messages.RRSetRoutingPolicyGeoPolicyGeoPolicyItem(
              location=policy_item['key'], rrdatas=policy_item['rrdatas']))

  return record_set
