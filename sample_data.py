"""Fictional people and posts used only by the explicit local demo and tests."""

from datetime import datetime, timedelta, timezone

from bson import ObjectId

POST_IDS = [ObjectId(f"67000000000000000000000{i}") for i in range(1, 5)]


def seed_sample_data(database):
    now = datetime.now(timezone.utc)
    database.users.insert_many([
        {"_id": "demo-alex", "username": "alexonrepeat", "display_name": "Alex", "bio": "Mostly indie and soul.", "genres": ["Indie", "Soul"]},
        {"_id": "demo-mina", "username": "mina.mp3", "display_name": "Mina Chen", "bio": "Frank Ocean, SZA, and whatever my friends send me.", "genres": ["R&B", "Alternative"]},
        {"_id": "demo-theo", "username": "theo.fm", "display_name": "Theo James", "bio": "Mostly rock. Send me recommendations.", "genres": ["Rock", "Indie"]},
        {"_id": "demo-noor", "username": "noor.wav", "display_name": "Noor Ali", "bio": "Trying to find new music.", "genres": ["Pop", "Soul"]},
    ])
    database.follows.insert_many([
        {"follower_id": "demo-alex", "followed_id": "demo-mina", "created_at": now},
        {"follower_id": "demo-alex", "followed_id": "demo-theo", "created_at": now},
    ])
    database.posts.insert_many([
        {"_id": POST_IDS[0], "user_id": "demo-mina", "title": "Pink + White", "artist": "Frank Ocean", "spotify_url": "https://open.spotify.com/track/3xKsf9qdS1CyvXSMEid6g8", "caption": "been listening to this all week", "genre": "R&B", "created_at": now - timedelta(minutes=18)},
        {"_id": POST_IDS[1], "user_id": "demo-theo", "title": "Dreams — 2004 Remaster", "artist": "Fleetwood Mac", "spotify_url": "https://open.spotify.com/track/0ofHAoxe9vBkTCp2UQIavz", "caption": "my roommate played this yesterday and now it's stuck in my head", "genre": "Rock", "created_at": now - timedelta(hours=2)},
        {"_id": POST_IDS[2], "user_id": "demo-mina", "title": "The Less I Know The Better", "artist": "Tame Impala", "spotify_url": "https://open.spotify.com/track/6K4t31amVTZDgR3sKmwUJJ", "caption": "anyone know songs with a similar bassline?", "genre": "Alternative", "created_at": now - timedelta(days=1)},
        {"_id": POST_IDS[3], "user_id": "demo-noor", "title": "Dreams — 2004 Remaster", "artist": "Fleetwood Mac", "spotify_url": "https://open.spotify.com/track/0ofHAoxe9vBkTCp2UQIavz", "caption": "heard this at a cafe and had to look it up", "genre": "Rock", "created_at": now - timedelta(minutes=5)},
    ])
    database.votes.insert_many([
        {"user_id": "demo-theo", "post_id": str(POST_IDS[0]), "created_at": now},
        {"user_id": "demo-noor", "post_id": str(POST_IDS[0]), "created_at": now},
        {"user_id": "demo-alex", "post_id": str(POST_IDS[1]), "created_at": now},
    ])
