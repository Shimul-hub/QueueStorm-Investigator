#!/usr/bin/env python3
"""Run all public sample cases against a live QueueStorm API."""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

SAMPLES_PATH = Path(__file__).resolve().parent.parent / "SUST_Preli_Sample_Cases.json"
HARD_FIELDS = [
    "relevant_transaction_id",
    "evidence_verdict",
    "case_type",
    "department",
    "human_review_required",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run QueueStorm sample cases")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    with open(SAMPLES_PATH, encoding="utf-8") as f:
        cases = json.load(f)["cases"]

    passed = 0
    timings: list[float] = []

    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        health = client.get("/health")
        if health.status_code != 200:
            print(f"Health check failed: {health.status_code}")
            return 1

        for case in cases:
            start = time.perf_counter()
            resp = client.post("/analyze-ticket", json=case["input"])
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            if resp.status_code != 200:
                print(f"FAIL {case['id']}: HTTP {resp.status_code}")
                continue

            body = resp.json()
            expected = case["expected_output"]
            ok = True
            for field in HARD_FIELDS:
                if body.get(field) != expected.get(field):
                    print(
                        f"FAIL {case['id']} {field}: "
                        f"got {body.get(field)!r} expected {expected.get(field)!r}"
                    )
                    ok = False
            if ok:
                passed += 1
                print(f"PASS {case['id']} ({elapsed:.2f}s)")
            else:
                print(f"  Response: {json.dumps(body, indent=2)[:500]}")

    if timings:
        sorted_t = sorted(timings)
        p95 = sorted_t[int(len(sorted_t) * 0.95)]
        print(f"\nResults: {passed}/{len(cases)} passed")
        print(f"Latency p95: {p95:.2f}s")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
