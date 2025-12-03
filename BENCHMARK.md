# Benchmark and test notes

## What was tested
- Syntax-only validation via `python -m compileall math_wave_sample.py` to ensure the refactored sampling logic compiles. Runtime validation was not executed because the execution environment is missing `numpy` and cannot reach package mirrors through the configured proxy.

## Expected performance impact
- The radial sampler now performs a single 30k-point sweep that simultaneously finds shell peaks and builds the PDF/CDF, replacing the former 15k+30k dual-pass scheme. That removes roughly one third of the expensive `radial_wavefunction` evaluations during `_prepare_radial`, so initialization of `HydrogenSampler` is expected to run about **1.5× faster** for the radial stage at the same precision.

## How to measure locally
1. Ensure `numpy` and the repository dependencies are installed.
2. Run a quick timing loop for the radial preparation step:
   ```bash
   python - <<'PY'
   import time
   from math_wave_sample import HydrogenSampler

   def bench(n, l, repeat=5):
       times = []
       for _ in range(repeat):
           obj = HydrogenSampler.__new__(HydrogenSampler)
           obj.n, obj.l, obj.m, obj.N = n, l, 0, 80000
           obj.rmax_theory = 8.0 * n * n
           t0 = time.perf_counter()
           HydrogenSampler._prepare_radial(obj)
           times.append(time.perf_counter() - t0)
       return sum(times) / len(times)

   for n, l in [(2, 1), (3, 2), (5, 3)]:
       print(f"n={n}, l={l}: {bench(n, l):.4f} s per _prepare_radial")
   PY
   ```
3. Compare the timings with a checkout of commit `bc78843` and its parent to quantify the delta.

## Environment limitations encountered
- `pip install numpy` and `apt-get install python3-numpy` both failed with `403 Forbidden` through the proxy, preventing runtime benchmarks in this container.
