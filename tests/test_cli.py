import pytest
from unittest.mock import patch, MagicMock
from cli.main import main

@pytest.fixture
def mock_post_dns_lookup():
    with patch("cli.main.post_dns_lookup") as mock_post:
        mock_post.return_value = "mock-task-id"
        yield mock_post

@pytest.fixture
def mock_get_task_status():
    with patch("cli.main.get_task_status") as mock_get:
        mock_get.side_effect = [
            {"task_status": "PENDING"},
            {"task_status": "SUCCESS", "task_result": {"details": {
                "udp://8.8.8.8": {
                    "command_status": "ok",
                    "rcode": "NOERROR",
                    "time_ms": 30.5,
                    "answers": [
                        {"value": "93.184.216.34", "type": "A", "ttl": 300}
                    ]
                }
            }}}
        ]
        yield mock_get

def test_main(mock_post_dns_lookup, mock_get_task_status, capsys):
    # Simulate command-line arguments
    with patch("sys.argv", ["main.py", "example.com", "udp://8.8.8.8", "--qtype", "A"]):
        # Pass mocked functions to main
        main(post_dns_lookup_func=mock_post_dns_lookup, get_task_status_func=mock_get_task_status)
    
    # Capture the output
    captured = capsys.readouterr()
    
    # Assertions
    assert "mock-task-id" in captured.out
    assert "udp://8.8.8.8 - 93.184.216.34 (TTL: 300) - 30.5 ms" in captured.out