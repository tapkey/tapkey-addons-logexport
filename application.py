import datetime
from flask import abort, Flask, make_response, url_for, redirect, render_template, request, Response, session
from authlib.flask.client import OAuth
import os
import io
import csv

app = Flask(__name__)

# Set the secret key to some random bytes
app.secret_key = bytearray(os.environ.get('APP_SECRET_KEY'), encoding="utf-8")


def fetch_tapkey_token():
    return session.get('auth')


oauth = OAuth(app)
oauth.register('tapkey',
               client_id=os.environ.get('TAPKEY_CLIENT_ID'),
               client_secret=os.environ.get('TAPKEY_CLIENT_SECRET'),
               access_token_url=os.environ.get('TAPKEY_TOKEN_ENDPOINT'),
               access_token_params=None,
               authorize_url=os.environ.get('TAPKEY_AUTHORIZATION_ENDPOINT'),
               api_base_url=f"{os.environ.get('TAPKEY_BASE_URI')}/api/v1/",
               client_kwargs={
                   'scope': 'manage:contacts manage:grants offline_access read:logs read:grants',
               },
               fetch_token=fetch_tapkey_token,
               )
oauth.init_app(app)


@app.route('/')
def status():
    return 'Service is running.'


@app.route('/tapkey')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.tapkey.authorize_redirect(redirect_uri)


@app.route('/tapkey/callback')
def authorize():
    token = oauth.tapkey.authorize_access_token()
    session['auth'] = token
    return redirect(url_for('owner_account_chooser'))


@app.route('/export')
def owner_account_chooser():
    resp = oauth.tapkey.get('Owners')
    owner_accounts = resp.json()
    for owner_account in owner_accounts:
        resp = oauth.tapkey.get(f"Owners/{owner_account['id']}/BoundLocks")
        owner_account['bound_locks'] = resp.json()
    return render_template('export.html', owner_accounts=owner_accounts)


@app.route('/download')
def download():
    owner_account_id = request.args.get('owner_account_id')
    bound_lock_id = request.args.get('bound_lock_id')

    if owner_account_id.isspace() or bound_lock_id.isspace():
        abort(500)
        abort(Response('Owner Account and Bound Lock required'))
        return

    # Get BoundLock details
    resp = oauth.tapkey.get(f"Owners/{owner_account_id}/BoundLocks/{bound_lock_id}")
    bound_lock = resp.json()

    # Get LogEntries for BoundLock
    resp = oauth.tapkey.get(f"Owners/{owner_account_id}/BoundLocks/{bound_lock_id}/LogEntries?"
                            f"$filter=logType eq 'Command' and command eq 'TriggerLock'&"
                            f"$select=id,entryNo,lockTimestamp,receivedAt,boundCardId,contactId&"
                            f"$orderby=lockTimestamp desc")
    log_entries = resp.json()

    # Get required Contacts
    contacts = []
    contact_ids = list(set(map(lambda x: x['contactId'], log_entries)))
    if not all(x is None for x in contact_ids):
        contact_ids_filter = '$filter=' + 'or'.join(map(lambda x: f"id eq '{x}'", contact_ids))
        resp = oauth.tapkey.get(f"Owners/{owner_account_id}/Contacts?{contact_ids_filter}&"
                                f"$select=id,email")
        contacts = resp.json()

    # Get required BoundCards
    bound_cards = []
    bound_card_ids = list(set(map(lambda x: x['boundCardId'], log_entries)))
    if not all(x is None for x in bound_card_ids):
        bound_card_ids_filter = '$filter=' + 'or'.join(map(lambda x: f"id eq '{x}'", bound_card_ids))
        resp = oauth.tapkey.get(f"Owners/{owner_account_id}/BoundCards?{bound_card_ids_filter}&"
                                f"$select=id,title")
        bound_cards = resp.json()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    for entry in log_entries:
        contact = next((x for x in contacts if x['id'] == entry['contactId']), None)
        bound_card = next((x for x in bound_cards if x['id'] == entry['boundCardId']), None)
        row = [
            entry['contactId'],
            contact['email'] if contact else None,
            entry['boundCardId'],
            bound_card['title'] if bound_card else None,
            entry['lockTimestamp'],
            entry['entryNo'],
            entry['receivedAt'],
            entry['id']
        ]
        writer.writerow(row)
    response = make_response(output.getvalue())
    cd = f"attachment; filename={bound_lock['id']}_{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}.csv"
    response.headers['Content-Disposition'] = cd
    response.mimetype='text/csv'
    return response