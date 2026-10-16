"""PyMongo queries. Relationships use the string returned by get_id()."""

import re
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError


def id_options(identifier):
    """Accept users/posts with string IDs or Mongo's usual ObjectId IDs."""
    value = str(identifier)
    return [value, ObjectId(value)] if ObjectId.is_valid(value) else [value]


class FeedRepository:
    def __init__(self, database):
        self.db = database

    def create_indexes(self):
        self.db.follows.create_index(
            [("follower_id", ASCENDING), ("followed_id", ASCENDING)], unique=True
        )
        self.db.votes.create_index(
            [("user_id", ASCENDING), ("post_id", ASCENDING)], unique=True
        )
        self.db.posts.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    def find_user(self, user_id):
        return self.db.users.find_one({"_id": {"$in": id_options(user_id)}})

    def find_post(self, post_id):
        return self.db.posts.find_one({"_id": {"$in": id_options(post_id)}})

    def followed_ids(self, user_id):
        return self.db.follows.distinct("followed_id", {"follower_id": str(user_id)})

    def following(self, user_id):
        identifiers = [option for uid in self.followed_ids(user_id) for option in id_options(uid)]
        return list(self.db.users.find({"_id": {"$in": identifiers}}).sort("username", ASCENDING))

    def find_people(self, user_id, query="", limit=30):
        criteria = {"_id": {"$nin": id_options(user_id)}}
        if query:
            # Escape user input: a search for .* should search for those characters.
            pattern = re.escape(query)
            criteria["$or"] = [
                {"username": {"$regex": pattern, "$options": "i"}},
                {"display_name": {"$regex": pattern, "$options": "i"}},
            ]
        else:
            criteria["_id"]["$nin"] += [
                option for uid in self.followed_ids(user_id) for option in id_options(uid)
            ]
        return list(self.db.users.find(criteria).sort("username", ASCENDING).limit(limit))

    def feed(self, user_id, page=1, page_size=12, query=""):
        """Following is a chronological feed from followed listeners."""
        return self._posts(user_id, {"user_id": {"$in": self.followed_ids(user_id)}},
                           page, page_size, query, "newest")

    def general_feed(self, user_id, page=1, page_size=12, query="", sort="top"):
        """The general feed includes every listener, regardless of follows."""
        return self._posts(user_id, {}, page, page_size, query, sort)

    def _posts(self, user_id, criteria, page, page_size, query, sort):
        if query:
            pattern = re.escape(query)
            criteria["$or"] = [
                {field: {"$regex": pattern, "$options": "i"}}
                for field in ("title", "artist", "caption")
            ]
        if sort == "top":
            # Rank before pagination, rather than sorting a single visible page.
            documents = list(self.db.posts.aggregate([
                {"$match": criteria},
                {"$addFields": {"_post_key": {"$toString": "$_id"}}},
                {"$lookup": {"from": "votes", "localField": "_post_key",
                             "foreignField": "post_id", "as": "_votes"}},
                {"$addFields": {"_vote_count": {"$size": "$_votes"}}},
                {"$sort": {"_vote_count": -1, "created_at": -1, "_id": -1}},
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size + 1},
                {"$project": {"_post_key": 0, "_votes": 0, "_vote_count": 0}},
            ]))
        else:
            documents = list(
                self.db.posts.find(criteria)
                .sort([("created_at", DESCENDING), ("_id", DESCENDING)])
                .skip((page - 1) * page_size)
                .limit(page_size + 1)
            )
        has_next = len(documents) > page_size
        documents = documents[:page_size]
        post_ids = [str(post["_id"]) for post in documents]
        counts = {
            entry["_id"]: entry["total"]
            for entry in self.db.votes.aggregate([
                {"$match": {"post_id": {"$in": post_ids}}},
                {"$group": {"_id": "$post_id", "total": {"$sum": 1}}},
            ])
        }
        own_votes = set(self.db.votes.distinct(
            "post_id", {"user_id": str(user_id), "post_id": {"$in": post_ids}}
        ))
        author_options = [
            option for uid in {str(post["user_id"]) for post in documents}
            for option in id_options(uid)
        ]
        authors = {
            str(user["_id"]): user
            for user in self.db.users.find({"_id": {"$in": author_options}})
        }
        followed_ids = set(self.followed_ids(user_id))
        for post in documents:
            post["id"] = str(post["_id"])
            post["author"] = authors.get(str(post["user_id"]), {
                "display_name": "Former member", "username": "former-member"
            })
            post["vote_count"] = counts.get(post["id"], 0)
            post["voted"] = post["id"] in own_votes
            post["is_followed"] = str(post["user_id"]) in followed_ids
        return documents, has_next

    def set_follow(self, user_id, target_id, enabled):
        relationship = {"follower_id": str(user_id), "followed_id": str(target_id)}
        if enabled:
            self._insert_once(self.db.follows, relationship)
        else:
            self.db.follows.delete_one(relationship)

    def set_vote(self, user_id, post_id, enabled):
        vote = {"user_id": str(user_id), "post_id": str(post_id)}
        if enabled:
            self._insert_once(self.db.votes, vote)
        else:
            self.db.votes.delete_one(vote)

    @staticmethod
    def _insert_once(collection, key):
        try:
            collection.update_one(
                key,
                {"$setOnInsert": {**key, "created_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
        except DuplicateKeyError:
            # A concurrent request may already have inserted this exact relationship.
            pass
