"""Normalize equipment manufacturer names without mistaking access protocols for brands."""
from __future__ import annotations

import re

PROTOCOL_NAMES = {
    "onvif", "rtsp", "http", "https", "isapi", "cgi", "snmp", "ssh",
    "auto", "unknown", "none", "generic", "ws-discovery", "",
}
ALIASES = {
    "hikvision": ("hikvision", "hiwatch", "хиквижн"),
    "dahua": ("dahua", "imou"),
    "axis": ("axis communications", "axis"),
    "uniview": ("uniview", "unv"),
    "hanwha": ("hanwha", "wisenet", "samsung techwin"),
    "tiandy": ("tiandy",),
    "bosch": ("bosch",),
    "mikrotik": ("mikrotik", "routeros"),
    "ubiquiti": ("ubiquiti", "unifi", "airos"),
    "cisco": ("cisco",),
    "huawei": ("huawei",),
    "juniper": ("juniper", "junos"),
    "zte": ("zte",),
    "eltex": ("eltex",),
    "d-link": ("d-link", "dlink"),
    "tp-link": ("tp-link", "tplink"),
    "cambium": ("cambium",),
    "bdcom": ("bdcom",),
}


def normalize_vendor(value: object) -> str | None:
    """Return a canonical vendor, or a non-protocol explicit manufacturer label."""
    if value is None:
        return None
    raw = str(value).strip()
    text = raw.lower()
    if not raw or text in PROTOCOL_NAMES:
        return None
    for canonical, names in ALIASES.items():
        if any(text == n or text.startswith(n + " ") for n in names):
            return canonical
    return raw[:80]


def infer_vendor(*values: object) -> str | None:
    """Conservatively find a known vendor in free-form names/model descriptions."""
    for value in values:
        if value is None:
            continue
        text = str(value).lower()
        for canonical, names in ALIASES.items():
            for name in names:
                if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", text):
                    return canonical
    return None


def manufacturer_for_display(detected: object, manual: object) -> str | None:
    """Prefer device-reported manufacturer to a manual value, excluding protocols."""
    return normalize_vendor(detected) or normalize_vendor(manual)
