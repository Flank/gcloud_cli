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

osconfig_metadata_value = (
    '{"softwareRecipes": [{"name": "install-gce-service-proxy-agent", '
    '"desired_state": "INSTALLED", "installSteps": [{"scriptRun": {"script": '
    '"#! /bin/bash\\nZONE=$( curl --silent '
    'http://metadata.google.internal/computeMetadata/v1/instance/zone -H '
    'Metadata-Flavor:Google | cut -d/ -f4 )\\nexport '
    'SERVICE_PROXY_AGENT_DIRECTORY=$(mktemp -d)\\nsudo gsutil cp   '
    'gs://gce-service-proxy-${ZONE}/service-proxy-agent/releases/service-proxy-agent-0.2.tgz'
    '   ${SERVICE_PROXY_AGENT_DIRECTORY}   || sudo gsutil cp     '
    'gs://gce-service-proxy/service-proxy-agent/releases/service-proxy-agent-0.2.tgz'
    '     ${SERVICE_PROXY_AGENT_DIRECTORY}\\nsudo tar -xzf '
    '${SERVICE_PROXY_AGENT_DIRECTORY}/service-proxy-agent-0.2.tgz -C '
    '${SERVICE_PROXY_AGENT_DIRECTORY}\\n${SERVICE_PROXY_AGENT_DIRECTORY}/service-proxy-agent/service-proxy-agent-bootstrap.sh"}}]}]}'
)


class InstanceTemplatesCreateWithServiceProxyGA(
    create_test_base.InstanceTemplatesCreateTestBase):
  """Test creation of Instance Templates with --service-proxy configuration argument in GA."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.api_version = 'v1'

  def testCreateWithBasicCall(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled
        """)

    # labels for tracking adoption of --service-proxy flag.
    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                # Running service-proxy-agent installation script without
                # interfering with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithProxyPort(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled,proxy-port=15002
        """)

    # labels for tracking adoption of --service-proxy flag.
    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"proxy-port": 15002, '
                       '"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                # Running service-proxy-agent installation script without
                # interfering with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithServingPorts(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled,serving-ports="90;80;70"
        """)

    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"service": {"serving-ports": [80, 90, 70]}, '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithInvalidServingPorts(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [serving-ports]: List of ports can only contain numbers between 1 and 65535.'
    ):
      self.Run("""
      compute instance-templates create template-1
      --service-proxy enabled,serving-ports="90;80;H"
      """)

  def testCreateWithStartupScriptInMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled --metadata startup-script='#! /bin/bash
