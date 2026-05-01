import pytest
from types import SimpleNamespace
from unittest.mock import patch, call

from cli.commands import (
    collect_targets,
    launcher,
    normalize_qtype,
    sort_result_by_dns_server,
    validate_address,
)
from cli.version import PACKAGE_VERSION


def make_success_status(
    server="udp://8.8.8.8",
    dns_protocol="Do53",
    rcode="NOERROR",
    time_ms=30.5,
    record_type="A",
    value="93.184.216.34",
    ttl=300,
):
    return {
        "task_status": "SUCCESS",
        "task_result": {
            "details": {
                server: {
                    "command_status": "ok",
                    "dns_protocol": dns_protocol,
                    "rcode": rcode,
                    "time_ms": time_ms,
                    "answers": [
                        {"value": value, "type": record_type, "ttl": ttl},
                    ],
                }
            },
            "duration": time_ms,
        },
    }


def make_failure_status(server="udp://8.8.8.8", error="connection error"):
    return {
        "task_status": "SUCCESS",
        "task_result": {
            "details": {
                server: {
                    "command_status": "error",
                    "error": error,
                }
            },
            "duration": 12.0,
        },
    }


@pytest.fixture
def mock_post_dns_lookup():
    with patch("cli.commands.post_dns_lookup", return_value="mock-task-id") as mock_post:
        yield mock_post


@pytest.fixture
def mock_post_reverse_lookup():
    with patch("cli.commands.post_reverse_lookup", return_value="mock-task-id") as mock_post:
        yield mock_post


def test_validate_address_valid_inputs():
    assert validate_address("udp://8.8.8.8") == "8.8.8.8"
    assert validate_address("tcp://1.1.1.1:53") == "1.1.1.1"
    assert validate_address("https://dns.google") == "dns.google"
    assert validate_address("tls://one.one.one.one") == "one.one.one.one"
    assert validate_address("quic://example.com:853") == "example.com"


@pytest.mark.parametrize(
    "invalid",
    [
        "ftp://8.8.8.8",
        "just-a-string",
        "://missing.scheme",
        "udp//missing-colon.com",
        "udp:/one-slash.com",
    ],
)
def test_validate_address_invalid_inputs(invalid):
    with pytest.raises(ValueError, match="invalid server address format"):
        validate_address(invalid)


def test_sort_result_by_dns_server_normal_case():
    data = {
        "udp://8.8.8.8": {"dns_protocol": "Do53"},
        "tls://1.1.1.1": {"dns_protocol": "DoT"},
        "https://dns.google": {"dns_protocol": "DoH"},
    }

    sorted_result = sort_result_by_dns_server(data)

    assert [item[0] for item in sorted_result] == [
        "tls://1.1.1.1",
        "udp://8.8.8.8",
        "https://dns.google",
    ]


def test_sort_result_by_dns_server_and_none_protocol():
    data = {
        "udp://8.8.8.8": {"dns_protocol": "Do53"},
        "tcp://1.1.1.1": {"dns_protocol": None},
        "tls://1.1.1.1": {"dns_protocol": "DoT"},
    }

    sorted_result = sort_result_by_dns_server(data)

    assert [item[0] for item in sorted_result] == [
        "tls://1.1.1.1",
        "tcp://1.1.1.1",
        "udp://8.8.8.8",
    ]


@pytest.mark.parametrize(
    "domain_type,fallback,expected",
    [
        (SimpleNamespace(value="A"), "MX", "A"),
        (SimpleNamespace(value="AAA"), "A", "AAAA"),
        (SimpleNamespace(value="AAAA"), "A", "AAAA"),
        ("MX", "A", "MX"),
        (None, "CNAME", "CNAME"),
    ],
)
def test_normalize_qtype(domain_type, fallback, expected):
    assert normalize_qtype(domain_type, fallback) == expected


def test_collect_targets_from_file_and_query():
    args = SimpleNamespace(
        input_file="domains.txt",
        query="example.com",
    )

    with patch("cli.commands.input_file") as mock_input_file:
        mock_input_file.return_value = [
            SimpleNamespace(domain="openai.com", domain_type=SimpleNamespace(value="AAAA")),
            SimpleNamespace(domain="github.com", domain_type=SimpleNamespace(value="MX")),
        ]

        targets = collect_targets(args)

    assert targets == [
        ("openai.com", SimpleNamespace(value="AAAA")),
        ("github.com", SimpleNamespace(value="MX")),
        ("example.com", None),
    ]


