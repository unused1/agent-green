#!/bin/bash
# Agent-Green Replication Container — Build Script
# Target: native linux/amd64 (e.g., Mars A5000 server, RunPod CPU pod).
# Not intended for Mac builds via QEMU emulation.
set -euo pipefail

IMAGE_NAME="agent-green"
TAG="v1.0-replication"
USER_PREFIX="${USER:-huabengtan}"
BUILD_CONTAINER_NAME="${USER_PREFIX}_replication_build"
OUTPUT_TARBALL="${IMAGE_NAME}-${TAG}.tar.gz"

# Script expects to be run from the repository root, where container/Dockerfile lives
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"

# === Architecture sanity check ===
ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" ]]; then
  echo "[ERROR] This build script targets linux/amd64 natively." >&2
  echo "[ERROR] Current architecture: $ARCH" >&2
  echo "[ERROR] Please run on a native x86_64 Linux host (Mars A5000 / RunPod CPU pod)." >&2
  exit 1
fi

# === Preflight checks ===
echo "[Preflight] Docker version: $(docker --version)"
echo "[Preflight] Disk space at /var/lib/docker (or docker root):"
docker info 2>/dev/null | grep "Docker Root Dir" || true
df -h "$(docker info 2>/dev/null | awk '/Docker Root Dir/{print $NF}')" 2>/dev/null || df -h /

echo "[Preflight] Building context:"
echo "  - Dockerfile: container/Dockerfile"
echo "  - Source files: 10 files from src/"
echo "  - Datasets: VulTrial_870 + VulTrial_10 (smoke-test)"
echo "  - Entrypoint + README: container/entrypoint.sh + container/REPLICATION_README.md"

# === Build ===
echo ""
echo "[Build] docker build -t ${IMAGE_NAME}:${TAG} -f container/Dockerfile ."
docker build \
  -t "${IMAGE_NAME}:${TAG}" \
  -f container/Dockerfile \
  .

echo "[Build] Image built successfully: ${IMAGE_NAME}:${TAG}"
docker images "${IMAGE_NAME}:${TAG}"

# === Save + compress ===
echo ""
echo "[Save] Exporting image to tarball: ${OUTPUT_TARBALL}"
docker save "${IMAGE_NAME}:${TAG}" | gzip > "${OUTPUT_TARBALL}"
echo "[Save] Tarball size:"
ls -lh "${OUTPUT_TARBALL}"

# === Done ===
cat <<EOF

========================================
  BUILD COMPLETE
========================================
Image: ${IMAGE_NAME}:${TAG}
Tarball: $(pwd)/${OUTPUT_TARBALL}

Next steps:
  1. Run a local smoke test (see REPLICATION_README.md):
     docker run --rm --gpus all \\
       --user \$(id -u):\$(id -g) \\
       -v \$(pwd)/results:/workspace/results \\
       -e DESIGN=SA -e MODE=instruct -e MODEL=qwen3-4b \\
       -e PROMPTING=zero -e SEED=1 -e SMOKE_TEST=1 \\
       --name ${USER_PREFIX}_replication_smoke \\
       ${IMAGE_NAME}:${TAG}

     (--user flag ensures output files are owned by you, not root)

  2. scp tarball to your Mac:
     scp ${OUTPUT_TARBALL} user@mac:~/Downloads/

  3. Upload to Google Drive and share with team members.
========================================
EOF
