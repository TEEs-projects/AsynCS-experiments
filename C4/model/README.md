# C4 / E5 Key-Related Protected-State Model

This directory is the reproducible local C4 source for the current E5 figure.
It supersedes the policy/total-state semantics in the 2026-06-13 and
2026-06-15 v1 previews without deleting those provenance artifacts.

## Contract

- `F={1,10,100,1000,10000}`.
- `P=ceil(0.25F)` and `R=1`; the default CoFunc object model reports `T=1`.
- Count only key-related protected state: authority secrets, warm key copies,
  and binding state required to select/use those keys.
- Exclude general policy, labels that are not retained for key selection,
  workload metadata, code, request payloads, sealing framing, and all timing.
- Keep `secret_payload_bytes`, `protected_state_payload_bytes`, and
  `retained_memory_bytes` separate.
- Missing baseline key managers remain `N/A`; they are never encoded as zero.

The byte-complete main comparison is deliberately limited to:

1. `AsynCS minimal core` (`source-derived`): one 32-byte persistent MSK;
   each warm placement has two 96-byte BF-IBE private capabilities plus one
   32-byte canonical FID binding.
2. `Per-function stored capabilities` (`paper-model`): the same two
   96-byte capabilities and FID granularity, but the authority persists both
   capabilities for every function. This is a controlled model, not Wallet,
   CoFunc, or Reusable measured state.

Wallet and CoFunc enter the object-count panel only. Reusable contributes a
source-backed session-state lower bound to the CSV/coverage table, but is not
plotted as a complete key-state total because its artifact lacks the relevant
function-key manager.

## Generate

From the repository root:

```bash
python3 experiments/state-scaling/c4-e5/build_c4_e5_state_scaling.py
python3 experiments/state-scaling/c4-e5/test_c4_e5_state_scaling.py
python3 experiments/state-scaling/c4-e5/validate_c4_e5_outputs.py --check-determinism
```

Outputs are written to `generated/` and committed:

- `c4_e5_state_scaling.csv`
- `c4_e5_constants.csv`
- `c4_e5_baseline_coverage.csv`
- `e5_key_related_protected_state.svg`
- `e5_key_related_protected_state.png`
- `manifest.csv`

## Source Probes

`source_evidence.csv` freezes exact refs, paths, locators, and file hashes where
the value came from a concrete source/artifact file. The two local probes used
to close sizes were:

```bash
# BLS12-381 serialization sizes from the same mcl build used by acsc:
# fr=32 g1=48 g2=96
mclBn_getFrByteSize / mclBn_getG1ByteSize / mclBn_getG2ByteSize

# Declared BF-IBE storage and local ELF symbol span:
nm -S --size-sort acsc/sgx_worker/enclave.so | \
  grep -E 'g_bfibe_(request_sk|function_sk|fid|key_loaded)'
```

The ELF probe reports 649 bytes of declared key/FID/length/valid storage and
56 bytes of linker padding per placement. Allocator/runtime overhead is zero
for those static arrays; the model does not extrapolate unrelated enclave or
runtime memory into E5.

The CoFunc tenant-count scenario uses the 14-day owner/function union from the
Azure Functions 2019 trace. Rebuild the complete summary, including the 14
per-day audit rows, with:

```bash
python3 experiments/state-scaling/c4-e5/trace-calibration/\
  summarize_azure_owner_function_ratio.py \
  /path/to/azurefunctions_dataset2019_azurefunctions-dataset2019.tar.xz \
  --output local-temp/azure_owner_function_ratio.json
cmp local-temp/azure_owner_function_ratio.json \
  experiments/state-scaling/c4-e5/trace-calibration/\
  azure_owner_function_ratio_v2.json
```

The input archive SHA-256 is
`aff8b3ca7240a41a109e4ee598e0a96e45fcb92e7b8395ac19cb3748cd260d89`.
The older `azure_owner_function_ratio.json` is retained because E5 figure
version `002` records its exact hash; new versions use the reproducible `v2`
file.
