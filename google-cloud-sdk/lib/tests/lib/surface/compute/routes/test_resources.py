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
"""Resources that are shared by two or more tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis

messages = core_apis.GetMessagesModule('compute', 'v1')

_COMPUTE_PATH = 'https://compute.googleapis.com/compute'


def MakeRoutes(msgs, api, network='default'):
  prefix = _COMPUTE_PATH + '/' + api
  return [
      msgs.Route(
          destRange='10.0.0.0/8',
          name='route-1',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopIp='10.240.0.0',
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-1'),
      ),
      msgs.Route(
          destRange='0.0.0.0/0',
          name='route-2',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopInstance=(prefix + '/projects/my-project/'
                           'zones/zone-1/instances/instance-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-2'),
      ),
      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-3',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopGateway=(prefix + '/projects/my-project/'
                          'global/gateways/default-internet-gateway'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-3'),
          priority=1,
      ),
      msgs.Route(
          destRange='10.10.0.0/16',
          name='route-4',
          network=(prefix + '/projects/my-project/'
                   'network/' + network),
          nextHopVpnTunnel=(prefix + '/projects/my-project/'
                            'regions/region-1/vpnTunnels/tunnel-1'),
          selfLink=(prefix + '/projects/my-project/'
                    'global/routes/route-4'),
      ),
  ]


ROUTES_V1 = MakeRoutes(messages, 'v1')
ROUTES_V1_TWO_NETWORKS = ROUTES_V1 + MakeRoutes(messages, 'v1', network='foo')
