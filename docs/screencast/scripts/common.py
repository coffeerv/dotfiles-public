"""Keep generated media separate from versioned production sources."""
import os
from pathlib import Path
S = Path(__file__).resolve().parent
R = Path(os.environ.get("SCREENCAST_WORKDIR", str(S.parent / "build"))).expanduser().resolve()
R.mkdir(parents=True, exist_ok=True)