def test_collect_targets_without_any_input():
    args = SimpleNamespace(input_file="", query="")

    with pytest.raises(ValueError, match="Provide a query or --input-file"):
        collect_targets(args)


def test_cli_version_flag(capsys):
    with patch("sys.argv", ["prog", "--version"]):
        with pytest.raises(SystemExit) as excinfo:
            launcher()

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert f"DNS Tester - version {PACKAGE_VERSION}" in captured.out


def test_main_direct_lookup(mock_post_dns_lookup, capsys):
    mock_status = [
        {"task_status": "PENDING"},
        make_success_status(),
    ]

    with patch("cli.commands.get_task_status", side_effect=mock_status) as mock_get:
        with patch("sys.argv", ["prog", "example.com", "udp://8.8.8.8", "--qtype", "A"]):
            launcher(
                post_dns_lookup_func=mock_post_dns_lookup,
                get_task_status_func=mock_get,
            )

    captured = capsys.readouterr()
    assert "Starting DNS lookup for domain: example.com (A)" in captured.out
    assert "udp://8.8.8.8 - Do53 - 30.50000ms - TTL: 300s - 93.184.216.34" in captured.out
    mock_post_dns_lookup.assert_called_once_with(
        "http://localhost:5000",
        "example.com",
        ["udp://8.8.8.8"],
        "A",
        False,
    )


def test_main_reverse_lookup(mock_post_reverse_lookup, capsys):
    mock_status = [
        {"task_status": "PENDING"},
        make_success_status(record_type="PTR", value="example.org", ttl=120),
    ]

    with patch("cli.commands.get_task_status", side_effect=mock_status) as mock_get:
        with patch("sys.argv", ["prog", "8.8.8.8", "udp://1.1.1.1", "--reverse"]):
            launcher(
                post_reverse_lookup_func=mock_post_reverse_lookup,
                get_task_status_func=mock_get,
            )

    captured = capsys.readouterr()
    assert "Starting Reverse DNS lookup for IP: 8.8.8.8" in captured.out
    assert "example.org" in captured.out
    mock_post_reverse_lookup.assert_called_once_with(
        "http://localhost:5000",
        "8.8.8.8",
        ["udp://1.1.1.1"],
        False,
    )


def test_main_input_file_multiple_domains(tmp_path, capsys):
    test_file = tmp_path / "domains.txt"
    test_file.write_text(
        "AAAA;cloudflare.com\n"
        "MX;gmail.com\n",
        encoding="utf-8",
    )

    post_mock = patch("cli.commands.post_dns_lookup", return_value="task-id").start()
    get_mock = patch("cli.commands.get_task_status").start()
    input_mock = patch("cli.commands.input_file").start()

    input_mock.return_value = [
        SimpleNamespace(domain="cloudflare.com", domain_type=SimpleNamespace(value="AAAA")),
        SimpleNamespace(domain="gmail.com", domain_type=SimpleNamespace(value="MX")),
    ]

    get_mock.side_effect = [
        {"task_status": "PENDING"},
        make_success_status(record_type="AAAA", value="2606:4700:4700::1111", ttl=300),
        {"task_status": "PENDING"},
        make_success_status(record_type="MX", value="alt1.gmail-smtp-in.l.google.com", ttl=600),
    ]

    try:
        with patch(
            "sys.argv",
            [
                "prog",
                "--input-file",
                str(test_file),
                "",
                "udp://8.8.8.8",
                "--pretty",
            ],
        ):
            launcher(
                post_dns_lookup_func=post_mock,
                get_task_status_func=get_mock,
            )
    finally:
        patch.stopall()

    captured = capsys.readouterr()
    assert "cloudflare.com" in captured.out
    assert "gmail.com" in captured.out
    assert "2606:4700:4700::1111" in captured.out
    assert "alt1.gmail-smtp-in.l.google.com" in captured.out

    assert post_mock.call_args_list == [
        call("http://localhost:5000", "cloudflare.com", ["udp://8.8.8.8"], "AAAA", False),
        call("http://localhost:5000", "gmail.com", ["udp://8.8.8.8"], "MX", False),
    ]


def test_main_shows_error_for_invalid_dns_server(capsys):
    with patch("sys.argv", ["prog", "example.com", "bad-server"]):
        launcher()

    captured = capsys.readouterr()
    assert "invalid server address format" in captured.out


def test_main_with_no_targets(capsys):
    with patch("cli.commands.input_file", return_value=[]):
        with patch("sys.argv", ["prog", "--input-file", "empty.txt"]):
            launcher()

    captured = capsys.readouterr()
    assert "Provide a query or --input-file" in captured.out