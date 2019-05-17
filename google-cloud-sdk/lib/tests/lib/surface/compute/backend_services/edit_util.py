# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Tests constanst for testing the backend-services edit subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap


YAML_FILE_CONTENTS_HEADER = textwrap.dedent("""\
    # You can edit the resource below. Lines beginning with "#" are
    # ignored.
    #
    # If you introduce a syntactic error, you will be given the
    # opportunity to edit the file again. You can abort by closing this
    # file without saving it.
    #
    # At the bottom of this file, you will find an example resource.
    #
    # Only fields that can be modified are shown. The original resource
    # with all of its fields is reproduced in the comment section at the
    # bottom of this document.

    """)
YAML_FILE_CONTENTS_WORKSPACE = textwrap.dedent("""\
    backends:
    - balancingMode: RATE
      group: https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/instanceGroups/group-1
      maxRate: 123
    - balancingMode: RATE
      group: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-b/instanceGroups/group-2
      maxRate: 456
    description: The best backend service
    healthChecks:
    - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/health-check
    port: 80
    portName: http
    protocol: HTTP
    timeoutSec: 15
    """)
YAML_FILE_CONTENTS_EXAMPLE = textwrap.dedent("""\

    # Example resource:
    # -----------------
    #
    #   backends:
    #   - balancingMode: RATE
    #     group: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/instanceGroups/group-1
    #     maxRate: 100
    #   - balancingMode: RATE
    #     group: https://www.googleapis.com/compute/v1/projects/my-project/zones/europe-west1-a/instanceGroups/group-2
    #     maxRate: 150
    #   description: My backend service
    #   healthChecks:
    #   - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/my-health-check-1
    #   - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/my-health-check-2
    #   name: backend-service
    #   port: 80
    #   portName: http
    #   protocol: HTTP
    #   selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/backend-service
    #   timeoutSec: 30
    #
    # Original resource:
    # ------------------
    #
    """)
YAML_FILE_CONTENTS_ORIGINAL = textwrap.dedent("""\
    #   backends:
    #   - balancingMode: RATE
    #     group: https://www.googleapis.com/compute/v1/projects/my-project/regions/us-central1/instanceGroups/group-1
    #     maxRate: 123
    #   - balancingMode: RATE
    #     group: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-b/instanceGroups/group-2
    #     maxRate: 456
    #   description: The best backend service
    #   healthChecks:
    #   - https://www.googleapis.com/compute/v1/projects/my-project/global/httpHealthChecks/health-check
    #   name: my-backend-service
    #   port: 80
    #   portName: http
    #   protocol: HTTP
    #   selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/backend-service
    #   timeoutSec: 15
    """)
YAML_FILE_CONTENTS = (YAML_FILE_CONTENTS_HEADER + YAML_FILE_CONTENTS_WORKSPACE +
                      YAML_FILE_CONTENTS_EXAMPLE + YAML_FILE_CONTENTS_ORIGINAL)
