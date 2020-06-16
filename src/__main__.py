import sys
import os

if __package__:
    from . import client
else:
    import client


if __name__ == "__main__":
    sys.exit(client.run_protected())
