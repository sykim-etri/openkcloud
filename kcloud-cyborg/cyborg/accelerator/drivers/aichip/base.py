# Copyright 2025 Electronics and Telecommunications Research Institute.
#
# This software was supported by the Institute of Information & Communications
# Technology Planning & Evaluation(IITP) grant funded by the Korea government
# (MSIT) (No.RS-2025-02263869, Development of AI Semiconductor Cloud Platform
# Establishment and Optimization Technology)
#
# Copyright 2018 Beijing Lenovo Software Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""
Cyborg AICHIP driver implementation.
"""
from oslo_log import log as logging

from cyborg.accelerator.drivers.aichip import utils


LOG = logging.getLogger(__name__)


class AICHIPDriver(object):
    """Base class for AICHIP drivers.

    This is just a AICHIP drivers interface.
    Vendor should implement their specific drivers.
    """

    @classmethod
    def create(cls, vendor, *args, **kwargs):
        for sclass in cls.__subclasses__():
            vendor_name = utils.VENDOR_MAPS.get(vendor, vendor)
            if vendor_name == sclass.VENDOR:
                return sclass(*args, **kwargs)
        raise LookupError("Not find the AICHIP driver for vendor %s" % vendor)

    def discover(self):
        """Discover AICHIP information of current vendor(Identified by class).

        :return: List of AICHIP information dict.
        """
        raise NotImplementedError()

    @classmethod
    def discover_vendors(cls):
        """Discover AICHIP vendors of current node.

        :return: AICHIP vendor ID list.
        """
        return utils.discover_vendors()
