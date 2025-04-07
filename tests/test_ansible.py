
import pytest
import subprocess
import json

from api.ansible import read_inventory, read_hosts_from_inventory, get_dns_servers_from_ansible

MOCK_INVENTORY = {
    "all": {
        "children": ["group1"]
    },
    "group1": {
        "hosts": ["host1"]
    },
    "_meta": {
        "hostvars": {
            "host1": {
                "dns_address": "1.1.1.1",
                "domain_name": "example.com",
                "services": "do53,doh, dot",
                "details": "Test DNS server"
            }
        }
    }
}


def test_read_inventory_success(monkeypatch):
    mock_output = json.dumps(MOCK_INVENTORY).encode('utf-8')

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=mock_output,
            stderr=b''
        )

    monkeypatch.setattr(subprocess, "run", mock_run)

    inventory = read_inventory('fake_inventory_path')
    assert 'all' in inventory
    assert '_meta' in inventory

def test_read_inventory_failure(monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd="ansible-inventory",
            stderr=b"error"
        )

    monkeypatch.setattr(subprocess, "run", mock_run)

    with pytest.raises(subprocess.CalledProcessError):
        read_inventory("fake_path")

def test_read_hosts_from_inventory_success(mocker):
    mocker.patch("api.ansible.read_inventory", return_value=MOCK_INVENTORY)

    hosts = read_hosts_from_inventory("fake_path")
    assert len(hosts) == 1
    assert hosts[0]["dns_address"] == "1.1.1.1"
    assert "services" in hosts[0]

def test_read_hosts_from_inventory_failure(mocker):
    mocker.patch("api.ansible.read_inventory", side_effect=subprocess.CalledProcessError(1, "cmd", stderr=b"boom"))

    result = read_hosts_from_inventory("fake_path")
    assert result == []

def test_get_dns_servers_from_ansible(mocker):
    mocker.patch("api.ansible.read_hosts_from_inventory", return_value=[
        {
            "dns_address": "8.8.8.8",
            "domain_name": "dns.google",
            "services": "do53,doh,dot",
            "details": "Google DNS"
        }
    ])

    result = get_dns_servers_from_ansible("fake_path")
    targets = [entry["target"] for entry in result]
    
    assert "udp://8.8.8.8" in targets
    assert "tcp://8.8.8.8" in targets
    assert "https://dns.google" in targets
    assert "tls://dns.google" in targets
    assert len(result) == 4  # 2 (do53) + 1 (doh) + 1 (dot)