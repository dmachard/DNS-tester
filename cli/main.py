import time
import requests
import argparse

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

def get_task_status(task_id):
    response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
    response.raise_for_status()
    return response.json()

def main(post_dns_lookup_func=post_dns_lookup, get_task_status_func=get_task_status):
    global API_BASE_URL

    parser = argparse.ArgumentParser(description="CLI for testing DNS lookup.")
    parser.add_argument("domain", help="Domain name to query.")
    parser.add_argument("dns_servers", nargs="*", help="List of DNS servers (e.g., udp://8.8.8.8). If not provided, servers will be fetched from inventory.")
    parser.add_argument("--qtype", default="A", choices=["A", "AAAA"], help="DNS query type (default: A).")
    parser.add_argument("--api-url", default=API_BASE_URL, help="Base URL of the API (default: http://localhost:5000).")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate verification.")
    args = parser.parse_args()

    API_BASE_URL = args.api_url

    print(f"Starting DNS lookup for domain: {args.domain}")
    print(f"\tUsing DNS servers: {', '.join(args.dns_servers) if args.dns_servers else 'Fetching from inventory'}")
    print(f"\tAPI Base URL: {API_BASE_URL}")
    print(f"\tTLS Skip Verify: {args.insecure}")
    
    try:
        task_id = post_dns_lookup_func(args.domain, args.dns_servers, args.qtype, args.insecure)
        print(f"\tTask ID: {task_id}")

        while True:
            task_status = get_task_status_func(task_id)
            if task_status["task_status"] == "SUCCESS":
                print("\nDNS Lookup Results:")
                for server, result in task_status["task_result"]["details"].items():
                    if result["command_status"] == "ok":
                        rcode = result.get("rcode", "Unknown")
                        if rcode != "NOERROR":
                            print(f"{server} - No valid answer (rcode: {rcode}) - {result['time_ms']} ms")
                        else:
                            final_answers = [
                                f"{ans['value']} (TTL: {ans['ttl']})"
                                for ans in result["answers"]
                                if ans["type"] in ["A", "AAAA"]
                            ]
                            if final_answers:
                                print(f"\t{server} - {', '.join(final_answers)} - {result['time_ms']} ms")
                            else:
                                print(f"\t{server} - No A or AAAA records found - {result['time_ms']} ms")
                    else:
                        rcode = result.get("rcode", "Unknown")
                        print(f"\t- {server} - Error: {result['error']} (rcode: {rcode})")
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