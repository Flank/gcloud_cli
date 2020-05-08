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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.compute.instance_templates import create_test_base


class InstanceTemplatesCreateWithMesh(
    create_test_base.InstanceTemplatesCreateTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'

  def testCreateWithBasicMesh(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON
        """)

    # labels for tracking adoption of mesh mode
    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh', value='{"mode": "ON"}'),
            m.Metadata.ItemsValueListEntry(
                # Running mesh-agent installation script without interfering
                # with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithBasicMeshAndMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON --metadata gce-mesh='{"mode": "OFF"}'
        """)

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh', value='{"mode": "ON"}'),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithBasicMeshOffAndMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=OFF --metadata gce-mesh='{"mode": "ON"}'
        """)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES)

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh', value='{"mode": "OFF"}'),
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithMeshAndWorkloadPorts(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON,workload-ports="90;80;70"
        """)

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh',
                value='{"mode": "ON", "service": {"workload-ports": [80, 90, 70]}}'
            ),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithMeshAndInvalidWorkloadPorts(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [workload-ports]: List of ports can only contain numbers between 1 and 65535.'
    ):
      self.Run("""
      compute instance-templates create template-1
      --mesh mode=ON,workload-ports="90;80;H"
      """)

  def testCreateWithMeshAndStartupScriptInMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON --metadata startup-script='#! /bin/bash
