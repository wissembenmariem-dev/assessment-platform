import secrets


def generate_token() -> str:
    return secrets.token_hex(16)


def generate_candidate_link(base_url: str, token: str) -> str:
    return f"{base_url}/test/{token}"
