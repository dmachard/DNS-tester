import pytest
from unittest.mock import patch, MagicMock
from cli.commands import launcher
from cli.commands import validate_address, sort_result_by_dns_server
from cli.version import PACKAGE_VERSION

@pytest.fixture
def mock_post_dns_lookup():
    with patch("cli.commands.post_dns_lookup") as mock_post:
        mock_post.return_value = "mock-task-id"
        yield mock_post

@pytest.fixture
def mock_get_task_status():
    with patch("cli.commands.get_task_status") as mock_get:
        mock_get.side_effect = [
            {"task_status": "PENDING"},
            {"task_status": "SUCCESS", "task_result": {
                "details": {
                    "udp://8.8.8.8": {
                        "command_status": "ok",
                        "dns_protocol": "Do53",
                        "rcode": "NOERROR",
                        "time_ms": 30.5,
                        "answers": [
                            {"value": "93.184.216.34", "type": "A", "ttl": 300}
                        ]
                    }
                },
                "duration": 30.5,
            }}
        ]
        yield mock_get

def test_main_direct_lookup(mock_post_dns_lookup, mock_get_task_status, capsys):
    # Simulate command-line arguments
    with patch("sys.argv", ["example.com", "udp://8.8.8.8", "--qtype", "A"]):
        # Pass mocked functions to main
        launcher(post_dns_lookup_func=mock_post_dns_lookup, get_task_status_func=mock_get_task_status)
    
    # Capture the output
    captured = capsys.readouterr()
    
    # Assertions
    assert "udp://8.8.8.8 - Do53 - 30.50000ms - TTL: 300s - 93.184.216.34" in captured.out

def test_validate_address_valid_inputs():
    assert validate_address("udp://8.8.8.8") == "8.8.8.8"
    assert validate_address("tcp://1.1.1.1:53") == "1.1.1.1"
    assert validate_address("https://dns.google") == "dns.google"
    assert validate_address("tls://one.one.one.one") == "one.one.one.one"
    assert validate_address("quic://example.com:853") == "example.com"

def test_validate_address_invalid_inputs():
    invalid_inputs = [
        "ftp://8.8.8.8",
        "just-a-string",
        "://missing.scheme",
        "udp//missing-colon.com",
        "udp:/one-slash.com",
    ]
    for invalid in invalid_inputs:
        with pytest.raises(ValueError, match="invalid server address format"):
            validate_address(invalid)

def test_cli_version_flag(capsys):
    with patch("sys.argv", ["--version"]):
        with pytest.raises(SystemExit) as excinfo:
            launcher()

        assert excinfo.value.code == 0

    captured = capsys.readouterr()
    assert f"DNS Tester - version {PACKAGE_VERSION}" in captured.out

def test_sort_result_by_dns_server_normal_case():
    data = {
        "udp://8.8.8.8": {"dns_protocol": "Do53"},
        "tls://1.1.1.1": {"dns_protocol": "DoT"},
        "https://dns.google": {"dns_protocol": "DoH"},
    }

    sorted_result = sort_result_by_dns_server(data)

    # Validate sort order (by host then dns_protocol)
    assert [item[0] for item in sorted_result] == [
        "tls://1.1.1.1",       # 1.1.1.1
        "udp://8.8.8.8",       # 8.8.8.8
        "https://dns.google",  # dns.google
    ]

# This test verifies that sort_result_by_dns_server correctly handles cases
# where the "dns_protocol" is None (e.g. when the DNS lookup command failed),
# and ensures such entries are sorted using "unknown" as a fallback.
def test_sort_result_by_dns_server_and_none_protocol():
    data = {
        "udp://8.8.8.8": {"dns_protocol": "Do53"},
        "tcp://1.1.1.1": {"dns_protocol": None},
        "tls://1.1.1.1": {"dns_protocol": "DoT"},
    }

    sorted_result = sort_result_by_dns_server(data)

    assert [item[0] for item in sorted_result] == [
        "tls://1.1.1.1",      # 1.1.1.1
        "tcp://1.1.1.1",      # 1.1.1.1 and unknown protocol 
        "udp://8.8.8.8",      # 8.8.8.8
    ]
