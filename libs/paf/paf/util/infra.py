import os


def setup_uvloop():
    # fmt: off
    if os.name != "nt":
        import uvloop
        uvloop.install()
    # fmt: on