apt-get update
apt-get install -y apache2
cat <<EOF > /var/www/html/index.html
<html><body><h1>Hello World</h1>
<p>This page was created from a simple startup script!</p>
</body></html>'
        """)

    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
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
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithDifferentMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled --metadata x=y,z=1,a=b,c=d
        """)

    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

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
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithLabelsAndMetadata(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled --service-proxy-labels myapp=review,version=canary --metadata x=y,z=1,a=b,c=d
        """)

    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

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
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"labels": {"myapp": "review", "version": "canary"}, '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
            m.Metadata.ItemsValueListEntry(key='x', value='y'),
            m.Metadata.ItemsValueListEntry(key='z', value='1'),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithUserLabels(self):
    m = self.messages
    self.Run('compute instance-templates create template-1'
             ' --service-proxy enabled'
             ' --service-proxy-labels myapp=review,version=canary'
             ' --metadata x=y,z=1,a=b,c=d'
             ' --labels k-0=v-0,k-1=v-1')

    labels_for_tracking_and_request = (('gce-service-proxy', 'on'),
                                       ('k-0', 'v-0'), ('k-1', 'v-1'))

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
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"labels": {"myapp": "review", "version": "canary"}, '
                       '"proxy-spec": {"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
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

  def testCreateWithNoScopes(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.ConflictingArgumentsException,
        'arguments not allowed simultaneously: --service-proxy, --no-scopes'):
      self.Run('compute instance-templates create template-1'
               ' --service-proxy enabled'
               ' --service-proxy-labels myapp=review,version=canary'
               ' --metadata x=y,z=1,a=b,c=d'
               ' --labels k-0=v-0,k-1=v-1'
               ' --no-scopes')

  def testCreateWithTracing(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled,tracing=ON
        """)

    # labels for tracking adoption of --service-proxy flag.
    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"tracing": "ON", '
                       '"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                # Running service-proxy-agent installation script without
                # interfering with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithAccessLog(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled,access-log="/var/log/envoy/access.log"
        """)

    # labels for tracking adoption of --service-proxy flag.
    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=(
                    '{"api-version": "0.2", '
                    '"proxy-spec": {"access-log": "/var/log/envoy/access.log", '
                    '"network": ""}}')),
            m.Metadata.ItemsValueListEntry(
                # Running service-proxy-agent installation script without
                # interfering with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithNetwork(self):
    m = self.messages
    self.Run("""
        compute instance-templates create template-1
          --service-proxy enabled,network="some-network"
        """)

    # labels for tracking adoption of --service-proxy flag.
    labels_for_tracking_service_proxy_adoption = (('gce-service-proxy', 'on'),)

    expected_scopes = sorted(create_test_base.DEFAULT_SCOPES +
                             ['https://www.googleapis.com/auth/cloud-platform'])

    template = self._MakeInstanceTemplate(
        metadata=m.Metadata(items=[
            m.Metadata.ItemsValueListEntry(
                key='enable-guest-attributes', value='TRUE'),
            m.Metadata.ItemsValueListEntry(key='enable-osconfig', value='true'),
            m.Metadata.ItemsValueListEntry(
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"proxy-spec": {"network": "some-network"}}')),
            m.Metadata.ItemsValueListEntry(
                # Running service-proxy-agent installation script without
                # interfering with user startup-script. See
                # go/vm-instance-software-configurations for more info.
                key='gce-software-declaration',
                value=osconfig_metadata_value),
        ]),
        labels=m.InstanceProperties.LabelsValue(additionalProperties=[
            m.InstanceProperties.LabelsValue.AdditionalProperty(
                key=pair[0], value=pair[1])
            for pair in labels_for_tracking_service_proxy_adoption
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

  def testCreateWithAllArgs(self):
    m = self.messages
    self.Run(
        'compute instance-templates create template-1'
        ' --service-proxy'
        ' enabled,network="some-network",serving-ports="70;80;90",proxy-port=15002,tracing=OFF,access-log="/var/log/envoy/access.log"'
        ' --service-proxy-labels myapp=review,version=canary'
        ' --metadata x=y,z=1,a=b,c=d'
        ' --labels k-0=v-0,k-1=v-1')

    labels_for_tracking_and_request = (('gce-service-proxy', 'on'),
                                       ('k-0', 'v-0'), ('k-1', 'v-1'))

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
                key='gce-service-proxy',
                value=('{"api-version": "0.2", '
                       '"service": {"serving-ports": [80, 90, 70]}, '
                       '"labels": {"myapp": "review", "version": "canary"}, '
                       '"proxy-spec": {"proxy-port": 15002, "tracing": "OFF", '
                       '"access-log": "/var/log/envoy/access.log", '
                       '"network": "some-network"}}')),
            m.Metadata.ItemsValueListEntry(
                key='gce-software-declaration', value=osconfig_metadata_value),
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


class InstanceTemplatesCreateWithServiceProxyBeta(
    InstanceTemplatesCreateWithServiceProxyGA):
  """Test creation of Instance Templates with --service-proxy configuration argument in Beta."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.api_version = 'beta'


class InstanceTemplatesCreateWithServiceProxyAlpha(
    InstanceTemplatesCreateWithServiceProxyGA):
  """Test creation of Instance Templates with --service-proxy configuration argument in Alpha."""

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.api_version = 'alpha'


if __name__ == '__main__':
  test_case.main()
