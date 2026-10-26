import sys
from pathlib import Path

# Add services/ai and repository root to sys.path
ai_dir = Path(__file__).resolve().parent
repo_dir = ai_dir.parent.parent

if str(ai_dir) not in sys.path:
    sys.path.insert(0, str(ai_dir))
if str(repo_dir) not in sys.path:
    sys.path.insert(0, str(repo_dir))
