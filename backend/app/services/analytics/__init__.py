"""Phase 4 analytics: data quality, liquidity forecasting, and anomaly detection.

The package is organized into pure, independently testable engines
(``app.services.quality.engine``, ``app.services.liquidity.engine``,
``app.services.anomaly.engine``) and orchestration/persistence helpers in this
package that read the Phase 3 ledger, run the engines, and persist explainable,
reproducible analytical artifacts.
"""

from __future__ import annotations
