import os
import bcrypt
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
heroku = Heroku(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://ndqbfkziohkzeb:9bc936bfdd050b1a3a20e151463fb443a07be1066c0017f2bf0d252929028cd8@ec2-107-21-216-112.compute-1.amazonaws.com:5432/d5fklgc90rvprp"

CORS(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(26), nullable=False)
    username = db.Column(db.String(26), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(), nullable=False)


    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'username', 'password')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# CREATE
@app.route("/signup", methods=["POST"])
def signup():
    name = request.json["name"]
    username = request.json["username"]
    password = request.json["password"]

    if User.query.filter_by(username=username).first():
        invalid = {"valid": False,
        "username": username}

        return jsonify(invalid)

    else:
        hashed_password = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        record = User(name, username, hashed_password)
        db.session.add(record)
        db.session.commit()

        record_verif = User.query.get(record.id)
        
        valid = {"valid": True,
        "name": record_verif.name,
        "id": record_verif.id}
        
        return jsonify(valid)

# READ
@app.route("/login", methods=["POST"])
def login():
    submitted_username = request.json["username"]
    submitted_password = request.json["password"]
    user = User.query.filter_by(username=submitted_username).first()

    if user:
        if bcrypt.checkpw(submitted_password.encode("utf8"), user.password):
            valid = {"valid": True, "name": user.name,
            "id": user.id}
            
            return jsonify(valid)

        else:
            invalid = {"valid": False, "reason": "Incorrect Password"}

            return jsonify(invalid)
            
    else:
        invalid = {"valid": False, "reason": "User doesn't exist"}

        return jsonify(invalid)

# UPDATE

# DELETE


if __name__ == '__main__':
    app.run(debug=True)
