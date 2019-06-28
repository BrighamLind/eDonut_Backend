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

    donuts = db.relationship("Donut", cascade="all, delete-orphan")

    def __init__(self, name, username, password):
        self.name = name
        self.username = username
        self.password = password


class Donut(db.Model):
    __tablename__ = 'donuts'
    id = db.Column(db.Integer, primary_key=True)
    picture = db.Column(db.String(), nullable=True)
    name = db.Column(db.String(30), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(), nullable=False)
    donut_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, picture, name, price, description, donut_user_id):
        self.picture = picture
        self.name = name
        self.price = price
        self.description = description
        self.donut_user_id = donut_user_id


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'username', 'password')


class DonutSchema(ma.Schema):
    class Meta:
        fields = ('id', 'picture', 'name', 'price', 'description', 'donut_user_id')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

donut_schema = DonutSchema()
donuts_schema = DonutSchema(many=True)


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


@app.route("/donut", methods=["POST", "PATCH", "DELETE"])
def create_donut():
    donut_user_id = request.json["userId"]
    user = User.query.get(donut_user_id)

    if user:
        if request.method == "DELETE":
            donut_id = request.json["donutId"]
            donut = Donut.query.get(donut_id)

            if donut:
                donut_to_delete = Donut.query.get(donut_id)

                db.session.delete(donut_to_delete)
                db.session.commit()

                return jsonify({"valid": True, "reason": f"{donut.name} was successfully deleted."})
    
            else:
                return jsonify({"valid": False, "reason": "That donut doesn't exist."})

        elif request.method == "POST" or request.method == "PATCH":
            picture = request.json["picture"]
            name = request.json["name"]
            price = request.json["price"]
            description = request.json["description"]

            if request.method == "POST":
                record = Donut(picture, name, price, description, donut_user_id)
                db.session.add(record)
                db.session.commit()

                record_verif = Donut.query.get(record.id)

                return f"Added {record_verif.name} to your inventory."

            elif request.method == "PATCH":
                donut_id = request.json["donutId"]
                donut = Donut.query.get(donut_id)

                if donut:
                    donut.picture = picture
                    donut.name = name
                    donut.price = price
                    donut.description = description

                    db.session.commit()

                    return donut_schema.jsonify(donut)

                else:
                    return jsonify({"valid": False, "reason": "That donut doesn't exist."})

        else:
            return jsonify({"valid": False, "reason": "Method not allowed."})

    else:
        return "It seems you're not authorized to do that..."


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


@app.route("/inventory", methods=["GET"])
def inventory():
    all_donuts = Donut.query.all()
    result = donuts_schema.dump(all_donuts).data

    return jsonify(result)


# UPDATE

# DELETE


if __name__ == '__main__':
    app.run(debug=True)
