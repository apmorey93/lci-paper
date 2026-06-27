#!/usr/bin/env python3
"""DEPRECATED CI stub.

The real LCI computation now lives in ``src/lci_program.py`` (cost frontier from
the validated queueing simulator + sourced public prices/benchmarks). This file
previously emitted a placeholder ``acc/(1+lat)`` formula that is NOT the LCI used
in the paper; it is retained only so legacy CI invocations fail loudly rather
than silently producing a misleading number.
"""

import sys

if __name__ == "__main__":
    sys.stderr.write(
        "aggregate_lci.py is deprecated. Run the real pipeline instead:\n"
        "  make results   (or: cd src && python lci_program.py && python make_ipd.py)\n"
    )
    sys.exit(1)
