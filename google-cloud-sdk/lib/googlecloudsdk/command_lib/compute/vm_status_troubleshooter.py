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
"""Troubleshoot VPC setting for ssh connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from apitools.base.py import encoding

from google.protobuf import timestamp_pb2
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.core import log

_API_MONITORING_CLIENT_NAME = 'monitoring'
_API_MONITORING_VERSION_V3 = 'v3'

_CUSTOM_JSON_FIELD_MAPPINGS = {
    'interval_startTime': 'interval.startTime',
    'interval_endTime': 'interval.endTime',
}

CPU_METRICS = 'compute.googleapis.com/instance/cpu/utilization'
CPU_MESSAGE = (
    'VM CPU utilization is high, which may causes slow SSH connections. Stop '
    'your VM instance, increase the number of CPUs, and then restart it.\nHelp '
    'for stopping a VM: '
    'https://cloud.google.com/compute/docs/instances/stop-start-instance')

FILTER_TEMPLATE = (
    'metric.type = "{metrics_type}" AND '
    'metric.label.instance_name = "{instance_name}"')

CPU_THRESHOLD = 0.99


class VMStatusTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check VM status.

  Performance cpu, memory, disk status checking.

  Attributes:
    project: The project object.
    zone: str, the zone name.
    instance: The instance object.
  """

  def __init__(self, project, zone, instance):
    self.project = project
    self.zone = zone
    self.instance = instance
    self.monitoring_client = apis.GetClientInstance(_API_MONITORING_CLIENT_NAME,
                                                    _API_MONITORING_VERSION_V3)
    self.monitoring_message = apis.GetMessagesModule(
        _API_MONITORING_CLIENT_NAME, _API_MONITORING_VERSION_V3)
    self.issues = {}

  def check_prerequisite(self):
    return

  def cleanup_resources(self):
    return

  def troubleshoot(self):
    log.status.Print('---- Checking VM status ----')
    self._CheckCpuStatus()
    log.status.Print('VM status: {0} issue(s) found.'.format(
        len(self.issues)))
    # Prompt appropriate messages to user.
    for message in self.issues.values():
      log.status.Print(message)

  def _CheckCpuStatus(self):
    """Check cpu utilization."""
    # Mapping of apitools request message fields to json parameters.
    for req_field, mapped_param in _CUSTOM_JSON_FIELD_MAPPINGS.items():
      encoding.AddCustomJsonFieldMapping(
          self.monitoring_message.MonitoringProjectsTimeSeriesListRequest,
          req_field, mapped_param)

    request = self._CreateTimeSeriesListRequest(CPU_METRICS)

    response = self.monitoring_client.projects_timeSeries.List(request=request)
    if response.timeSeries:
      points = response.timeSeries[0].Points
      cpu_utilizatian = sum(
          point.value.doublevalue for point in points) / len(points)
      if cpu_utilizatian > CPU_THRESHOLD:
        self.issues['cpu'] = CPU_MESSAGE

  def _CreateTimeSeriesListRequest(self, metrics_type):
    """Create a MonitoringProjectsTimeSeriesListRequest.

    Args:
      metrics_type: str, https://cloud.google.com/monitoring/api/metrics

    Returns:
      MonitoringProjectsTimeSeriesListRequest, input message for
      ProjectsTimeSeriesService List method.
    """
    current_time = datetime.datetime.utcnow()
    tp_proto_end_time = timestamp_pb2.Timestamp()
    tp_proto_end_time.FromDatetime(current_time)
    tp_proto_start_time = timestamp_pb2.Timestamp()
    tp_proto_start_time.FromDatetime(current_time -
                                     datetime.timedelta(seconds=600))
    return self.monitoring_message.MonitoringProjectsTimeSeriesListRequest(
        name='projects/{project}'.format(project=self.project.name),
        filter=FILTER_TEMPLATE.format(
            metrics_type=metrics_type, instance_name=self.instance.name),
        interval_endTime=tp_proto_end_time.ToJsonString(),
        interval_startTime=tp_proto_start_time.ToJsonString())
