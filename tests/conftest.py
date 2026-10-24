import socket
import pytest

def has_internet_access() -> bool:
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=0.8)
        sock.close()
        return True
    except OSError:
        return False

HAS_INTERNET = has_internet_access()

@pytest.fixture(scope="session")
def internet_available():
    return HAS_INTERNET
