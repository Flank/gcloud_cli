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
"""Helper methods to create instances of Cloud Run objects used in testing."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic as run_traffic
from googlecloudsdk.api_lib.util import apis

run_v1_messages = apis.GetMessagesModule("run", "v1")


def Metadata(name, namespace, annotations=None, labels=None):
  """Simplified the creation of googlecloudsdk.third_party.apis.run.v1.ObjectMeta.

  Args:
   name: name of the object
   namespace: the namespace of the object
   annotations: a dict of annotation (key,value) pairs
   labels: a dict of label (key,value) pairs

  Returns:
   a new ObjectMeta instance
  """
  metadata = run_v1_messages.ObjectMeta()
  metadata.name = name
  metadata.namespace = namespace

  if annotations:
    ann = run_v1_messages.ObjectMeta.AnnotationsValue()
    for k, v in annotations.items():
      p = run_v1_messages.ObjectMeta.AnnotationsValue.AdditionalProperty()
      p.key = k
      p.value = v
      ann.additionalProperties.append(p)
    metadata.annotations = ann

  if labels:
    lab = run_v1_messages.ObjectMeta.LabelsValue()
    for k, v in labels.items():
      l = run_v1_messages.ObjectMeta.LabelsValue.AdditionalProperty()
      l.key = k
      l.value = v
      lab.additionalProperties.append(l)
    metadata.labels = lab

  return metadata


def Container(name,
              image,
              env_vars=None,
              secrets=None,
              config_maps=None,
              command=None,
              args=None,
              ports=None,
              limits=None,
              volume_mounts=None):
  """Creates a new Cloud Run Container message.

  Args:
   name: string, name of the container
   image: string, image URL of the container
   env_vars: dict of environment variable names and values
   secrets: dict of secret keys and names
   config_maps: dict of config map keys and names
   command: list of strings, command to execute for the container
   args: list of strings, arguments for the command
   ports: list of tuples, where each element is a list of strings for port, name
     and protocol
   limits: dict of resource limits defined for the container

  Returns:
   a new Cloud Run Container message with the provided fields.
  """
  container = run_v1_messages.Container()
  container.name = name
  container.image = image

  if env_vars:
    for k, v in env_vars.items():
      var = run_v1_messages.EnvVar()
      var.name = k
      var.value = v
      container.env.append(var)

  if secrets:
    for s in secrets:
      sel = run_v1_messages.SecretKeySelector()
      sel.key = s["secretKey"]
      sel.name = s["secretName"]
      src = run_v1_messages.EnvVarSource()
      src.secretKeyRef = sel
      secret = run_v1_messages.EnvVar()
      secret.name = s["name"]
      secret.valueFrom = src
      container.env.append(secret)

  if config_maps:
    for c in config_maps:
      sel = run_v1_messages.ConfigMapKeySelector()
      sel.key = c["configKey"]
      sel.name = c["configName"]
      src = run_v1_messages.EnvVarSource()
      src.configMapKeyRef = sel
      config_map = run_v1_messages.EnvVar()
      config_map.name = c["name"]
      config_map.valueFrom = src
      container.env.append(config_map)

  container.command = command
  container.args = args

  if ports:
    for p in ports:
      port = run_v1_messages.ContainerPort()
      port.containerPort = p["port"]
      port.name = p["name"]
      port.protocol = p["protocol"]
      container.ports.append(port)

  if limits:
    lim = run_v1_messages.ResourceRequirements.LimitsValue()
    for k, v in limits.items():
      l = run_v1_messages.ResourceRequirements.LimitsValue.AdditionalProperty()
      l.key = k
      l.value = v
      lim.additionalProperties.append(l)
    resources = run_v1_messages.ResourceRequirements()
    resources.limits = lim
    container.resources = resources

  if volume_mounts:
    for m in volume_mounts:
      mount = run_v1_messages.VolumeMount()
      mount.name = m["name"]
      mount.mountPath = m["path"]
      container.volumeMounts.append(mount)

  return container


def RevisionSpec(container,
                 service_account,
                 timeout,
                 concurrency,
                 volumes=None):
  spec = run_v1_messages.RevisionSpec()
  spec.containers.append(container)
  spec.serviceAccountName = service_account
  spec.timeoutSeconds = timeout
  spec.containerConcurrency = concurrency

  if volumes:
    for v in volumes:
      vol = run_v1_messages.Volume()
      vol.name = v["name"]
      if "secret" in v:
        s = run_v1_messages.SecretVolumeSource()
        s.secretName = v["secret"]["secretName"]
        for i in v["secret"]["items"]:
          item = run_v1_messages.KeyToPath()
          item.key = i["key"]
          item.path = i["path"]
          s.items.append(item)
        vol.secret = s
      elif "configMap" in v:
        cm = run_v1_messages.ConfigMapVolumeSource()
        cm.name = v["configMap"]["name"]
        for i in v["configMap"]["items"]:
          item = run_v1_messages.KeyToPath()
          item.key = i["key"]
          item.path = i["path"]
          cm.items.append(item)
        vol.configMap = cm
      spec.volumes.append(vol)

  return spec


def Condition(condition_type,
              status="Unknown",
              severity="",
              msg="",
              reason="",
              last_transition_time=""):
  """Creates a new Condition object."""
  condition = run_v1_messages.GoogleCloudRunV1Condition()
  condition.type = condition_type
  condition.status = status
  condition.severity = severity
  condition.message = msg
  condition.reason = reason
  condition.lastTransitionTime = last_transition_time
  return condition


def RevisionStatus(conditions, image_digest="", log_url="", generation=0):
  status = run_v1_messages.RevisionStatus()
  status.conditions.extend(conditions)
  status.imageDigest = image_digest
  status.logUrl = log_url
  status.observedGeneration = generation
  return status


def TrafficTarget(rev=None,
                  percent=None,
                  is_latest=False,
                  tag=None,
                  url=None,
                  config_name=None):
  """Creates a new TrafficTarget object."""
  tt = run_v1_messages.TrafficTarget()
  tt.revisionName = rev
  tt.percent = percent
  tt.latestRevision = is_latest
  tt.tag = tag
  tt.url = url
  tt.configurationName = config_name
  return tt


def TrafficTargets(targets, msg_module):
  return run_traffic.TrafficTargets(msg_module, targets)


def Revision(msg_module, metadata=None, spec=None, status=None):
  rev_msg = run_v1_messages.Revision()
  rev_msg.metadata = metadata
  rev_msg.spec = spec
  rev_msg.status = status
  return revision.Revision(rev_msg, msg_module)


def ServiceSpec(template=None, traffic=None):
  spec = run_v1_messages.ServiceSpec()
  spec.template = template
  spec.traffic = traffic
  return spec


def ServiceStatus(address=None,
                  conditions=None,
                  latest_created=None,
                  latest_ready=None,
                  gen=None,
                  traffic=None,
                  url=None):
  """Creates a new ServiceStatus object."""
  spec = run_v1_messages.ServiceStatus()
  addr = run_v1_messages.Addressable()
  addr.url = address
  spec.address = addr
  spec.conditions = conditions or []
  spec.latestCreatedRevisionName = latest_created
  spec.latestReadyRevisionName = latest_ready
  spec.observedGeneration = gen
  spec.traffic = traffic
  spec.url = url
  return spec


def RunService(msg_module, metadata=None, spec=None, status=None):
  svc = run_v1_messages.Service()
  svc.metadata = metadata
  svc.spec = spec
  svc.status = status
  return service.Service(svc, msg_module)


def RunServiceRevisionTemplate(msg, msg_module):
  svc = run_v1_messages.Service()
  svc.spec = run_v1_messages.ServiceSpec()
  svc.spec.template = msg
  return service.Service(svc, msg_module).template


def TestMessagesModule():
  return run_v1_messages
