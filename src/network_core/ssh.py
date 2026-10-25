"""Read-only vendor SSH facts for Cisco IOS, Junos and Huawei VRP.

Never accepts arbitrary commands from the user. Host keys must already be trusted.
"""
from __future__ import annotations

import asyncio
import ipaddress
import re
from functools import partial

import paramiko

COMMANDS = {
    "cisco": "show version",
    "juniper": "show version",
    "huawei": "display version",
}


def parse_output(vendor: str, output: str) -> dict:
    result: dict = {"vendor": vendor, "manufacturer": vendor.title()}
    text = output[:32768]
    if vendor == "cisco":
        patterns = {
            "firmware_version": r"Cisco IOS(?: XE)? Software[^\n]*Version\s+([^,\s]+)",
            "model": r"(?im)^cisco\s+(\S+)\s+\([^\n]+\)\s+processor",
            "serial_number": r"(?im)^Processor board ID\s+(\S+)",
        }
    elif vendor == "juniper":
        patterns = {
            "firmware_version": r"(?im)^Junos:\s*([^\s]+)",
            "model": r"(?im)^Model:\s*(\S+)",
            "serial_number": r"(?im)^Serial number:\s*(\S+)",
        }
    else:
        patterns = {
            "firmware_version": r"(?im)^VRP \(R\) software, Version\s+([^\n]+)",
            "model": r"(?im)^(?:HUAWEI\s+)?([A-Z]{2,}[A-Z0-9-]+)\s+uptime",
            "serial_number": r"(?im)^\s*(?:ESN|Serial Number|SN)\s*[:=]\s*(\S+)",
        }
    for field, regex in patterns.items():
        found = re.search(regex, text)
        if found:
            result[field] = found.group(1).strip()[:255]
    return result


def _collect(
    host: str,
    username: str,
    password: str,
    port: int,
    vendor: str,
    known_hosts: str | None = None,
) -> dict:
    ipaddress.IPv4Address(host)
    if vendor not in COMMANDS:
        raise ValueError("Unsupported SSH vendor")
    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port")
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if known_hosts:
        client.load_host_keys(known_hosts)
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(
            host,
            port=port,
            username=username,
            password=password,
            timeout=6,
            auth_timeout=6,
            banner_timeout=6,
            allow_agent=False,
            look_for_keys=False,
        )
        _, stdout, stderr = client.exec_command(COMMANDS[vendor], timeout=10)
        output = stdout.read(32768).decode("utf-8", "replace")
        if stdout.channel.recv_exit_status() != 0 or not output.strip():
            raise RuntimeError("SSH inventory command failed")
        return parse_output(vendor, output)
    finally:
        client.close()


async def device_info(
    host: str,
    username: str,
    password: str,
    vendor: str,
    port: int = 22,
    *,
    known_hosts: str | None = None,
) -> dict:
    if not username:
        raise ValueError("SSH username required")
    return await asyncio.wait_for(
        asyncio.to_thread(
            partial(_collect, host, username, password, port, vendor, known_hosts)
        ),
        timeout=25,
    )
