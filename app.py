from flask import Flask, render_template, flash, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import random
import xml.etree.ElementTree as ET
import urllib.request
import os



#app configure
app = Flask(__name__)
app.secret_key = os.urandom(24)

#database config
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash=db.Column(db.String(120), nullable=False)
    score=db.Column(db.Integer)
    def __repr__(self):
        return '<User %r>' % self.username

# Ensure responses aren't cached for dev purposes only i hoooppe
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

#meh meh
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    global_score=db.session.query(func.sum(User.score).label("score"))
    global_score=global_score.scalar()
    return render_template("index.html",global_score=global_score)

@app.route('/register', methods = ["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        login=request.form.get("username")
        result=User.query.filter_by(username=login).first()
        if result:
            flash("Username already exists")
            return render_template("register.html")
        else:
            password_hash=generate_password_hash(request.form.get("password"))
            new_user=User(username=login, hash=password_hash, score=0)
            db.session.add(new_user)
            db.session.commit()
            session["user_id"]=new_user.id
            flash("Herzlich Willkomen")
            return redirect("/")

@app.route("/landing", methods=["GET","POST"])
@login_required
def landing():
    user=User.query.filter_by(id=session["user_id"]).first()
    if request.method == "POST":
        if request.form.get("ebay")=="ebay":
            user.score=user.score-1
            db.session.commit()
            return  redirect(session["item_url"])
        if request.form.get("charity")=="charity":
            user.score=user.score+1
            db.session.commit()
            return redirect("https://www.unicef.org/")
        if request.form.get("amount"):
            session["max_value"]=int (request.form.get("amount"))
            session["min_value"]=0.8* int(request.form.get("amount"))
        counter=0
        while True:
            url=("http://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsByKeywords"
            "&SERVICE-VERSION=1.0.0"
            "&SECURITY-APPNAME=PioreGrn-thechoos-PRD-82ccbdebc-5ffa1461"
            "&RESPONSE-DATA-FORMAT=XML"
            "&REST-PAYLOAD"
            f"&keywords={random_word()}"
            "&itemFilter(0).name=MaxPrice"
            f"&itemFilter(0).value={session['max_value']}"
            "&itemFilter(1).name=MinPrice"
            f"&itemFilter(1).value={session['min_value']}")
            response = urllib.request.urlopen(url)
            tree=ET.parse(response)
            root = tree.getroot()
            results=root[3]
            number_of_results=int (results.attrib['count'])
            counter+=1
            if counter >4:
                flash("Opps no reults try again")
                return redirect("/")
            if number_of_results != 0:
                break
        item=results[random.randrange(number_of_results)]
        item_title=item[1].text
        item_url=item[5].text
        item_picture=item[4].text
        session["item_url"]=item_url
        return render_template("landing.html", item_title=item_title, item_url=item_url, item_picture=item_picture, score=user.score)
    else:
        return render_template("landing.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/login", methods=["GET","POST"])
def login():
    session.clear()
    if request.method == "POST":
        login=request.form.get("username")
        password=request.form.get("password")
        user=User.query.filter_by(username=login).first()
        if not user or not check_password_hash(user.hash,password):
            flash("Wrong login or password")
            return render_template("login.html")
        else:
            session["user_id"]=user.id
            return redirect("/landing")
    else:
        return render_template("login.html")

@app.route("/change", methods=["GET","POST"])
@login_required
def change():
    if request.method=="GET":
        return render_template("change.html")
    else:
        user=User.query.filter_by(id=session["user_id"]).first()
        password_hash=generate_password_hash(request.form.get("password"))
        user.hash=password_hash
        db.session.commit()
        flash("Password changed")
        return redirect("/")

def random_word():
    return(random.choice(open('shakespeare.txt').read().split()).strip())
