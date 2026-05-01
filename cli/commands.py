import argparse
import ipaddress
import re
import sys
import time
from typing import Any

import requests

from cli.version import PACKAGE_VERSION
from cli.domains_from_file import input_file

API_BASE_URL = "http://localhost:5000"


def post_dns_lookup(api_url: str, domain: str, dns_servers=None, qtype: str = "A", tls_insecure_skip_verify: bool = False):
    payload = {
        "domain": domain,
        "dns_servers": [{"target": dns} for dns in dns_servers] if dns_servers else None,
        "qtype": qtype,
        "tls_insecure_skip_verify": tls_insecure_skip_verify,
    }
    response = requests.post(f"{api_url}/dns-lookup", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["task_id"]


def post_reverse_lookup(api_url: str, ip: str, dns_servers=None, tls_insecure_skip_verify: bool = False):
    payload = {
        "reverse_ip": ip,
        "dns_servers": [{"target": dns} for dns in dns_servers] if dns_servers else None,
        "tls_insecure_skip_verify": tls_insecure_skip_verify,
    }
    response = requests.post(f"{api_url}/reverse-lookup", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["task_id"]


def get_task_status(api_url: str, task_id: str):
    response = requests.get(f"{api_url}/tasks/{task_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def validate_ip(ip_string: str) -> bool:
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def validate_address(server_address: str) -> str:
    match = re.match(r"^(udp|tcp|tls|https|quic)://([^:/]+)", server_address.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"invalid server address format: {server_address}")
    return match.group(2)


def sort_result_by_dns_server(result: dict[str, Any]):
    return sorted(
        result.items(),
        key=lambda item: (validate_address(item[0]), str(item[1].get("dns_protocol") or "unknown")),
    )


def log_result(level: str, message: str, use_emoji: bool = False):
    symbols = {
        "ok": "✅ " if use_emoji else "[OK] ",
        "warn": "⚠️ " if use_emoji else "[WARN] ",
        "error": "❌ " if use_emoji else "[FAILED] ",
    }
    print(f"{symbols.get(level, '[???] ')}{message}")


def normalize_qtype(domain_type: Any, fallback: str) -> str:
    if domain_type is None:
        return fallback
    value = getattr(domain_type, "value", domain_type)
    if value is None:
        return fallback
    qtype = str(value).upper()
    return "AAAA" if qtype == "AAA" else qtype


def collect_targets(args) -> list[tuple[str, Any]]:
    targets: list[tuple[str, Any]] = []

    if args.input_file:
        for record in input_file(args.input_file):
            targets.append((record.domain, getattr(record, "domain_type", None)))

    if args.query:
        targets.append((args.query, None))

    if not targets:
        raise ValueError("Provide a query or --input-file.")

    return targets


def print_lookup_result(task_status: dict[str, Any], qtype: str, is_reverse: bool, args):
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
        if result["command_status"] != "ok":
            if args.debug:
                log_result("error", f"{server} - connection issue or error: {result['error']}", args.pretty)
            else:
                log_result("error", f"{server} - connection issue or error", args.pretty)
            continue

        dns_protocol = result.get("dns_protocol", "unknown")
        rcode = result.get("rcode", "Unknown")

        if rcode != "NOERROR":
            if rcode == "NXDOMAIN":
                log_result(
                    "warn",
                    f"{server} - Domain does not exist (rcode: NXDOMAIN) - {result['time_ms']:.2f} ms",
                    args.pretty,
                )
            else:
                log_result(
                    "warn",
                    f"{server} - No valid answer (rcode: {rcode}) - {result['time_ms']:.2f} ms",
                    args.pretty,
                )
            continue

        record_type = "PTR" if is_reverse else qtype
        answers = [
            (ans["value"], ans["ttl"])
            for ans in result.get("answers", [])
            if ans.get("type") == record_type
        ]

        if not answers:
            log_result(
                "warn",
                f"{server} - {dns_protocol} - No {record_type} records found - {result['time_ms']} ms",
                args.pretty,
            )
            continue

        values = [value for value, _ in answers]
        ttl_list = [ttl for _, ttl in answers]
        time_ms = float(result["time_ms"])
        time_sec = time_ms / 1000.0
        level = "warn" if time_sec > args.warn_threshold else "ok"

        if len(set(ttl_list)) == 1:
            log_result(
                level,
                f"{server} - {dns_protocol} - {time_ms:.5f}ms - TTL: {ttl_list[0]}s - {', '.join(values)}",
                args.pretty,
            )
        else:
            value_with_ttl = [f"{value} (TTL: {ttl})" for value, ttl in answers]
            log_result(
                level,
                f"{server} - {dns_protocol} - {time_ms:.5f}ms - {', '.join(value_with_ttl)}",
                args.pretty,
            )


def run_single_lookup(
    api_url: str,
    target: str,
    target_type: Any,
    dns_servers: list[str],
    args,
    post_dns_lookup_func=post_dns_lookup,
    post_reverse_lookup_func=post_reverse_lookup,
    get_task_status_func=get_task_status,
):
    is_reverse = args.reverse or validate_ip(target)
    qtype = "PTR" if is_reverse else normalize_qtype(target_type, args.qtype)

    if is_reverse:
        print(f"Starting Reverse DNS lookup for IP: {target}", end="", flush=True)
    else:
        print(f"Starting DNS lookup for domain: {target} ({qtype})", end="", flush=True)

    if args.debug:
        print(f"\n\tUsing DNS servers: {', '.join(dns_servers) if dns_servers else 'Fetching from inventory'}")
        print(f"\tQuery type: {qtype}")
        print(f"\tAPI Base URL: {api_url}")
        print(f"\tTLS Skip Verify: {args.insecure}")

    try:
        if is_reverse:
            task_id = post_reverse_lookup_func(api_url, target, dns_servers, args.insecure)
        else:
            task_id = post_dns_lookup_func(api_url, target, dns_servers, qtype, args.insecure)

        if args.debug:
            print(f"\tTask ID: {task_id}")

        while True:
            task_status = get_task_status_func(api_url, task_id)

            if task_status["task_status"] == "SUCCESS":
                print_lookup_result(task_status, qtype, is_reverse, args)
                return

            if task_status["task_status"] == "FAILURE":
                print("\tTask failed.")
                return

            print(".", end="", flush=True)
            time.sleep(0.5)

    except requests.RequestException as e:
        print(f"Error: {e}")


def launcher(post_dns_lookup_func=post_dns_lookup, post_reverse_lookup_func=post_reverse_lookup, get_task_status_func=get_task_status):
    parser = argparse.ArgumentParser(description="CLI for testing DNS lookup.")
    parser.add_argument("query", nargs="?", default="", help="Domain name or IP address to query.")
    parser.add_argument(
        "dns_servers",
        nargs="*",
        help="List of DNS servers (e.g. udp://8.8.8.8 or tcp://..., tls://...). If not provided, servers will be fetched from inventory.",
    )
    parser.add_argument("--qtype", default="A", choices=["A", "AAAA", "MX", "CNAME"], help="DNS query type (default: A).")
    parser.add_argument("--reverse", "-r", action="store_true", help="Perform a reverse DNS lookup (PTR record).")
    parser.add_argument("--api-url", default=API_BASE_URL, help="Base URL of the API (default: http://localhost:5000).")
    parser.add_argument("--insecure", action="store_true", help="Skip TLS certificate verification.")
    parser.add_argument("--version", "-v", action="store_true", help="Show package version and exit.")
    parser.add_argument("--debug", "-d", action="store_true", help="Show detailed error messages for failed lookups.")
    parser.add_argument("--pretty", "-p", action="store_true", help="Enable emoji-enhanced output.")
    parser.add_argument(
        "--warn-threshold",
        type=float,
        default=1.0,
        help="Response time threshold in seconds for warnings (default: 1.0s).",
    )
    parser.add_argument("--input-file", type=str, default="", help="File with domains to query.")
    args = parser.parse_args()

    if args.version:
        print(f"DNS Tester - version {PACKAGE_VERSION}")
        sys.exit(0)

    try:
        for dns_server in args.dns_servers:
            validate_address(dns_server)
    except ValueError as e:
        print(f"Error > {e}")
        return

    try:
        targets = collect_targets(args)
    except ValueError as e:
        print(f"Error > {e}")
        return

    for index, (target, target_type) in enumerate(targets, start=1):
        if len(targets) > 1:
            print(f"\n[{index}/{len(targets)}] {target}")
        run_single_lookup(
            args.api_url,
            target,
            target_type,
            args.dns_servers,
            args,
            post_dns_lookup_func=post_dns_lookup_func,
            post_reverse_lookup_func=post_reverse_lookup_func,
            get_task_status_func=get_task_status_func,
        )
