import datetime
from bson.objectid import ObjectId
from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import app  

def get_db():
    from database import users_collection
    return users_collection.database

def go_back():
    return redirect(request.referrer or url_for("communities"))

def communities_page():
    db = get_db()
    user_id = ObjectId(current_user.id) if current_user.is_authenticated else None

    communities = list(db["communities"].find())
    for c in communities:
        c["id"] = str(c["_id"])
        c["member_count"] = db["community_memberships"].count_documents(
            {"community_id": c["_id"]})
        c["joined"] = bool(user_id and db["community_memberships"].find_one(
            {"user_id": user_id, "community_id": c["_id"]}))
    communities.sort(key=lambda c: c["member_count"], reverse=True)

    return render_template("community.html",
                           featured=communities[0] if communities else None,
                           communities=communities[1:])

app.view_functions["communities"] = communities_page

@app.post("/communities/new")
@login_required
def create_community():
    db = get_db()
    name = request.form.get("name", "").strip().lower()
    if name.startswith("r/"):
        name = name[2:]

    if name and not db["communities"].find_one({"name": name}):
        user_id = ObjectId(current_user.id)
        result = db["communities"].insert_one({
            "name": name,
            "description": request.form.get("description", "").strip(),
            "created_by": user_id,
        })
        db["community_memberships"].insert_one({
            "user_id": user_id,
            "community_id": result.inserted_id,
            "joined_at": datetime.datetime.utcnow(),
        })
    return go_back()

@app.post("/communities/<community_id>/join")
@login_required
def join_community(community_id):
    db = get_db()
    membership = {"user_id": ObjectId(current_user.id),
                  "community_id": ObjectId(community_id)}
    if not db["community_memberships"].find_one(membership):
        membership["joined_at"] = datetime.datetime.utcnow()
        db["community_memberships"].insert_one(membership)
    return go_back()

@app.post("/communities/<community_id>/leave")
@login_required
def leave_community(community_id):
    get_db()["community_memberships"].delete_one(
        {"user_id": ObjectId(current_user.id),
         "community_id": ObjectId(community_id)})
    return go_back()