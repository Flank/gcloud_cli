# Copyright 2015 Google LLC. All Rights Reserved.
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

#% description: Creates a VM running a Salt master daemon in a Docker container.
#% parameters:
#% - name: zone
#%   type: string
#%   description: Zone to create the resources in.
#%   required: true
"""Generates config for a VM running a SaltStack master.

Just for fun this template is in Python, while the others in this
directory are in Jinja2.
"""

from __future__ import unicode_literals


def GenerateConfig(evaluation_context):
  return """
resources:
- type: compute.v1.firewall
  name: %(master)s-firewall
  properties:
    network: https://www.googleapis.com/compute/v1/projects/%(project)s/global/networks/default
    sourceRanges: [ "0.0.0.0/0" ]
    allowed:
    - IPProtocol: tcp
      ports: [ "4505", "4506" ]
- type: compute.v1.instance
  name: %(master)s
  properties:
    zone: %(zone)s
    machineType: https://www.googleapis.com/compute/v1/projects/%(project)s/zones/%(zone)s/machineTypes/f1-micro
    disks:
    - deviceName: boot
      type: PERSISTENT
      boot: true
      autoDelete: true
      initializeParams:
        sourceImage: https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/debian-7-wheezy-v20140619
    networkInterfaces:
    - network: https://www.googleapis.com/compute/v1/projects/%(project)s/global/networks/default
      accessConfigs:
      - name: External NAT
        type: ONE_TO_ONE_NAT
    metadata:
      items:
      - key: startup-script
        value: |
          #! /bin/bash
          sudo echo 'deb http://debian.saltstack.com/debian wheezy-saltstack main' >> /etc/apt/sources.list
          sudo wget -q -O- http://debian.saltstack.com/debian-salt-team-joehealy.gpg.key | sudo apt-key add -
          sudo apt-get update
          sudo apt-get -y install salt-master
          sudo salt-master -l debug
""" % {"master": evaluation_context.env["name"],
       "project": evaluation_context.env["project"],
       "zone": evaluation_context.properties["zone"]}