apt-get update
apt-get install -y apache2
cat <<EOF > /var/www/html/index.html
<html><body><h1>Hello World</h1>
<p>This page was created from a simple startup script!</p>
</body></html>'
        """)

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh', value='{"mode": "ON"}'),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(
                key='startup-script',
                value=textwrap.dedent("""\
                #! /bin/bash
                apt-get update
                apt-get install -y apache2
                cat <<EOF > /var/www/html/index.html
                <html><body><h1>Hello World</h1>
                <p>This page was created from a simple startup script!</p>
                </body></html>""")),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithBasicMeshAndDifferentMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON --metadata x=y,z=1,a=b,c=d
        """)

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh', value='{"mode": "ON"}'),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithMeshLabelsAndMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --mesh mode=ON --mesh-labels myapp=review,version=canary --metadata x=y,z=1,a=b,c=d
        """)

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh',
                value='{"mode": "ON", "labels": {"myapp": "review", "version": "canary"}}'
            ),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithAdvancedCallAndMetadata(self):
    m = self.messages
    self.Run(
        'compute instance-templates create template-1'
        ' --mesh mode=ON'
        ' --mesh-labels myapp=review,version=canary'
        ' --mesh-proxy-config TRAFFICDIRECTOR_ACCESS_LOG_PATH=/var/log/envoy/access.log'
        ',TRAFFICDIRECTOR_NETWORK_NAME=default'
        ' --metadata x=y,z=1,a=b,c=d')

    labels_for_tracking_mesh_adoption = (('mesh-mode', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh',
                value=(
                    '{"mode": "ON", '
                    '"labels": {"myapp": "review", "version": "canary"}, '
                    '"proxy-spec": {'
                    '"trafficdirector-config": {'
                    '"TRAFFICDIRECTOR_ACCESS_LOG_PATH": "/var/log/envoy/access.log", '
                    '"TRAFFICDIRECTOR_NETWORK_NAME": "default"}}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_mesh_adoption
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithAdvancedCallAndMetadataAndUserLabels(self):
    m = self.messages
    self.Run(
        'compute instance-templates create template-1'
        ' --mesh mode=ON'
        ' --mesh-labels myapp=review,version=canary'
        ' --mesh-proxy-config TRAFFICDIRECTOR_ACCESS_LOG_PATH=/var/log/envoy/access.log'
        ',TRAFFICDIRECTOR_NETWORK_NAME=default'
        ' --metadata x=y,z=1,a=b,c=d'
        ' --labels k-0=v-0,k-1=v-1')

    labels_for_tracking_and_request = (('mesh-mode', 'on'), ('k-0', 'v-0'),
                                       ('k-1', 'v-1'))

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh',
                value=(
                    '{"mode": "ON", '
                    '"labels": {"myapp": "review", "version": "canary"}, '
                    '"proxy-spec": {'
                    '"trafficdirector-config": {'
                    '"TRAFFICDIRECTOR_ACCESS_LOG_PATH": "/var/log/envoy/access.log", '
                    '"TRAFFICDIRECTOR_NETWORK_NAME": "default"}}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in sorted(labels_for_tracking_and_request)
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithAdvancedCallAndMetadataAndScopes(self):
    m = self.messages
    self.Run(
        'compute instance-templates create template-1'
        ' --mesh mode=ON'
        ' --mesh-labels myapp=review,version=canary'
        ' --mesh-proxy-config TRAFFICDIRECTOR_ACCESS_LOG_PATH=/var/log/envoy/access.log'
        ',TRAFFICDIRECTOR_NETWORK_NAME=default'
        ' --metadata x=y,z=1,a=b,c=d'
        ' --labels k-0=v-0,k-1=v-1'
        ' --scopes=datastore,default')

    labels_for_tracking_and_request = (('mesh-mode', 'on'), ('k-0', 'v-0'),
                                       ('k-1', 'v-1'))

    expected_scopes = sorted(
        create_test_base.DEFAULT_SCOPES +
        ['https://www.googleapis.com/auth/cloud-platform'] +
        ['https://www.googleapis.com/auth/datastore'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(key='a', value='b'),
            m.Metadata.ItemsValueListEntry(key='c', value='d'),
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-mesh',
                value=(
                    '{"mode": "ON", '
                    '"labels": {"myapp": "review", "version": "canary"}, '
                    '"proxy-spec": {'
                    '"trafficdirector-config": {'
                    '"TRAFFICDIRECTOR_ACCESS_LOG_PATH": "/var/log/envoy/access.log", '
                    '"TRAFFICDIRECTOR_NETWORK_NAME": "default"}}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration',
                value=(
                    '{'
                    '"softwareRecipes": [{'
                    '"name": "install-gce-mesh-agent", '
                    '"desired_state": "INSTALLED", '
                    '"installSteps": [{'
                    '"scriptRun": {'
                    '"script": "#! /bin/bash\\n'
                    'export MESH_AGENT_DIRECTORY=$(mktemp -d)\\n'
                    'sudo gsutil cp gs://gce-mesh/mesh-agent/releases/mesh-agent-0.1.tgz ${MESH_AGENT_DIRECTORY}\\n'
                    'sudo tar -xzf ${MESH_AGENT_DIRECTORY}/mesh-agent-0.1.tgz -C ${MESH_AGENT_DIRECTORY}\\n'
                    '${MESH_AGENT_DIRECTORY}/mesh-agent/mesh-agent-bootstrap.sh"}}]}]}'
                )),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in sorted(labels_for_tracking_and_request)
        ]),
        serviceAccounts=[
            m.ServiceAccount(email='default', scopes=expected_scopes)
        ],
    )

    self.CheckRequests(
        self.get_default_image_requests,
        [(self.compute.instanceTemplates, 'Insert',
          m.ComputeInstanceTemplatesInsertRequest(
              instanceTemplate=template,
              project='my-project',
          ))],
    )

  def testCreateWithMeshAndNoScopes(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --mesh, --no-scopes'):
      self.Run(
          'compute instance-templates create template-1'
          ' --mesh mode=ON'
          ' --mesh-labels myapp=review,version=canary'
          ' --mesh-proxy-config TRAFFICDIRECTOR_ACCESS_LOG_PATH=/var/log/envoy/access.log'
          ',TRAFFICDIRECTOR_NETWORK_NAME=default'
          ' --metadata x=y,z=1,a=b,c=d'
          ' --labels k-0=v-0,k-1=v-1'
          ' --no-scopes')


if __name__ == '__main__':
  test_case.main()
