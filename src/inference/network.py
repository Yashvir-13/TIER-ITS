import socket

_is_patched = False

def patch_ipv4():
    """
    Patches socket.getaddrinfo to resolve IPv4 addresses by default.
    Prevents long TCP SYN timeouts and socket hangs on networks with broken IPv6 routing to Google endpoints.
    """
    global _is_patched
    if _is_patched:
        return
    orig_getaddrinfo = socket.getaddrinfo
    def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
        if family == 0 or family == socket.AF_UNSPEC:
            family = socket.AF_INET
        return orig_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = getaddrinfo_ipv4
    _is_patched = True

# Apply automatically on module import
patch_ipv4()
