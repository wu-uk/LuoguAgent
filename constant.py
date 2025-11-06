from dotenv import load_dotenv
import os

load_dotenv()

DMX_API_KEY = os.getenv('DMX_API_KEY')
DMX_BASE_URL = "https://www.dmxapi.cn/v1"

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

ANALYSIS_CACHE_DIR = "./analysis_cache"
CACHE_DIR = "./luogu_cache"