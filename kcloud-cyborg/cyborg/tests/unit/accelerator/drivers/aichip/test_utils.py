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

import sys
from unittest import mock

from oslo_serialization import jsonutils

import cyborg
from cyborg.accelerator.drivers.aichip.furiosa.driver import (
    FuriosaAICHIPDriver
)
from cyborg.accelerator.drivers.aichip import utils
from cyborg.tests import base


CONF = cyborg.conf.CONF

FURIOSA_AICHIP_INFO = (
    "0000:3b:00.0 Processing accelerators [1200]: "
    "FuriosaAI, Inc. Warboy [1ed2:0000] (rev 01)"
)

BUILTIN = "__builtin__" if (sys.version_info[0] < 3) else "__builtins__"


class stdout(object):
    def readlines(self):
        return [FURIOSA_AICHIP_INFO]


class p(object):
    def __init__(self):
        self.stdout = stdout()

    def wait(self):
        pass


class TestAICHIPDriverUtils(base.TestCase):

    def setUp(self):
        super(TestAICHIPDriverUtils, self).setUp()
        self.p = p()

    @mock.patch("cyborg.accelerator.drivers.aichip.utils.lspci_privileged")
    def test_discover_vendors(self, mock_devices):
        mock_devices.return_value = self.p.stdout.readlines()
        aichip_vendors = utils.discover_vendors()
        self.assertEqual(1, len(aichip_vendors))

    @mock.patch("cyborg.accelerator.drivers.aichip.utils.lspci_privileged")
    def test_discover_aichips_report_AICHIP(self, mock_devices_for_vendor):
        """test furiosa AICHIP discover"""
        mock_devices_for_vendor.return_value = self.p.stdout.readlines()
        self.set_defaults(host="host-192-168-32-195", debug=True)

        furiosa = FuriosaAICHIPDriver()
        aichip_list = furiosa.discover()

        self.assertEqual(1, len(aichip_list))
        attach_handle_list = [
            {
                "attach_type": "PCI",
                "attach_info": '{"bus": "3b", '
                '"device": "00", '
                '"domain": "0000", '
                '"function": "0"}',
                "in_use": False,
            }
        ]
        attribute_list = [
            {"key": "rc", "value": "CUSTOM_AICHIP"},
            {"key": "trait0", "value": "OWNER_CYBORG"},
            {"key": "trait1", "value": "CUSTOM_FURIOSA_0000"},
        ]
        expected = {
            "vendor": "1ed2",
            "type": "AICHIP",
            "model": "FuriosaAI, Inc. Warboy",
            "std_board_info": {
                "controller": "Processing accelerators",
                "product_id": "0000",
            },
            "vendor_board_info": {"vendor_info": "aichip_vb_info"},
            "deployable_list": [
                {
                    "num_accelerators": 1,
                    "driver_name": "FURIOSA",
                    "name": "host-192-168-32-195_0000:3b:00.0",
                    "attach_handle_list": attach_handle_list,
                    "attribute_list": attribute_list,
                },
            ],
            "controlpath_id": {
                "cpid_info": '{"bus": "3b", '
                '"device": "00", '
                '"domain": "0000", '
                '"function": "0"}',
                "cpid_type": "PCI",
            },
        }
        aichip_obj = aichip_list[0]
        aichip_dict = aichip_obj.as_dict()
        aichip_dep_list = aichip_dict["deployable_list"]
        aichip_attach_handle_list = aichip_dep_list[0].as_dict()[
            "attach_handle_list"
        ]
        aichip_attribute_list = aichip_dep_list[0].as_dict()["attribute_list"]
        attri_obj_data = []
        [
            attri_obj_data.append(attr.as_dict())
            for attr in aichip_attribute_list
        ]
        attribute_actual_data = sorted(attri_obj_data, key=lambda i: i["key"])
        self.assertEqual(expected["vendor"], aichip_dict["vendor"])
        self.assertEqual(expected["model"], aichip_dict["model"])
        self.assertEqual(
            expected["controlpath_id"], aichip_dict["controlpath_id"]
        )
        self.assertEqual(
            expected["std_board_info"],
            jsonutils.loads(aichip_dict["std_board_info"]),
        )
        self.assertEqual(
            expected["vendor_board_info"],
            jsonutils.loads(aichip_dict["vendor_board_info"]),
        )
        self.assertEqual(
            expected["deployable_list"][0]["num_accelerators"],
            aichip_dep_list[0].as_dict()["num_accelerators"],
        )
        self.assertEqual(
            expected["deployable_list"][0]["name"],
            aichip_dep_list[0].as_dict()["name"],
        )
        self.assertEqual(
            expected["deployable_list"][0]["driver_name"],
            aichip_dep_list[0].as_dict()["driver_name"],
        )
        self.assertEqual(
            attach_handle_list[0], aichip_attach_handle_list[0].as_dict()
        )
        self.assertEqual(attribute_list, attribute_actual_data)


def multi_mock_open(*file_contents):
    """Create a mock "open" that will mock open multiple files in sequence.

    : params file_contents:  a list of file contents to be returned by open

    : returns: (MagicMock) a mock opener that will return the contents of the
               first file when opened the first time, the second file when
               opened the second time, etc.
    """

    mock_files = [
        mock.mock_open(read_data=content).return_value
        for content in file_contents
    ]
    mock_opener = mock.mock_open()
    mock_opener.side_effect = mock_files
    return mock_opener
