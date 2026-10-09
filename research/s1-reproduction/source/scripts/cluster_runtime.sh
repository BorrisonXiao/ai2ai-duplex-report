#!/usr/bin/env bash
# CUDA 12.8 matches the copied Torch runtimes. Runtime libraries remain in the
# pinned environments; this supplies the compiler/headers for fresh JIT caches.
export CUDA_HOME=/apps/software/extern/cuda/12.8.1
if [[ ! -x "$CUDA_HOME/bin/nvcc" ]]; then
  echo "Expected cluster CUDA toolkit is missing: $CUDA_HOME" >&2
  return 1
fi
export PATH="$CUDA_HOME/bin:$PATH"
export CUDA_DEVICE_ORDER=PCI_BUS_ID
