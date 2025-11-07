from dotenv import load_dotenv
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

load_dotenv(PROJECT_ROOT / ".env")

DMX_API_KEY = os.getenv('DMX_API_KEY')
DMX_BASE_URL = "https://www.dmxapi.cn/v1"

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

ANALYSIS_CACHE_DIR = PROJECT_ROOT / "analysis_cache"
CACHE_DIR = PROJECT_ROOT / "luogu_cache"