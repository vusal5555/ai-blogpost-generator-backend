from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("PUBLIC_SUPABASE_URL"),
    os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY"),
)
