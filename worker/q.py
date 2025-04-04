import subprocess
import json
import logging

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

def run_q(domain, qtype, dns_servers, tls_insecure_skip_verify):
    dnstester_logger.debug(f"run_q called with: {domain} {qtype} {dns_servers} {tls_insecure_skip_verify}")

    results = {}
    
    for server in dns_servers:
        try:
            # Clean the server string
            server_addr = server["target"]
            if server["target"].startswith("udp://"):
                server_addr = server["target"].replace("udp://", "")

            # Execute q command
            cmd = ["q", "--format=json", "@" + server_addr, domain, qtype]

            # Usage HTTP2 for DoH
            if server["target"].startswith("https://"):
                cmd.append("--http2")

            # Insecure TLS verification?
            if tls_insecure_skip_verify:
                cmd.append("--tls-insecure-skip-verify")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # Log the output
            if stdout:
                dnstester_logger.debug(f"output from q command: {stdout.decode('utf-8')}")
            if stderr:
                dnstester_logger.error(f"error from q command: {stderr.decode('utf-8')}")

            if process.returncode == 0:
                output_json = json.loads(stdout.decode('utf-8'))
                if not len(output_json):
                    results[server["target"]] = {
                        "command_status": "error",
                        "error": "JSON Output empty"
                    }
                else:
                    first_output = output_json[0]
                    replies = first_output.get("replies", [])

                    rcode_num = replies[0]["rcode"] if replies else "Unknown"
                    rcode_text = RCODE_MAPPING.get(rcode_num, "Unknown")

                    qtype_num = first_output["queries"][0]["question"][0]["qtype"] if first_output.get("queries") else "Unknown"
                    qtype_text = TYPE_MAPPING.get(qtype_num, "Unknown")

                    formatted_output = {
                        "target_description": server.get("description", ""),
                        "rcode": rcode_text,
                        "name": first_output["queries"][0]["question"][0]["name"] if first_output.get("queries") else "Unknown",
                        "qtype": qtype_text,
                        "answers": []
                    }

                    for reply in replies:
                        if "answer" in reply and reply["answer"]:
                            for ans in reply["answer"]:
                                formatted_output["answers"].append({
                                    "name": ans["hdr"]["name"],
                                    "type": TYPE_MAPPING.get(ans["hdr"]["rrtype"], "Unknown"),
                                    "ttl": ans["hdr"]["ttl"],
                                    "value": ans.get("a") or ans.get("aaaa") or ans.get("ptr") 
                                        or ans.get("ns") or ans.get("target") or ans.get("txt")
                                        or ans.get("mx") or ans.get("soa") 
                                })
                    
                    results[server["target"]] = {
                        "command_status": "ok",
                        "time_ms": first_output["time"] / 1_000_000,
                        **formatted_output
                    }

            else:
                error_output = stderr.decode('utf-8') or "Unknown error"
                results[server["target"]] = {
                    "command_status": "error",
                    "error": f"Process returned code {process.returncode}: {error_output}"
                }
        except Exception as e:
            results[server["target"]] = {
                "command_status": "error",
                "error": str(e)
            }
    
    # Update Prometheus metrics
    for server, result in results.items():
        if 'command_status' in result and result["command_status"] == "ok" :
            response_time_sec = result["time_ms"] / 1000  # Convert ms → seconds
            
            # Increment total queries count
            worker.metrics.dns_total_queries.labels(server=server).inc()
            
            # Observe response time histogram
            worker.metrics.dns_response_time.labels(server=server).observe(response_time_sec)
            
            # pdate latest response time
            worker.metrics.dns_avg_response_time.labels(server=server).set(response_time_sec)
            
            # Increment query type count (A, AAAA, CNAME, etc.)
            worker.metrics.dns_query_types_count.labels(qtype=result["qtype"]).inc()
            
            # Increment successful resolution count
            if result["rcode"] == "NOERROR":
                worker.metrics.dns_noerror_count.labels(server=server).inc()
            else:
                # Increment failed resolution count (NXDOMAIN, SERVFAIL...)
                worker.metrics.dns_failure_count.labels(server=server, rcode=result["rcode"]).inc()


    return results