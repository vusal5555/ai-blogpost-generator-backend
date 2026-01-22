from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()  # Works locally, ignored in production (that's fine)

supabase_url = os.getenv("PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

# Fail loudly if not configured
if not supabase_url or not supabase_key:
    raise ValueError(
        f"Missing Supabase config. "
        f"URL set: {supabase_url is not None}, "
        f"KEY set: {supabase_key is not None}"
    )

supabase = create_client(supabase_url, supabase_key)
