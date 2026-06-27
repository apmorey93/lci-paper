"""Discrete-event simulation of a GI/G/k serving station with server-side
dynamic (micro-)batching, plus an analytic Erlang-C reference for validation.

This module replaces the earlier placeholder "toy convex map". It produces
*measured* latency distributions (p50/p95) and throughput for a configurable
load, from an actual event-driven simulation with fixed seeds. The M/M/k
special case (batch_size=1, exponential inter-arrivals and service) is
validated against the closed-form Erlang-C mean waiting time in
``validate_queue.py``.

Model
-----
- ``k`` parallel servers (e.g. GPU replicas), single FIFO admission queue.
- Inter-arrival times: Gamma with squared coefficient of variation
  ``scv_arrival`` (=1 -> exponential, i.e. Poisson arrivals; the GI input).
- Server-side dynamic batching ("max batch size B, max delay tau_b"), the
  policy used by production inference servers (e.g. NVIDIA Triton, vLLM):
  a free server serves the head of the queue as soon as either ``B`` requests
  are queued, or ``tau_b`` has elapsed since the head request arrived.
- Batch service time: Gamma with mean ``service_time_ms`` and squared
  coefficient of variation ``scv_service`` (=1 -> exponential; the G input).
  A batch of up to B requests is processed together and all members complete
  at the same instant (processor-sharing within the batch).

Capacity / utilisation
----------------------
Maximum sustainable throughput is ``k * B / E[S]`` (each of k servers clears up
to B requests per service time E[S]). For a target nominal utilisation ``u`` we
set the arrival rate ``lambda = u * k * B / E[S]``. For ``B = 1`` this reduces to
the textbook ``u = lambda / (k * mu)``, so the M/M/k validation is exact.
"""

from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass
class QueueConfig:
    k: int = 1                       # number of servers
    scv_arrival: float = 1.0         # squared CoV of inter-arrivals (GI); 1 = Poisson
    scv_service: float = 1.0         # squared CoV of batch service time (G); 1 = exponential
    batch_size: int = 1              # max batch size B
    batch_timeout_ms: float = 0.0    # max batching delay tau_b (ms)
    service_time_ms: float = 1000.0  # mean batch service time E[S] (ms)


# --------------------------------------------------------------------------- #
# Random variate helpers (Gamma parameterised by mean and squared CoV)
# --------------------------------------------------------------------------- #
def _gamma_sampler(mean: float, scv: float, rng: np.random.Generator):
    """Return a callable drawing Gamma variates with given mean and squared CoV.

    scv == 1 -> exponential; scv -> 0 -> (near-)deterministic.
    """
    if scv <= 1e-9:
        return lambda: mean
    shape = 1.0 / scv
    scale = mean * scv
    return lambda: float(rng.gamma(shape, scale))


# --------------------------------------------------------------------------- #
# Discrete-event simulation
# --------------------------------------------------------------------------- #
def simulate(u: float, cfg: QueueConfig, n_arrivals: int = 200_000,
             warmup: int = 20_000, seed: int = 0) -> dict:
    """Simulate the station at nominal utilisation ``u`` and return statistics.

    Returns a dict with p50/p95/p99/mean of latency and waiting time (ms),
    measured throughput (req/s) and measured server utilisation.
    """
    u = float(min(max(u, 1e-6), 0.999))
    rng = np.random.default_rng(seed)

    ES = cfg.service_time_ms
    cap = cfg.k * cfg.batch_size / ES          # max throughput (req/ms)
    lam = u * cap                              # arrival rate (req/ms)
    mean_iat = 1.0 / lam

    draw_iat = _gamma_sampler(mean_iat, cfg.scv_arrival, rng)
    draw_svc = _gamma_sampler(ES, cfg.scv_service, rng)

    events: list = []                          # (time, seq, kind, payload)
    seq = 0

    def push(t, kind, payload=None):
        nonlocal seq
        heapq.heappush(events, (t, seq, kind, payload))
        seq += 1

    # Schedule all arrivals up front (open system).
    t = 0.0
    for i in range(n_arrivals):
        t += draw_iat()
        push(t, "arr", i)

    queue: deque = deque()        # arrival timestamps of waiting requests
    free = cfg.k                  # free servers
    busy_time = 0.0               # cumulative server-busy time (for utilisation)
    waits: list = []              # queue waiting time per request (post-warmup)
    lats: list = []               # end-to-end latency per request (post-warmup)
    completed = 0
    first_start = None
    last_event = 0.0

    def try_dispatch(now):
        nonlocal free
        while free > 0 and queue:
            head = queue[0]
            if len(queue) >= cfg.batch_size or (now - head) >= cfg.batch_timeout_ms:
                b = min(cfg.batch_size, len(queue))
                batch = [queue.popleft() for _ in range(b)]
                free -= 1
                svc = draw_svc()
                push(now + svc, "dep", (batch, now, svc))
            else:
                # Head not ready: wake up when its batching window closes.
                push(head + cfg.batch_timeout_ms, "timeout", None)
                break

    while events:
        now, _, kind, payload = heapq.heappop(events)
        last_event = now
        if kind == "arr":
            queue.append(now)
            try_dispatch(now)
        elif kind == "timeout":
            try_dispatch(now)
        elif kind == "dep":
            batch, start, svc = payload
            if first_start is None:
                first_start = start
            free += 1
            busy_time += svc
            for arr_t in batch:
                idx = completed
                completed += 1
                if idx >= warmup:
                    waits.append(start - arr_t)
                    lats.append(now - arr_t)
            try_dispatch(now)

    waits_a = np.asarray(waits, dtype=float)
    lats_a = np.asarray(lats, dtype=float)
    elapsed = max(last_event - (first_start or 0.0), 1e-9)
    measured_thru = completed / elapsed                     # req/ms

    return {
        "u_nominal": u,
        "lambda_req_per_ms": lam,
        "n_measured": int(lats_a.size),
        "wait_mean_ms": float(waits_a.mean()) if waits_a.size else 0.0,
        "lat_mean_ms": float(lats_a.mean()) if lats_a.size else 0.0,
        "lat_p50_ms": float(np.percentile(lats_a, 50)) if lats_a.size else 0.0,
        "lat_p95_ms": float(np.percentile(lats_a, 95)) if lats_a.size else 0.0,
        "lat_p99_ms": float(np.percentile(lats_a, 99)) if lats_a.size else 0.0,
        "throughput_req_per_s": measured_thru * 1000.0,
        "util_measured": float(busy_time / (cfg.k * elapsed)),
    }


