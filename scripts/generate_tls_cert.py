"""Generate a self-signed TLS certificate for local/LAN HTTPS.

Usage:
    python scripts/generate_tls_cert.py [extra-hostname-or-ip ...]

Writes certs/cert.pem and certs/key.pem (825-day validity), covering
localhost, 127.0.0.1, and this machine's detected LAN IP by default.
Pass additional hostnames/IPs as arguments if you reach the server another
way (a second LAN interface, a hostname from your router's DNS, etc).

Since this cert is self-signed, browsers will show a security warning on
first connection until you tell them to trust it — either click through the
warning once per device, or import certs/cert.pem into that device's/
browser's trusted certificate store to remove the warning permanently.
"""

import datetime
import ipaddress
import pathlib
import socket
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CERT_DIR = pathlib.Path(__file__).resolve().parent.parent / "certs"
VALID_DAYS = 825


def _detect_lan_ip() -> str | None:
    # Doesn't actually send traffic — UDP connect() just asks the OS to pick
    # the outbound interface/route, which reveals this machine's LAN IP.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def _san_entries(extra_hosts: list[str]) -> list[x509.GeneralName]:
    values = ["127.0.0.1"] + extra_hosts
    lan_ip = _detect_lan_ip()
    if lan_ip:
        values.append(lan_ip)

    entries: list[x509.GeneralName] = [x509.DNSName("localhost")]
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        try:
            entries.append(x509.IPAddress(ipaddress.ip_address(value)))
        except ValueError:
            entries.append(x509.DNSName(value))
    return entries


def generate(extra_hosts: list[str]) -> None:
    CERT_DIR.mkdir(exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Cognitive Load Reducer (self-signed)")])
    now = datetime.datetime.now(datetime.timezone.utc)
    sans = _san_entries(extra_hosts)

    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=VALID_DAYS))
        .add_extension(x509.SubjectAlternativeName(sans), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(key, hashes.SHA256())
    )

    key_path = CERT_DIR / "key.pem"
    cert_path = CERT_DIR / "cert.pem"
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Wrote {cert_path} and {key_path}")
    print(f"Valid for {VALID_DAYS} days, covers: " + ", ".join(str(e.value) for e in sans))
    print(
        "This cert is self-signed — browsers will warn on first connection "
        "until you trust it (click through once, or import certs/cert.pem "
        "into the device's trusted certificate store)."
    )


if __name__ == "__main__":
    generate(sys.argv[1:])
