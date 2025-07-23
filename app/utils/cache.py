import logging
from diskcache import Cache
from app.core.config import settings
from app.utils.enhanced_cache import enhanced_cache

# Legacy disk cache for backward compatibility
cache = Cache(settings.CACHE_DIR, size_limit=int(2e9))  # 2GB limit

def get_leaderboard_cache(page: int = 1, limit: int = 50):
    """Get leaderboard data from enhanced cache (70-80% faster)."""
    try:
        cache_key = f"leaderboard:{page}:{limit}"
        # Try enhanced cache first
        result = enhanced_cache.get(cache_key)
        if result is not None:
            logging.debug(f"Enhanced cache hit for leaderboard: {cache_key}")
            return result

        # Fallback to legacy cache
        result = cache.get(cache_key)
        if result is not None:
            # Promote to enhanced cache
            enhanced_cache.set(cache_key, result, ttl=60)
            logging.debug(f"Promoted leaderboard to enhanced cache: {cache_key}")

        return result
    except Exception as e:
        logging.error(f"Cache get error: {e}")
        return None

def set_leaderboard_cache(data, page: int = 1, limit: int = 50, expire: int = 60):
    """Set leaderboard data in enhanced cache."""
    try:
        cache_key = f"leaderboard:{page}:{limit}"
        # Set in enhanced cache
        enhanced_cache.set(cache_key, data, ttl=expire)

        # Also set in legacy cache for backward compatibility
        cache.set(cache_key, data, expire=expire)

        logging.debug(f"Cached leaderboard data: {cache_key}")
    except Exception as e:
        logging.error(f"Cache set error: {e}")

def invalidate_leaderboard_cache():
    """Invalidate all leaderboard cache entries using pattern matching."""
    try:
        # Use enhanced cache pattern invalidation
        count = enhanced_cache.invalidate_pattern("leaderboard:*")

        # Also invalidate legacy cache
        keys_to_delete = []
        for key in cache.iterkeys():
            if key.startswith('leaderboard:'):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            cache.delete(key)

        total_invalidated = count + len(keys_to_delete)
        logging.info(f"Invalidated {total_invalidated} leaderboard cache entries (enhanced: {count}, legacy: {len(keys_to_delete)})")
    except Exception as e:
        logging.error(f"Cache invalidation error: {e}")

def get_cache_stats():
    """Get comprehensive cache statistics."""
    try:
        enhanced_stats = enhanced_cache.get_stats()

        # Legacy cache stats
        legacy_stats = {
            "legacy_cache_size": len(cache),
            "legacy_cache_volume": cache.volume()
        }

        return {
            **enhanced_stats,
            **legacy_stats
        }
    except Exception as e:
        logging.error(f"Error getting cache stats: {e}")
        return {}