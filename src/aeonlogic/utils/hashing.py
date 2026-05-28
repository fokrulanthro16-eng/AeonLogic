import hashlib


def sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()
