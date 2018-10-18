from flask import Flask
from authlib.flask.client import OAuth
import os

app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

oauth = OAuth(app)
oauth.register('tapkey',
    client_id=os.environ.get('TAPKEY_CLIENT_ID'),
    client_secret=os.environ.get('TAPKEY_CLIENT_SECRET'),
    access_token_url='https://login.tapkey.com/connect/token',
    access_token_params=None,
    authorize_url='https://login.tapkey.com/connect/authorize',
    api_base_url='https://my.tapkey.com/api/v1/',
    client_kwargs=None,
)
oauth.init_app(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

from flask import url_for, render_template

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.tapkey.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = oauth.tapkey.authorize_access_token()
    # this is a pseudo method, you need to implement it yourself
    print(token);
    return redirect(url_for('tapkey_profile'))

@app.route('/profile')
def tapkey_profile():
    resp = oauth.tapkey.get('Owners')
    profile = resp.json()
    return profile