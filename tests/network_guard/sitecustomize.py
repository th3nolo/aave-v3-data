"""Inherited by Python worker processes during the offline test command."""
import ipaddress
import os
import sys


def is_loopback(host):
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        return False


def network_audit(event, args):
    if event == 'socket.getaddrinfo':
        host = args[0]
    elif event in ('socket.connect', 'socket.sendto'):
        address = args[1] if event == 'socket.connect' else args[2]
        if not isinstance(address, tuple):
            return  # Local IPC, not an IP endpoint.
        host = address[0]
    else:
        return
    if not is_loopback(host):
        # Record even when application code catches the exception. Never log URLs,
        # headers or credentials. Child processes append to the same test-only log.
        with open(os.environ['AAVE_NETWORK_VIOLATIONS'], 'a', encoding='utf-8') as log:
            log.write(event + '\n')
        raise RuntimeError('Offline test attempted external network access')


if os.environ.get('AAVE_NETWORK_VIOLATIONS'):
    sys.addaudithook(network_audit)
