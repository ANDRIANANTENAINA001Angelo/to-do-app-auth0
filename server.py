"""Python Flask WebApp Auth0 integration example
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from models import db, Todo
from flask import request


from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
db.init_app(app)

with app.app_context():
    db.create_all()


oauth = OAuth(app)

# print("Client ID:", env.get("AUTH0_CLIENT_ID"))
# print("Client Secret:", env.get("AUTH0_CLIENT_SECRET"))

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
    redirect_uri='http://127.0.0.1:3000/callback',  # ou localhost
)


# Controllers API
@app.route("/")
def home():
    todos = []
    if "user" in session:
        user_sub = session["user"]["userinfo"]["sub"]
        todos = Todo.query.filter_by(user_sub=user_sub).all()

    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        todos=todos,
    )



@app.route("/callback", methods=["GET", "POST"])
def callback():
    try:
        # print("in callback")
        token = oauth.auth0.authorize_access_token()
        # print(token)
        session["user"] = token
        # print(session["user"])
        # userinfo = oauth.auth0.parse_id_token(token)
        # session["user"] = userinfo
        return redirect("/")
    except Exception as e:
            # print("Erreur dans callback:", e)
            return f"Erreur dans callback: {e}", 500


@app.route("/login")
def login():
    # print(url_for("callback", _external=True))
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        audience="https://"+ env.get("AUTH0_DOMAIN")+ "/api/v2/"
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


# crud to do list
@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/login")

    task = request.form.get("task")
    user_sub = session["user"]["userinfo"]["sub"]
    if task:
        new_task = Todo(task=task, user_sub=user_sub)
        db.session.add(new_task)
        db.session.commit()
    return redirect("/")


@app.route("/done/<int:todo_id>")
def done(todo_id):
    user_sub = session["user"]["userinfo"]["sub"]
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_sub != user_sub:
        return "Non autorisé", 403
    todo.done = not todo.done
    db.session.commit()
    return redirect("/")


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    user_sub = session["user"]["userinfo"]["sub"]
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_sub != user_sub:
        return "Non autorisé", 403
    db.session.delete(todo)
    db.session.commit()
    return redirect("/")






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
