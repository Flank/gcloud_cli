# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Test data for suggest_commands module tests."""

ROOT = {
    'commands': {
        'app': {
            'commands': {
                'browse': {},
                'create': {},
                'deploy': {},
                'describe': {},
                'domain-mappings': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'firewall-rules': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'test-ip': {},
                        'update': {}
                    }
                },
                'instances': {
                    'commands': {
                        'delete': {},
                        'describe': {},
                        'disable-debug': {},
                        'enable-debug': {},
                        'list': {},
                        'scp': {},
                        'ssh': {}
                    }
                },
                'logs': {
                    'commands': {
                        'read': {},
                        'tail': {}
                    }
                },
                'open-console': {},
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'regions': {
                    'commands': {
                        'list': {}
                    }
                },
                'services': {
                    'commands': {
                        'browse': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'set-traffic': {}
                    }
                },
                'ssl-certificates': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'update': {},
                'versions': {
                    'commands': {
                        'browse': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'migrate': {},
                        'start': {},
                        'stop': {}
                    }
                }
            }
        },
        'auth': {
            'commands': {
                'activate-service-account': {},
                'application-default': {
                    'commands': {
                        'login': {},
                        'print-access-token': {},
                        'revoke': {}
                    }
                },
                'configure-docker': {},
                'list': {},
                'login': {},
                'revoke': {}
            }
        },
        'bigtable': {
            'commands': {
                'clusters': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'instances': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'set-iam-policy': {},
                        'update': {},
                        'upgrade': {}
                    }
                }
            }
        },
        'builds': {
            'commands': {
                'cancel': {},
                'describe': {},
                'list': {},
                'log': {},
                'submit': {}
            }
        },
        'components': {
            'commands': {
                'install': {},
                'list': {},
                'reinstall': {},
                'remove': {},
                'repositories': {
                    'commands': {
                        'add': {},
                        'list': {},
                        'remove': {}
                    }
                },
                'restore': {},
                'update': {}
            }
        },
        'composer': {
            'commands': {
                'environments': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'run': {},
                        'storage': {
                            'commands': {
                                'dags': {
                                    'commands': {
                                        'delete': {},
                                        'export': {},
                                        'import': {},
                                        'list': {}
                                    }
                                },
                                'data': {
                                    'commands': {
                                        'delete': {},
                                        'export': {},
                                        'import': {},
                                        'list': {}
                                    }
                                },
                                'plugins': {
                                    'commands': {
                                        'delete': {},
                                        'export': {},
                                        'import': {},
                                        'list': {}
                                    }
                                }
                            }
                        },
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                }
            }
        },
        'compute': {
            'commands': {
                'accelerator-types': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'addresses': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'backend-buckets': {
                    'commands': {
                        'add-signed-url-key': {},
                        'create': {},
                        'delete': {},
                        'delete-signed-url-key': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'backend-services': {
                    'commands': {
                        'add-backend': {},
                        'add-signed-url-key': {},
                        'create': {},
                        'delete': {},
                        'delete-signed-url-key': {},
                        'describe': {},
                        'edit': {},
                        'get-health': {},
                        'list': {},
                        'remove-backend': {},
                        'update': {},
                        'update-backend': {}
                    }
                },
                'commitments': {
                    'commands': {
                        'create': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'config-ssh': {},
                'connect-to-serial-port': {},
                'copy-files': {},
                'disk-types': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'disks': {
                    'commands': {
                        'add-labels': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'move': {},
                        'remove-labels': {},
                        'resize': {},
                        'snapshot': {},
                        'update': {}
                    }
                },
                'firewall-rules': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'forwarding-rules': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'set-target': {}
                    }
                },
                'health-checks': {
                    'commands': {
                        'create': {
                            'commands': {
                                'http': {},
                                'https': {},
                                'ssl': {},
                                'tcp': {}
                            }
                        },
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {
                            'commands': {
                                'http': {},
                                'https': {},
                                'ssl': {},
                                'tcp': {}
                            }
                        }
                    }
                },
                'http-health-checks': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'https-health-checks': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'images': {
                    'commands': {
                        'add-labels': {},
                        'create': {},
                        'delete': {},
                        'deprecate': {},
                        'describe': {},
                        'describe-from-family': {},
                        'export': {},
                        'import': {},
                        'list': {},
                        'remove-labels': {},
                        'update': {}
                    }
                },
                'instance-groups': {
                    'commands': {
                        'describe': {},
                        'get-named-ports': {},
                        'list': {},
                        'list-instances': {},
                        'managed': {
                            'commands': {
                                'abandon-instances': {},
                                'create': {},
                                'delete': {},
                                'delete-instances': {},
                                'describe': {},
                                'get-named-ports': {},
                                'list': {},
                                'list-instances': {},
                                'recreate-instances': {},
                                'resize': {},
                                'set-autoscaling': {},
                                'set-instance-template': {},
                                'set-named-ports': {},
                                'set-target-pools': {},
                                'stop-autoscaling': {},
                                'wait-until-stable': {}
                            }
                        },
                        'set-named-ports': {},
                        'unmanaged': {
                            'commands': {
                                'add-instances': {},
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'get-named-ports': {},
                                'list': {},
                                'list-instances': {},
                                'remove-instances': {},
                                'set-named-ports': {}
                            }
                        }
                    }
                },
                'instance-templates': {
                    'commands': {
                        'create': {},
                        'create-with-container': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'instances': {
                    'commands': {
                        'add-access-config': {},
                        'add-labels': {},
                        'add-metadata': {},
                        'add-tags': {},
                        'attach-disk': {},
                        'create': {},
                        'create-with-container': {},
                        'delete': {},
                        'delete-access-config': {},
                        'describe': {},
                        'detach-disk': {},
                        'get-serial-port-output': {},
                        'list': {},
                        'move': {},
                        'network-interfaces': {
                            'commands': {
                                'update': {}
                            }
                        },
                        'remove-labels': {},
                        'remove-metadata': {},
                        'remove-tags': {},
                        'reset': {},
                        'set-disk-auto-delete': {},
                        'set-machine-type': {},
                        'set-scheduling': {},
                        'set-service-account': {},
                        'simulate-maintenance-event': {},
                        'start': {},
                        'stop': {},
                        'tail-serial-port-output': {},
                        'update': {},
                        'update-access-config': {},
                        'update-container': {}
                    }
                },
                'interconnects': {
                    'commands': {
                        'attachments': {
                            'commands': {
                                'dedicated': {
                                    'commands': {
                                        'create': {},
                                        'update': {}
                                    }
                                },
                                'delete': {},
                                'describe': {},
                                'list': {},
                                'partner': {
                                    'commands': {
                                        'create': {},
                                        'update': {}
                                    }
                                }
                            }
                        },
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'locations': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        },
                        'update': {}
                    }
                },
                'machine-types': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'networks': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'peerings': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'list': {}
                            }
                        },
                        'subnets': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'expand-ip-range': {},
                                'list': {},
                                'list-usable': {},
                                'update': {}
                            }
                        },
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'os-login': {
                    'commands': {
                        'describe-profile': {},
                        'remove-profile': {},
                        'ssh-keys': {
                            'commands': {
                                'add': {},
                                'describe': {},
                                'list': {},
                                'remove': {},
                                'update': {}
                            }
                        }
                    }
                },
                'project-info': {
                    'commands': {
                        'add-metadata': {},
                        'describe': {},
                        'remove-metadata': {},
                        'set-usage-bucket': {},
                        'update': {}
                    }
                },
                'regions': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'reset-windows-password': {},
                'routers': {
                    'commands': {
                        'add-bgp-peer': {},
                        'add-interface': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-status': {},
                        'list': {},
                        'remove-bgp-peer': {},
                        'remove-interface': {},
                        'update': {},
                        'update-bgp-peer': {},
                        'update-interface': {}
                    }
                },
                'routes': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'scp': {},
                'shared-vpc': {
                    'commands': {
                        'associated-projects': {
                            'commands': {
                                'add': {},
                                'list': {},
                                'remove': {}
                            }
                        },
                        'disable': {},
                        'enable': {},
                        'get-host-project': {},
                        'list-associated-resources': {},
                        'organizations': {
                            'commands': {
                                'list-host-projects': {}
                            }
                        }
                    }
                },
                'sign-url': {},
                'snapshots': {
                    'commands': {
                        'add-labels': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'remove-labels': {},
                        'update': {}
                    }
                },
                'sole-tenancy': {
                    'commands': {
                        'node-groups': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'list': {},
                                'list-nodes': {},
                                'update': {}
                            }
                        },
                        'node-templates': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'list': {}
                            }
                        },
                        'node-types': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        }
                    }
                },
                'ssh': {},
                'ssl-certificates': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'ssl-policies': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'list-available-features': {},
                        'update': {}
                    }
                },
                'target-http-proxies': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'target-https-proxies': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'target-instances': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'target-pools': {
                    'commands': {
                        'add-health-checks': {},
                        'add-instances': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-health': {},
                        'list': {},
                        'remove-health-checks': {},
                        'remove-instances': {},
                        'set-backup': {}
                    }
                },
                'target-ssl-proxies': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'target-tcp-proxies': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'target-vpn-gateways': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'tpus': {
                    'commands': {
                        'accelerator-types': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        },
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'locations': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        },
                        'reimage': {},
                        'start': {},
                        'stop': {},
                        'versions': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        }
                    }
                },
                'url-maps': {
                    'commands': {
                        'add-host-rule': {},
                        'add-path-matcher': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'edit': {},
                        'invalidate-cdn-cache': {},
                        'list': {},
                        'list-cdn-cache-invalidations': {},
                        'remove-host-rule': {},
                        'remove-path-matcher': {},
                        'set-default-service': {}
                    }
                },
                'vpn-tunnels': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'zones': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                }
            }
        },
        'config': {
            'commands': {
                'configurations': {
                    'commands': {
                        'activate': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'get-value': {},
                'list': {},
                'set': {},
                'unset': {}
            }
        },
        'container': {
            'commands': {
                'clusters': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-credentials': {},
                        'list': {},
                        'resize': {},
                        'update': {},
                        'upgrade': {}
                    }
                },
                'get-server-config': {},
                'images': {
                    'commands': {
                        'add-tag': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'list-tags': {},
                        'untag': {}
                    }
                },
                'node-pools': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'rollback': {},
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                }
            }
        },
        'dataflow': {
            'commands': {
                'jobs': {
                    'commands': {
                        'cancel': {},
                        'describe': {},
                        'drain': {},
                        'list': {},
                        'run': {},
                        'show': {}
                    }
                }
            }
        },
        'dataproc': {
            'commands': {
                'clusters': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'diagnose': {},
                        'get-iam-policy': {},
                        'list': {},
                        'set-iam-policy': {},
                        'update': {}
                    }
                },
                'jobs': {
                    'commands': {
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'kill': {},
                        'list': {},
                        'set-iam-policy': {},
                        'submit': {
                            'commands': {
                                'hadoop': {},
                                'hive': {},
                                'pig': {},
                                'pyspark': {},
                                'spark': {},
                                'spark-sql': {}
                            }
                        },
                        'update': {},
                        'wait': {}
                    }
                },
                'operations': {
                    'commands': {
                        'cancel': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'set-iam-policy': {}
                    }
                },
                'workflow-templates': {
                    'commands': {
                        'add-job': {
                            'commands': {
                                'hadoop': {},
                                'hive': {},
                                'pig': {},
                                'pyspark': {},
                                'spark': {},
                                'spark-sql': {}
                            }
                        },
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'export': {},
                        'get-iam-policy': {},
                        'import': {},
                        'instantiate': {},
                        'instantiate-from-file': {},
                        'list': {},
                        'remove-job': {},
                        'set-cluster-selector': {},
                        'set-iam-policy': {},
                        'set-managed-cluster': {}
                    }
                }
            }
        },
        'datastore': {
            'commands': {
                'cleanup-indexes': {},
                'create-indexes': {},
                'export': {},
                'import': {},
                'indexes': {
                    'commands': {
                        'cleanup': {},
                        'create': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'operations': {
                    'commands': {
                        'cancel': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                }
            }
        },
        'debug': {
            'commands': {
                'logpoints': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'list': {}
                    }
                },
                'snapshots': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'source': {
                    'commands': {
                        'gen-repo-info-file': {}
                    }
                },
                'targets': {
                    'commands': {
                        'list': {}
                    }
                }
            }
        },
        'deployment-manager': {
            'commands': {
                'deployments': {
                    'commands': {
                        'cancel-preview': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'stop': {},
                        'update': {}
                    }
                },
                'manifests': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'resources': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'types': {
                    'commands': {
                        'list': {}
                    }
                }
            }
        },
        'dns': {
            'commands': {
                'dns-keys': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'managed-zones': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'project-info': {
                    'commands': {
                        'describe': {}
                    }
                },
                'record-sets': {
                    'commands': {
                        'changes': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        },
                        'export': {},
                        'import': {},
                        'list': {},
                        'transaction': {
                            'commands': {
                                'abort': {},
                                'add': {},
                                'describe': {},
                                'execute': {},
                                'remove': {},
                                'start': {}
                            }
                        }
                    }
                }
            }
        },
        'docker': {},
        'domains': {
            'commands': {
                'list-user-verified': {},
                'verify': {}
            }
        },
        'endpoints': {
            'commands': {
                'configs': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'services': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'check-iam-policy': {},
                        'delete': {},
                        'deploy': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'undelete': {}
                    }
                }
            }
        },
        'feedback': {},
        'firebase': {
            'commands': {
                'test': {
                    'commands': {
                        'android': {
                            'commands': {
                                'locales': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                },
                                'models': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                },
                                'run': {},
                                'versions': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                }
                            }
                        },
                        'ios': {
                            'commands': {
                                'locales': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                },
                                'models': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                },
                                'run': {},
                                'versions': {
                                    'commands': {
                                        'describe': {},
                                        'list': {}
                                    }
                                }
                            }
                        },
                        'network-profiles': {
                            'commands': {
                                'describe': {},
                                'list': {}
                            }
                        }
                    }
                }
            }
        },
        'functions': {
            'commands': {
                'call': {},
                'delete': {},
                'deploy': {},
                'describe': {},
                'event-types': {
                    'commands': {
                        'list': {}
                    }
                },
                'list': {},
                'logs': {
                    'commands': {
                        'read': {}
                    }
                },
                'regions': {
                    'commands': {
                        'list': {}
                    }
                }
            }
        },
        'help': {},
        'iam': {
            'commands': {
                'list-grantable-roles': {},
                'list-testable-permissions': {},
                'roles': {
                    'commands': {
                        'copy': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'undelete': {},
                        'update': {}
                    }
                },
                'service-accounts': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'keys': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'list': {}
                            }
                        },
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'set-iam-policy': {},
                        'sign-blob': {},
                        'update': {}
                    }
                }
            }
        },
        'info': {},
        'init': {},
        'iot': {
            'commands': {
                'devices': {
                    'commands': {
                        'configs': {
                            'commands': {
                                'describe': {},
                                'get-value': {},
                                'list': {},
                                'update': {}
                            }
                        },
                        'create': {},
                        'credentials': {
                            'commands': {
                                'clear': {},
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'list': {},
                                'update': {}
                            }
                        },
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'states': {
                            'commands': {
                                'list': {}
                            }
                        },
                        'update': {}
                    }
                },
                'registries': {
                    'commands': {
                        'create': {},
                        'credentials': {
                            'commands': {
                                'clear': {},
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'list': {}
                            }
                        },
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'set-iam-policy': {},
                        'update': {}
                    }
                }
            }
        },
        'kms': {
            'commands': {
                'decrypt': {},
                'encrypt': {},
                'keyrings': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'set-iam-policy': {}
                    }
                },
                'keys': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'remove-rotation-schedule': {},
                        'set-iam-policy': {},
                        'set-primary-version': {},
                        'set-rotation-schedule': {},
                        'update': {},
                        'versions': {
                            'commands': {
                                'create': {},
                                'describe': {},
                                'destroy': {},
                                'disable': {},
                                'enable': {},
                                'list': {},
                                'restore': {}
                            }
                        }
                    }
                },
                'locations': {
                    'commands': {
                        'list': {}
                    }
                }
            }
        },
        'logging': {
            'commands': {
                'logs': {
                    'commands': {
                        'delete': {},
                        'list': {}
                    }
                },
                'metrics': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'read': {},
                'resource-descriptors': {
                    'commands': {
                        'list': {}
                    }
                },
                'sinks': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'write': {}
            }
        },
        'ml': {
            'commands': {
                'language': {
                    'commands': {
                        'analyze-entities': {},
                        'analyze-entity-sentiment': {},
                        'analyze-sentiment': {},
                        'analyze-syntax': {},
                        'classify-text': {}
                    }
                },
                'speech': {
                    'commands': {
                        'operations': {
                            'commands': {
                                'describe': {},
                                'wait': {}
                            }
                        },
                        'recognize': {},
                        'recognize-long-running': {}
                    }
                },
                'video': {
                    'commands': {
                        'detect-explicit-content': {},
                        'detect-labels': {},
                        'detect-shot-changes': {},
                        'operations': {
                            'commands': {
                                'describe': {},
                                'wait': {}
                            }
                        }
                    }
                },
                'vision': {
                    'commands': {
                        'detect-document': {},
                        'detect-faces': {},
                        'detect-image-properties': {},
                        'detect-labels': {},
                        'detect-landmarks': {},
                        'detect-logos': {},
                        'detect-safe-search': {},
                        'detect-text': {},
                        'detect-web': {},
                        'suggest-crop': {}
                    }
                }
            }
        },
        'ml-engine': {
            'commands': {
                'jobs': {
                    'commands': {
                        'cancel': {},
                        'describe': {},
                        'list': {},
                        'stream-logs': {},
                        'submit': {
                            'commands': {
                                'prediction': {},
                                'training': {}
                            }
                        },
                        'update': {}
                    }
                },
                'local': {
                    'commands': {
                        'predict': {},
                        'train': {}
                    }
                },
                'models': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'set-iam-policy': {},
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'cancel': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'predict': {},
                'versions': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'set-default': {},
                        'update': {}
                    }
                }
            }
        },
        'organizations': {
            'commands': {
                'add-iam-policy-binding': {},
                'describe': {},
                'get-iam-policy': {},
                'list': {},
                'remove-iam-policy-binding': {},
                'set-iam-policy': {}
            }
        },
        'projects': {
            'commands': {
                'add-iam-policy-binding': {},
                'create': {},
                'delete': {},
                'describe': {},
                'get-iam-policy': {},
                'list': {},
                'remove-iam-policy-binding': {},
                'set-iam-policy': {},
                'undelete': {},
                'update': {}
            }
        },
        'pubsub': {
            'commands': {
                'subscriptions': {
                    'commands': {
                        'ack': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'modify-message-ack-deadline': {},
                        'modify-push-config': {},
                        'pull': {}
                    }
                },
                'topics': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'list-subscriptions': {},
                        'publish': {}
                    }
                }
            }
        },
        'redis': {
            'commands': {
                'instances': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'regions': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'zones': {
                    'commands': {
                        'list': {}
                    }
                }
            }
        },
        'services': {
            'commands': {
                'disable': {},
                'enable': {},
                'list': {},
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                }
            }
        },
        'source': {
            'commands': {
                'repos': {
                    'commands': {
                        'clone': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'set-iam-policy': {}
                    }
                }
            }
        },
        'spanner': {
            'commands': {
                'databases': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'ddl': {
                            'commands': {
                                'describe': {},
                                'update': {}
                            }
                        },
                        'delete': {},
                        'describe': {},
                        'execute-sql': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'sessions': {
                            'commands': {
                                'delete': {},
                                'list': {}
                            }
                        },
                        'set-iam-policy': {}
                    }
                },
                'instance-configs': {
                    'commands': {
                        'describe': {},
                        'list': {}
                    }
                },
                'instances': {
                    'commands': {
                        'add-iam-policy-binding': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'get-iam-policy': {},
                        'list': {},
                        'remove-iam-policy-binding': {},
                        'set-iam-policy': {},
                        'update': {}
                    }
                },
                'operations': {
                    'commands': {
                        'cancel': {},
                        'describe': {},
                        'list': {}
                    }
                }
            }
        },
        'sql': {
            'commands': {
                'backups': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'restore': {}
                    }
                },
                'connect': {},
                'databases': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {},
                        'patch': {}
                    }
                },
                'export': {
                    'commands': {
                        'csv': {},
                        'sql': {}
                    }
                },
                'flags': {
                    'commands': {
                        'list': {}
                    }
                },
                'import': {
                    'commands': {
                        'csv': {},
                        'sql': {}
                    }
                },
                'instances': {
                    'commands': {
                        'clone': {},
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'export': {},
                        'failover': {},
                        'import': {},
                        'list': {},
                        'patch': {},
                        'promote-replica': {},
                        'reset-ssl-config': {},
                        'restart': {},
                        'restore-backup': {}
                    }
                },
                'operations': {
                    'commands': {
                        'describe': {},
                        'list': {},
                        'wait': {}
                    }
                },
                'ssl': {
                    'commands': {
                        'client-certs': {
                            'commands': {
                                'create': {},
                                'delete': {},
                                'describe': {},
                                'list': {}
                            }
                        }
                    }
                },
                'ssl-certs': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'describe': {},
                        'list': {}
                    }
                },
                'tiers': {
                    'commands': {
                        'list': {}
                    }
                },
                'users': {
                    'commands': {
                        'create': {},
                        'delete': {},
                        'list': {},
                        'set-password': {}
                    }
                }
            }
        },
        'topic': {
            'commands': {
                'arg-files': {},
                'cli-trees': {},
                'command-conventions': {},
                'configurations': {},
                'datetimes': {},
                'escaping': {},
                'filters': {},
                'flags-file': {},
                'formats': {},
                'gcloudignore': {},
                'offline-help': {},
                'projections': {},
                'resource-keys': {},
                'startup': {}
            }
        },
        'version': {}
    }
}
