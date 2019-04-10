from flask import Flask, redirect, url_for
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_dance.contrib.github import make_github_blueprint, github
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissupposedtobeasecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///Users/merry/Documents/GitHub/DancePresentation/login.db'

twitter_blueprint = make_twitter_blueprint(api_key='YYOWvShi57d2zKjPrlli9YeUp',
                                           api_secret='WalZDSnUDL49c9Wk8F8MwJ96cG4moKwpPDeT985F2PSneSdVYa')

github_blueprint = make_github_blueprint(client_id='28924667867edb422ee1',
                                         client_secret='caa82380b1cd2535ba04019cf06311a9c966299d')

app.register_blueprint(twitter_blueprint, url_prefix='/twitter_login')

app.register_blueprint(github_blueprint, url_prefix='/github_login')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True)


class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


twitter_blueprint.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user, user_required=False)


@app.route('/twitter')
def twitter_login():
    if not twitter.authorized:
        return redirect(url_for('twitter.login'))
    account_info = twitter.get('account/settings.json')

    if account_info.ok:
        account_info_json = account_info.json()

    return '<h1>Your Twitter name is @{}'.format(account_info_json['screen_name'])
    return '<h1>Request failed!</h1>'


@oauth_authorized.connect_via(twitter_blueprint)
def twitter_logged_in(blueprint, token):
    account_info = blueprint.session.get('account/settings.json')

    if account_info.ok:
        account_info_json = account_info.json()
        username = account_info_json['screen_name']

        query = User.query.filter_by(username=username)

        try:
            user = query.one()
        except NoResultFound:
            user = User(username=username)
            db.session.add(user)
            db.session.commit()

        login_user(user)


@app.route('/github')
def github_login():
    if not github.authorized:
        return redirect(url_for('github.login'))

    account_info = github.get('/user')

    if account_info.ok:
        account_info_json = account_info.json()

        return '<h1>Your Github name is {}'.format(account_info_json['login'])

    return '<h1>Request failed!</h1>'


@app.route('/')
@login_required
def index():
    return '<h1>You are logged in as {}</h1>'.format(current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
