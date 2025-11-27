======
Cyborg
======

OpenStack Acceleration as a Service

Cyborg provides a general management framework for accelerators such as
FPGA, GPU, SoCs, NVMe SSDs, CCIX caches, DPDK/SPDK, pmem  and so forth.

* Free software: Apache license
* Wiki: https://wiki.openstack.org/wiki/Cyborg
* Source: https://opendev.org/openstack/cyborg
* Blueprints: https://blueprints.launchpad.net/openstack-cyborg
* Bugs: https://bugs.launchpad.net/openstack-cyborg
* Documentation: https://docs.openstack.org/cyborg/latest/
* Release notes: https://docs.openstack.org/releasenotes/cyborg/
* Design specifications: https://specs.openstack.org/openstack/cyborg-specs/

Features
--------

* REST API for basic accelerator life cycle management
* Generic driver for common accelerator support

Extending Cyborg to Integrate K-NPUs as Accelerators
----------------------------------------------------

This branch extends OpenStack Cyborg to support **K-NPUs
(Knowledge-based NPUs)** as hardware accelerators. The development is
based on the **stable/2024.1** release of Cyborg, and the goal is to
enable seamless integration of K-NPUs into the Cyborg framework.

Key Features of K-NPU Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **K-NPU Integration**: Extends the Cyborg framework to include K-NPUs
   as a supported accelerator type, allowing for efficient management
   and utilization of these hardware resources.

-  **Custom Driver Components**: Custom drivers have been developed to
   interact with K-NPU hardware, ensuring that K-NPU resources can be
   provisioned, managed, and monitored effectively.

-  **OpenStack-Helm Deployment**: The development work is designed to be
   deployed within OpenStack environments using OpenStack-Helm for
   easier configuration and management.

Development and Customization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Developers looking to contribute or further customize the K-NPU
integration can refer to the relevant directories where the custom code
changes are implemented. This includes modifications to the Cyborg API,
agent, and conductor components to support K-NPU resources.
