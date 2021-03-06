# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""JSON-based KubeRun backend binding wrapper."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import kubernetesobject
from googlecloudsdk.api_lib.kuberun import mapobject


class BackendBinding(kubernetesobject.KubernetesObject):
  """Wraps JSON-based dict object of a backend binding."""

  @property
  def service(self):
    return self._props['spec']['targetService']

  @property
  def ready(self):
    for c in self._props['status']['conditions']:
      if c['type'] == 'Ready':
        return c['status']
    return 'UNKNOWN'


class ResourceRecord(mapobject.MapObject):
  """Wraps JSON-based dict object of a resource record of a domain mapping."""

  @property
  def type(self):
    return self._props['type']

  @property
  def rrdata(self):
    return self._props['rrdata']

  @property
  def name(self):
    return self._props.get('name')

  @name.setter
  def name(self, n):
    self._props['name'] = n
