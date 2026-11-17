from supabase import create_client, Client
from app.core.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL non configurée. Vérifiez votre fichier .env")
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL non configurée. Vérifiez votre fichier .env")
    return create_client(settings.supabase_url, settings.supabase_service_key)


@property
def supabase_admin():
    return get_supabase_admin()