def sweep(us, cfg: QueueConfig, n_arrivals: int = 200_000, warmup: int = 20_000,
          replications: int = 8, base_seed: int = 0) -> "list[dict]":
    """Run ``simulate`` over a utilisation grid with multiple replications.

    Returns one record per ``u`` with mean and standard deviation (across
    replication seeds) for p50/p95 latency and throughput.
    """
    out = []
    for u in us:
        p50s, p95s, p99s, thru, util = [], [], [], [], []
        for r in range(replications):
            res = simulate(u, cfg, n_arrivals=n_arrivals, warmup=warmup,
                           seed=base_seed + 1000 * r + int(u * 1000))
            p50s.append(res["lat_p50_ms"]); p95s.append(res["lat_p95_ms"])
            p99s.append(res["lat_p99_ms"]); thru.append(res["throughput_req_per_s"])
            util.append(res["util_measured"])
        n = len(p95s)
        out.append({
            "u": float(u),
            "p50_ms": float(np.mean(p50s)),
            "p95_ms": float(np.mean(p95s)),
            "p95_sd": float(np.std(p95s, ddof=1)) if n > 1 else 0.0,
            "p99_ms": float(np.mean(p99s)),
            "throughput_req_per_s": float(np.mean(thru)),
            "util_measured": float(np.mean(util)),
            "replications": replications,
        })
    return out


# --------------------------------------------------------------------------- #
# Analytic reference: Erlang-C mean waiting time for M/M/k
# --------------------------------------------------------------------------- #
def erlang_c(k: int, a: float) -> float:
    """Erlang-C probability of waiting for an M/M/k queue with offered load a."""
    if a >= k:
        return 1.0
    s = sum(a ** n / math.factorial(n) for n in range(k))
    last = a ** k / math.factorial(k) * (k / (k - a))
    return last / (s + last)


def mmk_wait_mean(k: int, u: float, service_time_ms: float = 1000.0) -> float:
    """Closed-form mean waiting time (ms) for M/M/k: Wq = C(k,a) / (k*mu - lambda)."""
    a = k * u                       # offered load in Erlangs
    mu = 1.0 / service_time_ms      # service rate per server (per ms)
    lam = a * mu
    if a >= k:
        return float("inf")
    return erlang_c(k, a) / (k * mu - lam)


if __name__ == "__main__":
    cfg = QueueConfig(k=4, service_time_ms=1000.0)
    for u in (0.5, 0.8, 0.95):
        r = simulate(u, cfg, n_arrivals=120_000, warmup=20_000, seed=1)
        print(f"u={u:.2f}  p50={r['lat_p50_ms']:.0f}ms  p95={r['lat_p95_ms']:.0f}ms  "
              f"thru={r['throughput_req_per_s']:.3f}/s  util={r['util_measured']:.3f}")
