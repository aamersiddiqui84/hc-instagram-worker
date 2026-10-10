"""Public-account collection via Instaloader; no Meta developer API."""
from datetime import timezone
from itertools import islice

def timestamp(value):
    return int(value.replace(tzinfo=timezone.utc).timestamp())

def post_item(post, reel=False):
    return {'id': str(post.mediaid), 'kind': 'reel' if reel else 'post',
            'url': f'https://www.instagram.com/{"reel" if reel else "p"}/{post.shortcode}/',
            'thumbnail': post.url, 'caption': (post.caption or '')[:500]}

def story_item(item, username, now):
    expiry = timestamp(item.date_utc) + 86400
    if expiry <= now:
        return None
    return {'id': str(item.mediaid), 'kind': 'story',
            'url': f'https://www.instagram.com/stories/{username}/{item.mediaid}/',
            'thumbnail': item.url, 'caption': 'Active story', 'expires_at': expiry}

def collect(loader, profile_factory, username, types, now):
    profile = profile_factory(loader.context, username)
    if profile.is_private:
        raise ValueError('Only public profiles are supported')
    out = {}
    # Separate categories: a Stories failure must not discard successful Posts.
    if 'media' in types:
        try:
            posts = [post_item(p) for p in islice(profile.get_posts(), 20)]
            reels = [post_item(p, reel=True) for p in islice(profile.get_reels(), 20)]
            by_id = {p['id']: p for p in posts}
            by_id.update({p['id']: p for p in reels})
            out['media'] = list(by_id.values())
        except Exception:
            out['media_error'] = 'Media retrieval unavailable'
    if 'stories' in types:
        if not loader.context.is_logged_in:
            out['stories_error'] = 'Server session required for Stories'
        else:
            try:
                items = []
                for story in loader.get_stories(userids=[profile.userid]):
                    for item in islice(story.get_items(), 40):
                        normalized = story_item(item, username, now)
                        if normalized:
                            items.append(normalized)
                out['stories'] = items[:40]
            except Exception:
                out['stories_error'] = 'Stories retrieval unavailable'
    return out
