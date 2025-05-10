import time
import requests
import argparse
import ipaddress

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
    
def main(post_dns_lookup_func=post_dns_lookup, post_reverse_lookup_func=post_reverse_lookup, get_task_status_func=get_task_status):
    global API_BASE_URL

    parser = argparse.ArgumentParser(description="CLI for testing DNS lookup.")
    parser.add_argument("query", help="Domain name to query.")
    parser.add_argument("dns_servers", nargs="*", help="List of DNS servers (e.g., udp://8.8.8.8). If not provided, servers will be fetched from inventory.")
    parser.add_argument("--qtype", default="A", choices=["A", "AAAA"], help="DNS query type (default: A).")
    parser.add_argument("--reverse", "-r", action="store_true", help="Perform a reverse DNS lookup (PTR record).")
    parser.add_argument("--api-url", default=API_BASE_URL, help="Base URL of the API (default: http://localhost:5000).")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate verification.")
    args = parser.parse_args()

    API_BASE_URL = args.api_url

    is_reverse = args.reverse or validate_ip(args.query)
    
    if is_reverse:
        print(f"Starting Reverse DNS lookup for IP: {args.query}")
        query_type = "PTR"
    else:
        print(f"Starting DNS lookup for domain: {args.query}")
        query_type = args.qtype

    print(f"\tUsing DNS servers: {', '.join(args.dns_servers) if args.dns_servers else 'Fetching from inventory'}")
    print(f"\tQuery type: {query_type}")
    print(f"\tAPI Base URL: {API_BASE_URL}")
    print(f"\tTLS Skip Verify: {args.insecure}")
    
    try:
        if is_reverse:
            task_id = post_reverse_lookup_func(args.query, args.dns_servers, args.insecure)
        else:
            task_id = post_dns_lookup_func(args.query, args.dns_servers, args.qtype, args.insecure)
        print(f"\tTask ID: {task_id}")

        while True:
            task_status = get_task_status_func(task_id)
            if task_status["task_status"] == "SUCCESS":
                print("\nDNS lookup of %d servers completed in %.4fs:" % (len(task_status["task_result"]["details"]), task_status["task_result"]["duration"]) )
                for server, result in task_status["task_result"]["details"].items():
                    dns_protocol = result["dns_protocol"]
                    if result["command_status"] == "ok":
                        rcode = result.get("rcode", "Unknown")
                        if rcode != "NOERROR":
                            print(f"\t{server} - No valid answer (rcode: {rcode}) - {result['time_ms']} ms")
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

                                if len(set(ttl_list)) == 1:
                                    print(f"\t{server} - {dns_protocol} - {time_ms:.5f}ms - TTL: {ttl_list[0]}s - {', '.join(values)}")
                                else:
                                    value_with_ttl = [f"{ip} (TTL: {ttl})" for ip, ttl in answers]
                                    print(f"\t{server} - {dns_protocol} - {time_ms:.5f}ms - {', '.join(value_with_ttl)}")
                            else:
                                print(f"\t{server} - {dns_protocol} - No {record_type} records found - {result['time_ms']} ms")
                    else:
                        rcode = result.get("rcode", "Unknown")
                        print(f"\t- {server} - {dns_protocol} - Error: {result['error']} (rcode: {rcode})")
                break
            elif task_status["task_status"] == "FAILURE":
                print("\tTask failed.")
                break
            else:
                print("\tWaiting for task to complete...")
                time.sleep(1)
    except requests.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()