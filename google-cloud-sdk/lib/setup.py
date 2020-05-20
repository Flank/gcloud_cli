#!/usr/bin/python
# -*- coding: utf-8 -*- #
# Copyright 2011 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Setup installation module for gcloud-cli."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from setuptools import find_packages
from setuptools import setup

long_desc = ('gcloud-cli is a Python application that lets you access '
             'Google Cloud Platform from the command line.')


tests_require = [
    'modulegraph>=0.15',
    'pytest',
    'pytest-pythonpath',
    'pytest-xdist',
]

extras = {
    'test': tests_require,
}

setup(
    name='gcloud-cli',
    version='HEAD',
    url='https://developers.google.com/cloud/sdk',
    download_url='https://cloud.google.com/sdk',
    license='Apache 2.0',
    author='Google LLC.',
    author_email='google-cloud-sdk@googlegroups.com',
    description=('A command line tool for interacting with '
                 'Google Cloud Platform.'),
    long_description=long_desc,
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(exclude=['tests', 'third_party']),
    package_data={
        'googlecloudsdk': [
            os.path.join('core', '*.json'),
            os.path.join('core', 'credentials', '*.html'),
        ],
    },
    entry_points={
        'console_scripts': [
            'gcloud = gcloud:main',
            'regen_apis = tools.regen_apis.main:main',
        ],
    },
    install_requires=[
        'appdirs>=1.4.0',
        'argparse==1.2.1',
        'enum34>=0.9.23',
        'fasteners==0.14.1',
        'futures==3.0.5',
        'google-apitools>=0.5.13',
        'grpcio>=1.4.0',
        'httplib2==0.18.0',
        'ipaddr==2.1.11',
        'jsonschema>=2.0.0',
        'Mako>=0.7.3',
        'monotonic==1.2',
        'oauth2==1.5.170',
        'packaging>=16.8',
        'portpicker>=1.1.1',
        'prompt_toolkit==1.0.3',
        'pyparsing>=2.1.0',
        'protobuf==3.2.0',
        'PyYAML==3.11',
        'pyu2f>=0.1.1',  # Dependency of Oauth2client.
        'requests==2.10.0',
        'rsa>=3.1.4',
        'ruamel.yaml==0.11.11',
        'setuptools>=34.1.0',
        'six>=1.9.0',
        'uritemplate>=0.6',
        'websocket-client==0.10.0',
        'wcwidth>=0.1.6',
    ],
    tests_require=tests_require,
    extras_require=extras,
    setup_requires=['pytest-runner'],
)
