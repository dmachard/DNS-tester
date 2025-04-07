import subprocess
import json
import logging

dnstester_logger = logging.getLogger('dnstester')

def read_inventory(inventory_path):
    command = f'ansible-inventory -i {inventory_path} --list'
    process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    inventory = json.loads(process.stdout)
    return inventory

def read_hosts_from_inventory(inventory_path):
    try:
        inventory = read_inventory(inventory_path)
        all_hosts = inventory.get('all', {}).get('children', [])
        dns_servers = []
        for group in all_hosts:
            hosts = inventory.get(group, {}).get('hosts', [])
            for host in hosts:
                host_vars = inventory['_meta']['hostvars'].get(host, {})
                dns_info = {
                    'dns_address': host_vars.get('dns_address'),
                    'domain_name': host_vars.get('domain_name'),
                    'services': host_vars.get('services'),
                    'details': host_vars.get('details'),
                }
                dns_servers.append(dns_info)
    except subprocess.CalledProcessError as e:
        dnstester_logger.error(f"Error reading inventory: {e.stderr.decode()}")
        return []
    return dns_servers

def get_dns_servers_from_ansible(inventory_path='/app/ansible_hosts.ini'):
    dns_servers = read_hosts_from_inventory(inventory_path)
    dnstester_logger.debug(f"DNS servers from Ansible inventory: {dns_servers}")
    dns_info_list = []
    for dns_server in dns_servers:
        dns_address = dns_server.get('dns_address')
        domain_name = dns_server.get('domain_name')
        description = dns_server.get('details')
        supported_services = dns_server.get('services', '').split(',')

        for service in supported_services:
            if service.strip() == 'do53':
                dns_info = { "target": f"udp://{dns_address}", "description": description }
                dns_info_list.append(dns_info)
                dns_info = { "target": f"tcp://{dns_address}", "description": description }
                dns_info_list.append(dns_info)
            elif service.strip() == 'doh':
                if domain_name:
                    dns_info = { "target": f"https://{domain_name}", "description": description }
                else:
                    dns_info = { "target": f"https://{dns_address}", "description": description }
                dns_info_list.append(dns_info)
            elif service.strip() == 'dot':
                if domain_name:
                    dns_info = { "target": f"tls://{domain_name}", "description": description }
                else:
                    dns_info = { "target": f"tls://{dns_address}", "description": description }
                dns_info_list.append(dns_info)

    return dns_info_list