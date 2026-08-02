# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from unittest.mock import patch

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

from ansible_collections.community.general.plugins.modules import wakeonlan

MAGIC_PACKET = b"\xff" * 6 + bytes.fromhex("00005e005366") * 16


class TestWakeonlanModule(ModuleTestCase):
    def setUp(self):
        super().setUp()
        self.module = wakeonlan

    def sent_packet(self, args):
        with patch.object(wakeonlan.socket, "socket") as socket_mock:
            with set_module_args(args):
                with self.assertRaises(AnsibleExitJson):
                    self.module.main()
        return socket_mock.return_value.sendto.call_args[0]

    def test_magic_packet(self):
        """The magic packet is the 102 bytes described by the AMD Magic Packet specification"""
        payload, address = self.sent_packet({"mac": "00:00:5E:00:53:66", "broadcast": "192.0.2.23", "port": 9})

        self.assertEqual(len(payload), 102)
        self.assertEqual(payload, MAGIC_PACKET)
        self.assertEqual(address, ("192.0.2.23", 9))

    def test_magic_packet_without_separators(self):
        """A MAC address without separators results in the very same packet"""
        payload, address = self.sent_packet({"mac": "00005E005366"})

        self.assertEqual(payload, MAGIC_PACKET)
        self.assertEqual(address, ("255.255.255.255", 7))

    def test_invalid_mac_length(self):
        with set_module_args({"mac": "00:00:5E:00:53"}):
            with self.assertRaises(AnsibleFailJson):
                self.module.main()

    def test_invalid_mac_format(self):
        with set_module_args({"mac": "00:00:5E:00:53:ZZ"}):
            with self.assertRaises(AnsibleFailJson):
                self.module.main()
