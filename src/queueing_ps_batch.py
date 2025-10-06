from dataclasses import dataclass

@dataclass
class QueueConfig:
    k: int                 # number of servers
    scv_arrival: float     # squared coeff. of variation of interarrivals (GI)
    scv_service: float     # squared coeff. of variation of service times (G)
    batch_size: int        # max batch size B
    batch_timeout_ms: float # batching timeout tau_b (ms)
    service_rate_tps: float # service rate per server (tokens/sec or jobs/sec)

def approx_p95_latency(utilization: float, cfg: QueueConfig) -> float:
    """
    Approximate p95 latency (ms) under GI/G/k-PS with batching.
    NOTE: Placeholder convex map; replace with validated approximation if desired.
    """
    u = max(1e-6, min(0.999, utilization))
    # Base PS-like convexity
    base = 100.0 * (1.0 / (1.0 - u))**1.2
    # Batching factor (larger batch/timeout => larger tail)
    batch_factor = 1.0 + 0.02 * (cfg.batch_size - 1) + 0.001 * cfg.batch_timeout_ms
    scv_factor = (1 + cfg.scv_arrival) * (1 + 0.5 * cfg.scv_service)
    return float(base * batch_factor * scv_factor)

def lci_convexity_curve(us, cfg: QueueConfig, lci_base: float = 1.0):
    """Return (u, p95_ms, LCI_u) for a utilization grid (toy mapping)."""
    out = []
    for u in us:
        p95 = approx_p95_latency(u, cfg)
        # Simple monotone penalty mapping
        lci_u = lci_base * (1.0 + 0.001 * max(0.0, p95 - 300.0))
        out.append((u, p95, lci_u))
    return out
