import datetime
import ipaddress

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from scripts import generate_tls_cert


def test_generate_writes_cert_and_key(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_tls_cert, "CERT_DIR", tmp_path)
    monkeypatch.setattr(generate_tls_cert, "_detect_lan_ip", lambda: None)

    generate_tls_cert.generate([])

    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    assert cert_path.exists()
    assert key_path.exists()

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    assert isinstance(key, rsa.RSAPrivateKey)

    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert "localhost" in san.get_values_for_type(x509.DNSName)
    assert ipaddress.ip_address("127.0.0.1") in san.get_values_for_type(x509.IPAddress)

    now = datetime.datetime.now(datetime.timezone.utc)
    assert cert.not_valid_after_utc > now
    assert cert.not_valid_before_utc < now


def test_generate_includes_detected_lan_ip_and_extra_hosts(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_tls_cert, "CERT_DIR", tmp_path)
    monkeypatch.setattr(generate_tls_cert, "_detect_lan_ip", lambda: "192.168.1.50")

    generate_tls_cert.generate(["my-clr-box"])

    cert = x509.load_pem_x509_certificate((tmp_path / "cert.pem").read_bytes())
    san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert ipaddress.ip_address("192.168.1.50") in san.get_values_for_type(x509.IPAddress)
    assert "my-clr-box" in san.get_values_for_type(x509.DNSName)
