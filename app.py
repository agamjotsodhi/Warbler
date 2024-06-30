import os
from flask import Flask, render_template, request, flash, redirect, abort, session, g
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from forms import UserAddForm, LoginForm, MessageForm, EditProfileForm
from models import db, connect_db, User, Message, Likes
from flask_bcrypt import Bcrypt
import pdb

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///warbler')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "warble secret123")
toolbar = DebugToolbarExtension(app)

bcrypt = Bcrypt()
connect_db(app)

##############################################################################
# Routes for user - signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def do_login(user):
    """Log in a user."""
    
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout a user."""
    
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""
    
    # signup form from forms.py
    form = UserAddForm()
    if form.validate_on_submit():
        try:
            # PDB debugger, added breakpoint here to test signup route, uncomment below to use
            # pdb.set_trace()
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()
            
        except IntegrityError:
            # Rollback in case of error - if username already is in database
            db.session.rollback()
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)
        return redirect("/")
    
    else:
        
        return render_template('users/signup.html', form=form)

@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""
    
    # login form from forms.py
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")
        
        # if cred. not in database show error msg: 
        flash("Invalid credentials.", 'danger')
        
    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""
    
    do_logout()
    flash("You have successfully logged out.", "success")
    
    return redirect("/login")

##############################################################################
# General user routes

@app.route('/users')
def list_users():
    """Page with listing of users."""
    
    # Includes the search 'q' parameter in querystring to search by that username
    search = request.args.get('q')
    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()
        
    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user's own profile."""
    
    user = User.query.get_or_404(user_id)
    # snagging messages in order from the database;
    # user.messages won't be in order by default
    
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    likes = [message.id for message in user.likes]
    
    return render_template('users/show.html', user=user, messages=messages, likes=likes)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show all accounts that user is following """
    
    # if not correct user, show error
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of all accounts that follow user."""
    
    # Error if not correct user
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    followed_user = User.query.get_or_404(follow_id)
    g.user.following.append(followed_user)
    db.session.commit()
    
    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    followed_user = User.query.get(follow_id)
    g.user.following.remove(followed_user)
    db.session.commit()
    
    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/<int:user_id>/likes', methods=["GET"])
def show_likes(user_id):
    """Show liked messages for a user."""
    if not g.user:
        flash("Access unauthorized error. Please log in.", "danger")
        return redirect("/")
    
    user = User.query.get_or_404(user_id)
    
    return render_template('users/likes.html', user=user, likes=user.likes)


##############################################################################
# Messages routes

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message."""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()
        return redirect(f"/users/{g.user.id}")
    
    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""
    msg = Message.query.get(message_id)
    
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()
    
    return redirect(f"/users/{g.user.id}")


@app.route('/messages/<int:message_id>/like', methods=['POST'])
def add_like(message_id):
    """User liking a post functionality """
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    liked_message = Message.query.get_or_404(message_id)
    
    # Display error if user likes there own post
    if liked_message.user_id == g.user.id:
        return abort(403)
    
    # Add to user's likes in database
    user_likes = g.user.likes
    if liked_message in user_likes:
        g.user.likes = [like for like in user_likes if like != liked_message]
    else:
        g.user.likes.append(liked_message)
    db.session.commit()
    
    return redirect("/")


##############################################################################
# User profile

@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = EditProfileForm(obj=g.user)
    if form.validate_on_submit():
        if bcrypt.check_password_hash(g.user.password, form.password.data):
            g.user.username = form.username.data
            g.user.email = form.email.data
            g.user.image_url = form.image_url.data
            g.user.header_image_url = form.header_image_url.data
            g.user.location = form.location.data
            g.user.bio = form.bio.data
            
            # succesful update
            db.session.commit()
            flash("Profile successfully updated!", "success")
            return redirect(f"/users/{g.user.id}")
        else:
            # error handling for incorrect cred.
            flash("Incorrect Password, profile could not be updated.", "danger")
            return redirect("/")
        
    return render_template("users/edit.html", form=form, user_id=g.user.id)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    do_logout()
    db.session.delete(g.user)
    db.session.commit()
    
    return redirect("/signup")


##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    """Show homepage:
    - fetch the ids of accounts the user is following including user's id
    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """
    
    if g.user:
        following_ids = [f.id for f in g.user.following]
        following_ids.append(g.user.id)
        
        if not following_ids:
            flash("No new messages. To read more warbles, follow more people!")
            messages = []
        else:
            messages = (Message.query.filter(Message.user_id.in_(following_ids))
                        .order_by(Message.timestamp.desc()).limit(100).all())
        return render_template('home.html', messages=messages)
    else:
        
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""
    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    
    return req
