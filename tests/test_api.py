from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.app import app

import pytest

client = TestClient(app)

def test_health_check():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("worker.lookup.lookup_dns.delay", return_value=MagicMock(id="fake-task-id"))
def test_post_dnslookup_get_taskid(mock_celery):
    data = {
        "domain": "example.com",
        "dns_servers": [ {"target": "udp://8.8.8.8:53", "description": ""}, {"target": "tls://1.1.1.1:853", "description": ""}],
        "qtype": "A"
    }
    response = client.post("/dns-lookup", json=data)

    assert response.status_code == 200
    assert response.json() == {"task_id": "fake-task-id", "message": "DNS lookup enqueued"}
    mock_celery.assert_called_once_with("example.com", "A", [{"target": "udp://8.8.8.8:53", "description": ""}, {"target": "tls://1.1.1.1:853", "description": ""}], False)

@pytest.mark.parametrize("valid_qtype", ["A", "AAAA", "CNAME", "PTR", "TXT"])
@patch("worker.lookup.lookup_dns.delay", return_value=MagicMock(id="fake-task-id"))
def test_post_dnslookup_valid_qtype(mock_celery, valid_qtype):
    response = client.post(
        "/dns-lookup",
        json={"domain": "example.com", "dns_servers": [ {"target": "udp://8.8.8.8:53", "description": ""} ], "qtype": valid_qtype}
    )
    assert response.status_code == 200
    assert "task_id" in response.json()
    mock_celery.assert_called_once_with("example.com", valid_qtype, [{"target": "udp://8.8.8.8:53", "description": ""}], False)

@pytest.mark.parametrize("invalid_qtype", ["MX", "SRV", "WRONG_TYPE", "123"])
@patch("worker.lookup.lookup_dns.delay", return_value=MagicMock(id="fake-task-id"))
def test_post_dnslookup_invalid_qtype(mock_celery, invalid_qtype):
    response = client.post(
        "/dns-lookup",
        json={"domain": "example.com", "dns_servers": [ {"target": "udp://8.8.8.8:53"} ], "qtype": invalid_qtype}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.parametrize("valid_server", [
    {"target": "udp://8.8.8.8:53"}, {"target": "tcp://1.1.1.1"},  {"target": "https://dns.google"}, {"target": "quic://9.9.9.9"}, {"target": "tls://dns.cloudflare.com"}
])
@patch("worker.lookup.lookup_dns.delay", return_value=MagicMock(id="fake-task-id"))
def test_post_dnslookup_valid_dns_server(mock_celery, valid_server):
    response = client.post(
        "/dns-lookup",
        json={"domain": "example.com", "dns_servers": [valid_server], "qtype": "A"}
    )
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.parametrize("invalid_server", [
    {"target": "8.8.8.8"},  {"target": "1.1.1.1:53"},  {"target": "ftp://8.8.8.8"}, {"target": "dns.google"}, {"target": "://9.9.9.9"}      
])
@patch("worker.lookup.lookup_dns.delay", return_value=MagicMock(id="fake-task-id"))
def test_post_dnslookup_invalid_dns_server(mock_celery, invalid_server):
    response = client.post(
        "/dns-lookup",
        json={"domain": "example.com", "dns_servers": [invalid_server], "qtype": "A"}
    )
    assert response.status_code == 422  # Erreur de validation attendue
    assert "detail" in response.json()

@patch("worker.lookup.lookup_dns.AsyncResult")
def test_get_tasks_status(mock_async_result):
    mock_async_result.return_value.state = "SUCCESS"
    mock_async_result.return_value.result = {
        "udp://8.8.8.8:53": {
            "command_status": "ok",
            "time_ms": 13.9,
            "rcode": "NoError",
            "name": "example.com.",
            "qtype": "A",
            "answers": [
                {
                    "name": "example.com.",
                    "type": "A",
                    "ttl": 190,
                    "value": "93.184.216.34"
                }
            ]
        }
    }

    response = client.get("/tasks/fake-task-id")

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "fake-task-id",
        "task_status": "SUCCESS",
        "result": {
            "udp://8.8.8.8:53": {
                "command_status": "ok",
                "error": None,
                "time_ms": 13.9,
                "rcode": "NoError",
                "name": "example.com.",
                "qtype": "A",
                "answers": [
                    {
                        "name": "example.com.",
                        "type": "A",
                        "ttl": 190,
                        "value": "93.184.216.34"
                    }
                ]
            }
        }
    }

    mock_async_result.assert_called_once_with("fake-task-id")