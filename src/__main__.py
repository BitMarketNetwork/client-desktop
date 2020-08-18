import sys
import os

abs_path = os.path.join(os.getcwd(), "dep")
sys.path.append(abs_path)

if __package__:
    from . import client
else:
    import client


if __name__ == "__main__":
    sys.exit(client.run_protected())
