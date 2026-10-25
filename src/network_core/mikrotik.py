"""RouterOS API helpers using librouteros; never execute arbitrary CLI commands."""
from __future__ import annotations

import asyncio
import ipaddress
import ssl

from librouteros import connect
from librouteros.login import plain


def _run(
    host: str,
    username: str,
    password: str,
    port: int,
    use_ssl: bool,
    resource: str,
) -> list[dict]:
    ssl_wrapper = None
    if use_ssl:
        context = ssl.create_default_context()
        ssl_wrapper = lambda sock: context.wrap_socket(sock, server_hostname=host)
    api = connect(
        host=host,
        username=username,
        password=password,
        port=port,
        ssl_wrapper=ssl_wrapper,
        login_method=plain,
    )
    try:
        path = tuple(part for part in resource.strip("/").split("/") if part)
        if not path or any(not part.replace("-", "").replace("_", "").isalnum() for part in path):
            raise ValueError("Недопустимый RouterOS API resource")
        return [dict(item) for item in api.path(*path)]
    finally:
        api.close()


async def read_resource(
    host: str,
    username: str,
    password: str,
    port: int = 8728,
    use_ssl: bool = False,
    resource: str = "/system/resource",
) -> list[dict]:
    if not host or not username:
        raise ValueError("Укажите адрес и имя пользователя MikroTik")
    return await asyncio.to_thread(_run, host, username, password, port, use_ssl, resource)


async def discover_subnets(
    networks: list[str],
    *,
    port: int = 8728,
    username: str | None = None,
    password: str = "",
    use_ssl: bool = False,
    concurrency: int = 64,
    timeout_seconds: float = 0.8,
    max_hosts: int = 4096,
) -> dict:
    """Find RouterOS API candidates in explicitly configured private IPv4 networks."""
    if not 1 <= port <= 65535:
        raise ValueError("Недопустимый TCP-порт")
    if not 1 <= concurrency <= 128:
        raise ValueError("Параллелизм должен быть от 1 до 128")
    if not 0.1 <= timeout_seconds <= 10:
        raise ValueError("Таймаут должен быть от 0.1 до 10 секунд")
    if not 1 <= max_hosts <= 4096:
        raise ValueError("Лимит адресов должен быть от 1 до 4096")
    if not networks or len(networks) > 100:
        raise ValueError("Укажите от 1 до 100 подсетей")

    parsed = []
    for cidr in networks:
        try:
            net = ipaddress.ip_network(cidr.strip(), strict=False)
        except ValueError as exc:
            raise ValueError(f"Некорректная подсеть: {cidr}") from exc
        if not isinstance(net, ipaddress.IPv4Network) or not net.is_private:
            raise ValueError(f"Разрешены только частные IPv4-подсети: {cidr}")
        parsed.append(net)

    addresses: set[str] = set()
    for net in ipaddress.collapse_addresses(parsed):
        if net.num_addresses + len(addresses) > max_hosts + 2:
            raise ValueError(f"Слишком большой диапазон: максимум {max_hosts} IP за один поиск")
        addresses.update(str(address) for address in net.hosts())
        if len(addresses) > max_hosts:
            raise ValueError(f"Слишком большой диапазон: максимум {max_hosts} IP за один поиск")

    sem = asyncio.Semaphore(concurrency)

    async def probe(host: str) -> dict | None:
        async with sem:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=timeout_seconds
                )
                writer.close()
                await writer.wait_closed()
            except (OSError, asyncio.TimeoutError):
                return None

            result = {"host": host, "port": port, "status": "port_open", "confirmed": False}
            if username:
                try:
                    rows = await asyncio.wait_for(
                        read_resource(host, username, password, port, use_ssl, "/system/identity"),
                        timeout=max(3.0, timeout_seconds * 3),
                    )
                    result["identity"] = str(rows[0].get("name", "")) if rows else ""
                    result["status"] = "mikrotik"
                    result["confirmed"] = True
                except Exception:
                    result["status"] = "api_auth_failed"
            return result

    results = await asyncio.gather(
        *(probe(host) for host in sorted(addresses, key=lambda x: ipaddress.IPv4Address(x)))
    )
    found = [item for item in results if item is not None]
    return {
        "networks": [str(n) for n in parsed],
        "scanned": len(addresses),
        "candidates": len(found),
        "confirmed": sum(1 for item in found if item["confirmed"]),
        "items": found,
    }
