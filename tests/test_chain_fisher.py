"""Unit tests for the chain Fisher IPD helper."""

from __future__ import annotations

import unittest

import pandas as pd

from src.make_ipd import chain_fisher


class ChainFisherTest(unittest.TestCase):
    """Validate the numerical behaviour of the chain Fisher helper."""

    def test_normalizes_base(self) -> None:
        """The resulting series should start at 1 regardless of raw scaling."""

        data = pd.DataFrame(
            {
                "date": ["2025-01-01", "2025-01-01", "2025-06-01", "2025-06-01"],
                "family": ["qa", "code", "qa", "code"],
                "LCI": [2.0, 4.0, 1.0, 2.0],
            }
        )
        result = chain_fisher(data)

        self.assertEqual(list(result["date"].astype(str)), ["2025-01-01", "2025-06-01"])
        self.assertEqual(result["IPD"].iloc[0], 1.0)
        self.assertAlmostEqual(result["IPD"].iloc[1], 0.5)

    def test_carries_forward_without_overlap(self) -> None:
        """When no overlapping families exist, the index should stay flat."""

        data = pd.DataFrame(
            {
                "date": ["2025-01-01", "2025-06-01"],
                "family": ["qa", "code"],
                "LCI": [3.0, 6.0],
            }
        )
        result = chain_fisher(data)

        self.assertEqual(result["IPD"].tolist(), [1.0, 1.0])


if __name__ == "__main__":  # pragma: no cover - manual invocation
    unittest.main()
