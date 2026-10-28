"""CLI for shared S1 saved-output evaluation and local progress reporting."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from s1_eval.runner import main
if __name__ == '__main__':
    main()
