import subprocess
import json

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

def run_q(domain, qtype, dns_servers, tls_insecure_skip_verify):
    results = {}
    
    for server in dns_servers:
        try:
            # Clean the server string
            server_addr = server
            if server.startswith("udp://"):
                server_addr = server.replace("udp://", "")

            # Execute q command
            cmd = ["q", "--format=json", "@" + server_addr, domain, qtype]

            # Usage HTTP2 for DoH
            if server.startswith("https://"):
                cmd.append("--http2")

            # Insecure TLS verification?
            if tls_insecure_skip_verify:
                cmd.append("--tls-insecure-skip-verify")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                output_json = json.loads(stdout.decode('utf-8'))
                if not len(output_json):
                    results[server] = {
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
                                        or ans.get("ns") or ans.get("cname") or ans.get("txt")
                                        or ans.get("mx") or ans.get("soa") 
                                })
                    
                    results[server] = {
                        "command_status": "ok",
                        "time_ms": first_output["time"] / 1_000_000,
                        **formatted_output
                    }

            else:
                error_output = stderr.decode('utf-8') or "Unknown error"
                results[server] = {
                    "command_status": "error",
                    "error": f"Process returned code {process.returncode}: {error_output}"
                }
        except Exception as e:
            results[server] = {
                "command_status": "error",
                "error": str(e)
            }
    
    return results