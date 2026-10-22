from flask import Flask, jsonify, request

import pymongo
from bson.objectid import ObjectId
import datetime
from database import users_collection, posts_collection, votes_collection, follows_collection

app = Flask(__name__)

# Basic GET endpoint returning JSON
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Flask backend is running"}), 200

if __name__ == '__main__':
    # Run development server with auto-reload enabled
    app.run(debug=True, port=5000)