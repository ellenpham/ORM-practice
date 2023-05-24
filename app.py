from flask import Flask, jsonify, request, abort

app = Flask(__name__)

from flask_marshmallow import Marshmallow
from marshmallow.validate import Length
ma = Marshmallow(app)

from flask_sqlalchemy import SQLAlchemy 
# set the database URI via SQLAlchemy, 
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://db_dev:123456@localhost:5432/trello_clone_db"
# to avoid the deprecation warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#create the database object
db = SQLAlchemy(app)

from flask_bcrypt import Bcrypt
bcrypt = Bcrypt(app)

# create app's cli command named create, then run it in the terminal as "flask create", 
# it will invoke create_db function
@app.cli.command("create")
def create_db():
    db.create_all()
    print("Tables created")

@app.cli.command("seed")
def seed_db():
    from datetime import date
    # create the card object
    card1 = Card(
        # set the attributes, not the id, SQLAlchemy will manage that for us
        title = "Start the project",
        description = "Stage 1, creating the database",
        status = "To Do",
        priority = "High",
        date = date.today()
    )
    # Add the object as a new row to the table
    db.session.add(card1)

    card2 = Card(
        # set the attributes, not the id, SQLAlchemy will manage that for us
        title = "SQLAlchemy and Marshmallow",
        description = "Stage 2, integrate both modules in the project",
        status = "Ongoing",
        priority = "High",
        date = date.today()
    )
    # Add the object as a new row to the table
    db.session.add(card2)

    # seed the users table with a couple of users
    admin_user = User(
        email = "admin@email.com",
        password = bcrypt.generate_password_hash("password123").decode("utf-8"),
        admin = True
    )

    db.session.add(admin_user)

    user_1 = User(
        email = "user1@email.com",
        password = bcrypt.generate_password_hash("123456").decode("utf-8")
    )

    db.session.add(user_1)

    # commit the changes
    db.session.commit()
    print("Table seeded")

@app.cli.command("drop")
def drop_db():
    db.drop_all()
    print("Tables dropped") 

# Model definition area
# Card model
class Card(db.Model):
    # define the table name for the db
    __tablename__= "CARDS"
    # Set the primary key, we need to define that each attribute is also a column in the db table, remember "db" is the object we created in the previous step.
    id = db.Column(db.Integer,primary_key=True)
    # Add the rest of the attributes. 
    title = db.Column(db.String())
    description = db.Column(db.String())
    date = db.Column(db.Date())
    status = db.Column(db.String())
    priority = db.Column(db.String())

# User model
class User(db.Model):
    __tablename__= "USERS"

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(), nullable=False, unique = True)
    password = db.Column(db.String(), nullable=False)
    admin = db.Column(db.Boolean(), default=False)

#create the Card Schema with Marshmallow, it will provide the serialization needed for converting the data into JSON
class CardSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ("id", "title", "description", "date", "status", "priority")

#single card schema, when one card needs to be retrieved
card_schema = CardSchema()
#multiple card schema, when many cards need to be retrieved
cards_schema = CardSchema(many=True)

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
    #set the password's length to a minimum of 6 characters
    password = ma.String(validate=Length(min=6))

user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Route declaration area
@app.route("/")
def hello():
  return "Hello World!"

@app.route("/cards", methods=["GET"])
def get_cards():
    # get all the cards from the database table
    cards_list = Card.query.all()
    # Convert the cards from the database into a JSON format and store them in result
    result = cards_schema.dump(cards_list)
    # return the data in JSON format
    return jsonify(result)

@app.route("/auth/register", methods=["POST"])
def auth_register():
    # The request data will be loaded in a user_schema converted to JSON. 
    # request needs to be imported from
    user_fields = user_schema.load(request.json)

    # find the user
    user = User.query.filter_by(email=user_fields["email"]).first()

    if user:
        # return an abort message to inform the user. That will end the request
        return abort(400, description = "Email already registered")
    
    # Create the user object
    user = User()

    # Add the email attribute
    user.email = user_fields["email"]

    # Add the password attribute hashed by bcrypt
    user.password = bcrypt.generate_password_hash(user_fields["password"]).decode("utf-8")

    # Add it to he database and commit the changes
    db.session.add(user)
    db.session.commit()

    # Return the user to check the request was successful
    return jsonify(user_schema.dump(user))