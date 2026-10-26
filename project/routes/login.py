from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import UserMixin, login_user, logout_user
from werkzeug.security import check_password_hash 

class LoginUser(UserMixin):
    def __init__(self, doc):
        self.id = str(doc["_id"])

login_bp = Blueprint('login', __name__)

@login_bp.post("/login")
@login_bp.post("/login.html")
def login_submit():
    from database import users_collection

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
 
    found = users_collection.find_one({"$or": [
        {"username": username},         
        {"username": username.lower()},
        {"email": username.lower()},     
    ]})
 
    if found and found.get("password_hash") and \
            check_password_hash(found["password_hash"], password):
        login_user(LoginUser(found))
        return redirect(url_for("general_feed.general_feed"))
 
    return render_template("login.html", error="Wrong username or password.")
 
@login_bp.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))
 
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)