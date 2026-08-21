"""Device resolution for YOLO — auto selects CUDA / MPS / CPU."""

import torch


def resolve_device(device: str | None) -> str:
    """
    Resolve device string for ultralytics YOLO.
    - auto -> cuda:0 if available, else mps if available, else cpu
    - explicit values pass through (cpu, mps, cuda, 0, cuda:0 ...)
    """
    if device is None or str(device).strip().lower() == "auto":
        if torch.cuda.is_available():
            return "0"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    d = str(device).strip().lower()
    # normalize common aliases
    if d in {"cuda", "gpu"}:
        return "0"
    if d in {"mps", "cpu", "0", "cuda:0"}:
        return d
    # allow numeric like "1"
    if d.isdigit():
        return d
    # fallback as-is (let ultralytics validate)
    return str(device).strip()


def get_device_info() -> dict:
    return {
        "cuda_available": torch.cuda.is_available(),
        "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
        "mps_built": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_built()) if hasattr(torch.backends, "mps") else False,
    }
