import sys


class ProgressView:
    TOOLBAR_WIDTH = 50

    def __init__(self):
        pass

    def reset(self):
        sys.stdout.write("[%s]" % (" " * self.TOOLBAR_WIDTH))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.TOOLBAR_WIDTH+1))

    def finish(self):
        sys.stdout.write("]\n")

    def __call__(self, fact, total):
        if total > 0:
            sys.stdout.write("-" * int(fact * self.TOOLBAR_WIDTH/total))
        else:
            sys.stdout.write("-")
        sys.stdout.flush()
