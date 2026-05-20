#!/usr/bin/env bash
# Perbaiki / pasang PyTorch CPU yang aman untuk Raspberry Pi 4 (aarch64).
# Menangani venv yang sudah terpasang torch+cu atau versi yang memicu "Illegal instruction".
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

find_venv() {
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        echo "$VIRTUAL_ENV"
        return 0
    fi
    local candidate
    for candidate in "$REPO_ROOT/usbcamtest" "$SCRIPT_DIR/usbcamtest"; do
        if [[ -f "$candidate/bin/activate" ]]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

if ! VENV_DIR="$(find_venv)"; then
    echo "venv tidak ditemukan."
    echo "Buat di root repo: cd $REPO_ROOT && python3 -m venv usbcamtest"
    exit 1
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

ARCH="$(uname -m)"
echo "=== fix_pytorch_raspi.sh ==="
echo "venv : $VENV_DIR"
echo "arch : $ARCH"
echo ""

if [[ "$ARCH" != "aarch64" ]]; then
    echo "Peringatan: mesin ini bukan aarch64 (Raspberry Pi)."
    echo "Skrip tetap bisa memasang torch CPU, tetapi biasanya hanya diperlukan di Pi."
    read -r -p "Lanjutkan? [y/N] " ans
    [[ "${ans,,}" == "y" ]] || exit 0
fi

torch_status() {
    python - <<'PY'
try:
    import torch
    version = torch.__version__
    broken = ("+cu" in version) or version.startswith(("2.11", "2.12"))
    print("broken" if broken else "ok", version)
except ModuleNotFoundError:
    print("missing", "")
except Exception as exc:
    print("error", exc)
PY
}

read -r STATUS TORCH_VER <<< "$(torch_status)"
echo "PyTorch saat ini: ${TORCH_VER:-<tidak ada>} ($STATUS)"
echo ""

if [[ "$STATUS" == "ok" ]]; then
    echo "PyTorch sudah terlihat aman untuk Pi. Tetap pasang ulang dependensi? [y/N]"
    read -r -p "> " ans
    [[ "${ans,,}" == "y" ]] || {
        echo "Lewati pemasangan. Tes YOLO..."
        python "$SCRIPT_DIR/check_yolo_torch.py" && exit 0
    }
fi

echo "Menghapus torch/torchvision dan paket NVIDIA CUDA dari venv (jika ada)..."
pip uninstall -y torch torchvision 2>/dev/null || true

mapfile -t NVIDIA_PKGS < <(pip list --format=freeze | sed -n 's/^\(nvidia-[^=]*\)==.*/\1/p')
if ((${#NVIDIA_PKGS[@]})); then
  pip uninstall -y "${NVIDIA_PKGS[@]}" 2>/dev/null || true
fi

echo ""
echo "Memasang dari requirements-raspberrypi.txt ..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements-raspberrypi.txt"

echo ""
read -r STATUS TORCH_VER <<< "$(torch_status)"
echo "PyTorch setelah pemasangan: $TORCH_VER ($STATUS)"

if [[ "$STATUS" == "broken" ]]; then
    echo "ERROR: PyTorch masih tidak sesuai. Coba manual:"
    echo "  pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu"
    exit 1
fi

echo ""
python "$SCRIPT_DIR/check_yolo_torch.py"
echo ""
echo "Selesai. Jalankan Level 7: python Level_7_Deteksi_Objek_YOLO.py"
