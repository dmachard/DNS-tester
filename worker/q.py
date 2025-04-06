import subprocess
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import worker.metrics

# Mapping des rcode et types DNS
RCODE_MAPPING = {
    0: "NOERROR",
    2: "SERVFAIL",
    3: "NXDOMAIN",
    5: "REFUSED",
}

TYPE_MAPPING = {
    1: "A",
    2: "NS",
    5: "CNAME",
    6: "SOA",
    12: "PTR",
    15: "MX",
    16: "TXT",
    28: "AAAA"
}

dnstester_logger = logging.getLogger('dnstester')


def _query_server(domain, qtype, server, tls_insecure_skip_verify):
    result = {}
    try:
        server_addr = server["target"]
        if server_addr.startswith("udp://"):
            server_addr = server_addr.replace("udp://", "")

        cmd = ["q", "--format=json", "@" + server_addr, domain, qtype]

        if qtype == "PTR":
            cmd.append("-x")
        if server["target"].startswith("https://"):
            cmd.append("--http2")
        if tls_insecure_skip_verify:
            cmd.append("--tls-insecure-skip-verify")

        dnstester_logger.debug(f"Executing command: {' '.join(cmd)}")

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if stdout:
            dnstester_logger.debug(f"output from q command: {stdout.decode('utf-8')}")
        if stderr:
            dnstester_logger.error(f"error from q command: {stderr.decode('utf-8')}")

        if process.returncode == 0:
            output_json = json.loads(stdout.decode('utf-8'))
            if not output_json:
                result = {
                    "command_status": "error",
                    "error": "JSON Output empty"
                }
            else:
                first_output = output_json[0]
                replies = first_output.get("replies", [])

                rcode_num = replies[0]["rcode"] if replies and "rcode" in replies[0] else "Unknown"
                rcode_text = RCODE_MAPPING.get(rcode_num, "Unknown")

                qtype_num = first_output["queries"][0]["question"][0]["qtype"] if first_output.get("queries") else "Unknown"
                qtype_text = TYPE_MAPPING.get(qtype_num, "Unknown")

                formatted_output = {
                    "description": server.get("description", ""),
                    "rcode": rcode_text,
                    "name": first_output["queries"][0]["question"][0]["name"] if first_output.get("queries") else "Unknown",
                    "qtype": qtype_text,
                    "answers": []
                }

                for reply in replies:
                    if "answer" in reply and reply["answer"]:
                        for ans in reply["answer"]:
                            value = next((ans.get(k) for k in ["a", "aaaa", "ptr", "ns", "target", "txt", "mx", "soa"] if ans.get(k)), "Unknown")
                            formatted_output["answers"].append({
                                "name": ans["hdr"]["name"],
                                "type": TYPE_MAPPING.get(ans["hdr"]["rrtype"], "Unknown"),
                                "ttl": ans["hdr"]["ttl"],
                                "value": value
                            })

                result = {
                    "command_status": "ok",
                    "time_ms": first_output["time"] / 1_000_000,
                    **formatted_output
                }
        else:
            result = {
                "command_status": "error",
                "error": f"Process returned code {process.returncode}: {stderr.decode('utf-8') or 'Unknown error'}"
            }

    except Exception as e:
        result = {
            "command_status": "error",
            "error": str(e)
        }

    return server["target"], result


def run_q(domain, qtype, dns_servers, tls_insecure_skip_verify):
    dnstester_logger.debug(f"run_q called with: {domain} {qtype} {dns_servers} {tls_insecure_skip_verify}")

    results = {}

    with ThreadPoolExecutor(max_workers=len(dns_servers)) as executor:
        futures = [
            executor.submit(_query_server, domain, qtype, server, tls_insecure_skip_verify)
            for server in dns_servers
        ]

        for future in as_completed(futures):
            server_target, result = future.result()
            results[server_target] = result

    # Update Prometheus metrics
    for server, result in results.items():
        if result.get("command_status") == "ok":
            response_time_sec = result["time_ms"] / 1000

            worker.metrics.dns_total_queries.labels(server=server).inc()
            worker.metrics.dns_response_time.labels(server=server).observe(response_time_sec)
            worker.metrics.dns_avg_response_time.labels(server=server).set(response_time_sec)
            worker.metrics.dns_query_types_count.labels(qtype=result["qtype"]).inc()

            if result["rcode"] == "NOERROR":
                worker.metrics.dns_noerror_count.labels(server=server).inc()
            else:
                worker.metrics.dns_failure_count.labels(server=server, rcode=result["rcode"]).inc()

    return results
