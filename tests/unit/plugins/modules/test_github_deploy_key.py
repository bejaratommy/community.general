# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    exit_json,
    fail_json,
    set_module_args,
)

from ansible_collections.community.general.plugins.modules import github_deploy_key

KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIC80tXocc1EjGbA3o9g+2Ifru9vZkzVXqqtC4zAccCCE"

EXISTING_KEY = {"id": 155460473, "title": "my-key", "key": KEY, "read_only": True}

BASE_ARGS = {
    "owner": "johndoe",
    "repo": "example",
    "name": "my-key",
    "key": KEY,
    "token": "ghp_test_token",
}


def make_fetch_url_response(body, status=200):
    response = MagicMock()
    response.read.return_value = json.dumps(body).encode("utf-8")
    info = {"status": status, "msg": f"OK ({len(json.dumps(body))} bytes)"}
    return (response, info)


@pytest.fixture(autouse=True)
def patch_module():
    with patch.multiple(
        "ansible.module_utils.basic.AnsibleModule",
        exit_json=exit_json,
        fail_json=fail_json,
    ):
        yield


@pytest.fixture
def fetch_url_mock():
    with patch.object(github_deploy_key, "fetch_url") as mock:
        yield mock


def methods_called(fetch_url_mock):
    return [call.kwargs["method"] for call in fetch_url_mock.call_args_list]


def test_check_mode_absent_does_not_delete_existing_key(fetch_url_mock):
    fetch_url_mock.side_effect = [make_fetch_url_response([EXISTING_KEY])]

    with set_module_args(dict(BASE_ARGS, state="absent", _ansible_check_mode=True)):
        with pytest.raises(AnsibleExitJson) as exc:
            github_deploy_key.main()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert result["id"] == str(EXISTING_KEY["id"])
    assert methods_called(fetch_url_mock) == ["GET"]


def test_check_mode_absent_missing_key(fetch_url_mock):
    fetch_url_mock.side_effect = [make_fetch_url_response([])]

    with set_module_args(dict(BASE_ARGS, state="absent", _ansible_check_mode=True)):
        with pytest.raises(AnsibleExitJson) as exc:
            github_deploy_key.main()

    result = exc.value.args[0]
    assert result["changed"] is False
    assert methods_called(fetch_url_mock) == ["GET"]


def test_check_mode_present_existing_key(fetch_url_mock):
    fetch_url_mock.side_effect = [make_fetch_url_response([EXISTING_KEY])]

    with set_module_args(dict(BASE_ARGS, _ansible_check_mode=True)):
        with pytest.raises(AnsibleExitJson) as exc:
            github_deploy_key.main()

    result = exc.value.args[0]
    assert result["changed"] is False
    assert methods_called(fetch_url_mock) == ["GET"]


def test_check_mode_present_missing_key(fetch_url_mock):
    fetch_url_mock.side_effect = [make_fetch_url_response([])]

    with set_module_args(dict(BASE_ARGS, _ansible_check_mode=True)):
        with pytest.raises(AnsibleExitJson) as exc:
            github_deploy_key.main()

    result = exc.value.args[0]
    assert result["changed"] is True
    assert methods_called(fetch_url_mock) == ["GET"]
