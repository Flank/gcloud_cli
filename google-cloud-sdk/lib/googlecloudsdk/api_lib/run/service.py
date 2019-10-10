# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Wraps a Serverless Service message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import traffic


ENDPOINT_VISIBILITY = 'serving.knative.dev/visibility'
CLUSTER_LOCAL = 'cluster-local'


class Service(k8s_object.KubernetesObject):
  """Wraps a Serverless Service message, making fields more convenient.

  Setting properties on a Service (where possible) writes through to the
  nested Kubernetes-style fields.
  """
  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Service'
  # Field names that are present in Cloud Run messages, but should not be
  # initialized because they aren't supported by the control plane yet.
  FIELD_BLACKLIST = ['manual', 'release', 'template']

  @classmethod
  def New(cls, client, namespace):
    """Produces a new Service object.

    Args:
      client: The Cloud Run API client.
      namespace: str, The serving namespace.

    Returns:
      A new Service object to be deployed.
    """
    ret = super(Service, cls).New(client, namespace)
    # We're in oneOf territory, set the other to None for now.
    ret.spec.pinned = None

    # Unset a pile of unused things on the container.
    ret.configuration.container.lifecycle = None
    ret.configuration.container.livenessProbe = None
    ret.configuration.container.readinessProbe = None
    ret.configuration.container.resources = None
    ret.configuration.container.securityContext = None
    return ret

  def _EnsureRevisionMeta(self):
    revision_meta = self.spec.revisionTemplate.metadata
    if revision_meta is None:
      revision_meta = self._messages.ObjectMeta()
      self.spec.revisionTemplate.metadata = revision_meta
    return revision_meta

  @property
  def configuration(self):
    """Configuration (configuration.Configuration) of the service, if any."""
    options = (self._m.spec.pinned, self._m.spec.runLatest)
    ret = next((o.configuration for o in options if o is not None), None)
    if ret:
      return configuration.Configuration.SpecOnly(ret, self._messages)
    return None

  @property
  def template(self):
    if self.configuration:
      return self.configuration.template
    else:
      ret = revision.Revision.Template(
          self.spec.template, self.MessagesModule())
      if not ret.metadata:
        ret.metadata = self.MessagesModule().ObjectMeta()
      return ret

  @property
  def revision_labels(self):
    return self.template.labels

  @property
  def latest_created_revision(self):
    return self.status.latestCreatedRevisionName

  @property
  def latest_ready_revision(self):
    return self.status.latestReadyRevisionName

  @property
  def serving_revisions(self):
    return [t.revisionName for t in self.status.traffic if t.percent]

  @property
  def domain(self):
    return self._m.status.url or self._m.status.domain

  @domain.setter
  def domain(self, domain):
    self._m.status.url = self._m.status.domain = domain

  @property
  def ready_symbol(self):
    if (self.ready is False and  # pylint: disable=g-bool-id-comparison
        self.latest_ready_revision and
        self.latest_created_revision != self.latest_ready_revision):
      return '!'
    return super(Service, self).ready_symbol

  @property
  def last_modifier(self):
    return self.annotations.get(u'serving.knative.dev/lastModifier')

  @property
  def last_transition_time(self):
    return next((c.lastTransitionTime
                 for c in self.status.conditions
                 if c.type == u'Ready'), None)

  @property
  def traffic(self):
    self.AssertFullObject()
    return traffic.TrafficTargets(self._messages, self.spec.traffic)

  @property
  def vpc_connector(self):
    return self.annotations.get(u'run.googleapis.com/vpc-access-connector')
