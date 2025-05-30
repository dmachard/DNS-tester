import time
import requests
import argparse
import ipaddress
import re
import sys

from cli.version import PACKAGE_VERSION

API_BASE_URL = "http://localhost:5000"

def post_dns_lookup(domain, dns_servers=None, qtype="A", tls_insecure_skip_verify=False):
    payload = {
        "domain": domain,
        "dns_servers": [{"target": dns} for dns in dns_servers] if dns_servers else None,
        "qtype": qtype,
        "tls_insecure_skip_verify": tls_insecure_skip_verify
    }
    response = requests.post(f"{API_BASE_URL}/dns-lookup", json=payload)
    response.raise_for_status()
    return response.json()["task_id"]

def post_reverse_lookup(ip, dns_servers=None, tls_insecure_skip_verify=False):
    payload = {
        "reverse_ip": ip,
        "dns_servers": [{"target": dns} for dns in dns_servers] if dns_servers else None,
        "tls_insecure_skip_verify": tls_insecure_skip_verify
    }
    response = requests.post(f"{API_BASE_URL}/reverse-lookup", json=payload)
    response.raise_for_status()
    return response.json()["task_id"]

def get_task_status(task_id):
    response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()

def validate_ip(ip_string):
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False

def validate_address(server_address):
    match = re.match(r'^(udp|tcp|tls|https|quic)://([^:/]+)', server_address)
    if not match:
        raise ValueError(f"invalid server address format: {server_address}")
    return match.group(2)

def sort_result_by_dns_server(result):
    sorted_result = sorted(result.items(), key=lambda item: (validate_address(item[0]), item[1].get("dns_protocol") or "unknown"))
    return sorted_result

def log_result(level, message, use_emoji=False):
    """Log a message with emoji or ASCII fallback based on encoding support."""
    symbols = {
        "ok":    "✅ " if use_emoji else "[OK]",
        "warn":  "⚠️ " if use_emoji else "[WARN] ",
        "error": "❌ " if use_emoji else "[FAILED] ",
    }
    print(f"{symbols.get(level, '[???]')} {message}")

def launcher(post_dns_lookup_func=post_dns_lookup, post_reverse_lookup_func=post_reverse_lookup, get_task_status_func=get_task_status):
    global API_BASE_URL

    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"DNS Tester - version {PACKAGE_VERSION}")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="CLI for testing DNS lookup.")
    parser.add_argument("query", help="Domain name to query.")
    parser.add_argument("dns_servers", nargs="*", help="List of DNS servers (e.g., udp://8.8.8.8 or tcp://..., tls://...). If not provided, servers will be fetched from inventory.")
    parser.add_argument("--qtype", default="A", choices=["A", "AAAA"], help="DNS query type (default: A).")
    parser.add_argument("--reverse", "-r", action="store_true", help="Perform a reverse DNS lookup (PTR record).")
    parser.add_argument("--api-url", default=API_BASE_URL, help="Base URL of the API (default: http://localhost:5000).")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate verification.")
    parser.add_argument("--version", "-v", action="store_true", help="Show package version and exit.")
    parser.add_argument("--debug", "-d", action="store_true", help="Show detailed error messages for failed lookups.")
    parser.add_argument("--pretty", "-p", action="store_true", help="Enable emoji-enhanced output.")
    parser.add_argument( "--warn-threshold",type=float,default=1.0, help="Response time threshold in seconds for warnings (default: 1.0s).")
    args = parser.parse_args()


    API_BASE_URL = args.api_url

    is_reverse = args.reverse or validate_ip(args.query)
    
    if is_reverse:
        print(f"Starting Reverse DNS lookup for IP: {args.query} ")
        query_type = "PTR"
    else:
        print(f"Starting DNS lookup for domain: {args.query} ")
        query_type = args.qtype

    try:
        for dns_server in args.dns_servers:
            validate_address(dns_server)
    except ValueError as e:
        print(f"Error > {e}")
        return

    if args.debug:
        print(f"\tUsing DNS servers: {', '.join(args.dns_servers) if args.dns_servers else 'Fetching from inventory'}")
        print(f"\tQuery type: {query_type}")
        print(f"\tAPI Base URL: {API_BASE_URL}")
        print(f"\tTLS Skip Verify: {args.insecure}")
    
    try:
        if is_reverse:
            task_id = post_reverse_lookup_func(args.query, args.dns_servers, args.insecure)
        else:
            task_id = post_dns_lookup_func(args.query, args.dns_servers, args.qtype, args.insecure)
        if args.debug:
            print(f"\tTask ID: {task_id}")

        while True:
            task_status = get_task_status_func(task_id)
            if task_status["task_status"] == "SUCCESS":

               
                nb_commands_ok = sum(
                                    1 for result in task_status["task_result"]["details"].values()
                                    if result["command_status"] == "ok"
                                )
                nb_commands = len(task_status["task_result"]["details"])
                total_duration = task_status["task_result"]["duration"]

                print(
                    "\nDNS lookup succeeded for %d out of %d servers (%.4f seconds total)"
                    % (nb_commands_ok, nb_commands, total_duration)
                )
                
                for server, result in sort_result_by_dns_server(task_status["task_result"]["details"]):
                    if result["command_status"] == "ok":
                        dns_protocol = result["dns_protocol"]
                        rcode = result.get("rcode", "Unknown")
                        if rcode != "NOERROR":
                            if rcode == "NXDOMAIN":
                                log_result("warn", f"{server} - Domain does not exist (rcode: NXDOMAIN) - {result['time_ms']:.2f} ms", args.pretty)
                            else:
                                log_result("warn", f"{server} - No valid answer (rcode: {rcode}) - {result['time_ms']:.2f} ms", args.pretty)
                        else:
                            record_type = "PTR" if is_reverse else query_type
                            answers = [
                                (ans["value"], ans["ttl"])
                                for ans in result["answers"]
                                if ans["type"] == record_type
                            ]
                            if answers:
                                values = [value for value, _ in answers]
                                ttl_list = [ttl for _, ttl in answers]
                                time_ms = result["time_ms"]
                                time_sec = time_ms / 1000
                                
                                # Determine log level based on threshold
                                level = "warn" if time_sec > args.warn_threshold else "ok"

                                if len(set(ttl_list)) == 1:
                                    log_result(level, f"{server} - {dns_protocol} - {time_ms:.5f}ms - TTL: {ttl_list[0]}s - {', '.join(values)}", args.pretty)
                                else:
                                    value_with_ttl = [f"{ip} (TTL: {ttl})" for ip, ttl in answers]
                                    log_result(level, f"{server} - {dns_protocol} - {time_ms:.5f}ms - {', '.join(value_with_ttl)}", args.pretty)
                            else:
                                log_result("warn", f"{server} - {dns_protocol} - No {record_type} records found - {result['time_ms']} ms", args.pretty)
                    else:
                        if args.debug:
                            log_result("error", f"{server} - connection issue or error: {result['error']}", args.pretty)
                        else:
                            log_result("error", f"{server} - connection issue or error", args.pretty)
                break
            elif task_status["task_status"] == "FAILURE":
                print("\tTask failed.")
                break
            else:
                if args.debug:
                    print("\tWaiting for task to complete...")
                time.sleep(1)
    except requests.RequestException as e:
        print(f"Error: {e}")
