import os
import bcrypt
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_heroku import Heroku
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
heroku = Heroku(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = ""

CORS(app)
db = SQLAlchemy(app)
ma = Marshmallow(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    username = db.Column(db.String(length=10), unique=True, nullable=False)
    password = db.Column(db.LargeBinary(), nullable=False)

    exercises = db.relationship("Exercise", cascade="all, delete-orphan")
    exercise_stats = db.relationship("ExerciseStat", cascade="all, delete-orphan")
    exercise_goals = db.relationship("ExerciseGoal", cascade="all, delete-orphan")
    body_measurements = db.relationship("BodyMeasurement", cascade="all, delete-orphan")
    body_measurement_goals = db.relationship("BodyMeasurementGoal", cascade="all, delete-orphan")

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


if __name__ == '__main__':
    app.run(debug=True)
