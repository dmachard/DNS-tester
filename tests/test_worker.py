import json

from unittest.mock import patch, MagicMock
from worker.q import run_q

MOCK_Q_SUCCESS_OUTPUT = b'''
[
    {
        "queries": [
            {
                "id": 12345,
                "question": [{"name": "example.com.", "qtype": 1, "qclass": 1}]
            }
        ],
        "replies": [
            {
                "id": 12345,
                "rcode": 0,
                "question": [{"name": "example.com.", "qtype": 1, "qclass": 1}],
                "answer": [
                    {
                        "hdr": {"name": "example.com.", "rrtype": 1, "class": 1, "ttl": 300, "rdlength": 4},
                        "a": "93.184.216.34"
                    }
                ]
            }
        ],
        "server": "8.8.8.8:53",
        "time": 12000000
    }
]
'''

@patch("subprocess.Popen")
def test_run_q_success(mock_popen):
    """Test successful execution of q"""
    mock_process = MagicMock()
    mock_process.communicate.return_value = (MOCK_Q_SUCCESS_OUTPUT, b"")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    result = run_q("example.com", "A", ["udp://8.8.8.8"], False)

    # Check if server key exists in results
    assert "udp://8.8.8.8" in result
    server_result = result["udp://8.8.8.8"]

    assert server_result["command_status"] == "ok"
    assert server_result["time_ms"] == 12
    assert server_result["rcode"] == "NOERROR"
    assert server_result["name"] == "example.com."
    assert server_result["qtype"] == "A"

    # Ensure there's at least one answer
    assert "answers" in server_result
    assert len(server_result["answers"]) == 1

     # Validate the DNS answer
    answer = server_result["answers"][0]
    assert answer["name"] == "example.com."
    assert answer["type"] == "A"
    assert answer["ttl"] == 300
    assert answer["value"] == "93.184.216.34"