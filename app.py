import base64
import datetime
from flask import abort, Flask, make_response, url_for, redirect, render_template, request, Response, session
from authlib.integrations.flask_client import OAuth
from applicationinsights.flask.ext import AppInsights
import os
import io
import csv

app = Flask(__name__)

# Check for existence of required environment variables
if 'APP_SECRET_KEY' not in os.environ:
    raise KeyError('APP_SECRET_KEY not found.')
if 'TAPKEY_CLIENT_ID' not in os.environ:
    raise KeyError('TAPKEY_CLIENT_ID not found.')
if 'TAPKEY_CLIENT_SECRET' not in os.environ:
    raise KeyError('TAPKEY_CLIENT_SECRET not found.')

# Set the secret key to some random bytes
app.secret_key = os.environ.get('APP_SECRET_KEY')

# Application Insights (required on Azure only)
if 'APPINSIGHTS_INSTRUMENTATIONKEY' in os.environ:
    app.config['APPINSIGHTS_INSTRUMENTATIONKEY'] = os.environ.get('APPINSIGHTS_INSTRUMENTATIONKEY')
    AppInsights(app)


def fetch_tapkey_token():
    return session.get('auth')


oauth = OAuth(app)
oauth.register('tapkey',
               client_id=os.environ.get('TAPKEY_CLIENT_ID'),
               client_secret=os.environ.get('TAPKEY_CLIENT_SECRET'),
               access_token_url=os.environ.get('TAPKEY_TOKEN_ENDPOINT', 'https://login.tapkey.com/connect/token'),
               access_token_params=None,
               authorize_url=os.environ.get('TAPKEY_AUTHORIZATION_ENDPOINT', 'https://login.tapkey.com/connect/authorize'),
               api_base_url=f"{os.environ.get('TAPKEY_BASE_URI', 'https://my.tapkey.com')}/api/v1/",
               client_kwargs={
                   'scope': 'read:owneraccounts read:core:entities read:logs offline_access',
               },
               fetch_token=fetch_tapkey_token,
               )
oauth.init_app(app)


@app.route('/')
def status():
    return 'Service is running.'


@app.route('/tapkey')
def login():
    """
    Initiates the login flow with Tapkey.
    Redirects the user to the authorization endpoint.
    """
    # Force https redirects when behind a proxy (required on Azure only)
    if 'APPINSIGHTS_INSTRUMENTATIONKEY' in os.environ:  # set on Azure
        redirect_uri = url_for('authorize', _external=True, _scheme='https')
    else:
        redirect_uri = url_for('authorize', _external=True)

    # As this sample does not have a user session management with loging out, this
    # endpoint always starts a new authorization code flow, without detecting if the user
    # might be already logged in.

    return oauth.tapkey.authorize_redirect(redirect_uri)


@app.route('/tapkey/callback')
def authorize():
    """
    Callback endpoint for the Tapkey authorization.
    Handles the authorization response and saves the access token in the session.
    """
    token = oauth.tapkey.authorize_access_token()
    session['auth'] = token
    return redirect(url_for('owner_account_chooser'))


@app.route('/export')
def owner_account_chooser():
    """
    Fetches the owner accounts of the current signed-in user from the Tapkey Web API.
    Renders the export.html template with the owner accounts data.
    """
    owner_accounts = fetch_owner_accounts()
    return render_template('export.html', owner_accounts=owner_accounts)


@app.route('/download')
def download():
    """
    Handles the download of log entries for a specific owner account.
    Fetches log entries, contacts, cards, and locks from the Tapkey Web API.
    Writes the log entries to a CSV file and returns it as a download.
    """
    owner_account_id = request.args.get('owner_account_id')

    if owner_account_id is None or owner_account_id.isspace():
        abort(400)
        abort(Response('Owner Account and Bound Lock required.'))
        return

    # Fetch all the log entries of the owner account
    log_entries = fetch_log_entries(owner_account_id)

    # Fetch all the contacts of the owner account and map them by their ID
    contacts = fetch_contacts(owner_account_id)
    contacts_by_id = {contact['id']: contact for contact in contacts}

    # Fetch all the cards of the owner account and map them by their ID
    cards = fetch_cards(owner_account_id)
    cards_by_id = {card['id']: card for card in cards}

    # Fetch all the locks of the owner account and map them by their ID
    locks = fetch_locks(owner_account_id)
    locks_by_id = {lock['id']: lock for lock in locks}

    # Create a CSV writer to write log entries to CSV
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    # Add CSV Header
    writer.writerow([
        'BoundLockId',
        'Lock Serial Number',
        'Lock Name',
        'Contact ID',
        'Contact Identifier',
        'NFC Transponder ID',
        'NFC Transponder Title',
        'Lock Timestamp',
        'Entry Number',
        'Received At',
        'ID'
    ])

    # Write log entries
    for entry in log_entries:

        # Map entities to this log entry
        contact = contacts_by_id.get(entry.get('contactId'))
        card = cards_by_id.get(entry.get('boundCardId'))
        lock = locks_by_id.get(entry.get('boundLockId'))
        readable_lock_id = to_readable_lock_id(lock['physicalLockId']) if lock else None

        # Add log entry to CSV
        writer.writerow([
            lock.get('id') if lock else None,
            readable_lock_id if lock else None,
            lock.get('title') if lock else None,
            entry.get('contactId'),
            contact.get('identifier') if contact else None,
            entry.get('boundCardId'),
            card.get('title') if card else None,
            entry.get('lockTimestamp'),
            entry.get('entryNo'),
            entry.get('receivedAt'),
            entry.get('id')
        ])

    # Respond as CSV download
    response = make_response(output.getvalue())
    cd = f"attachment; filename={owner_account_id}_{datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')}.csv"
    response.headers['Content-Disposition'] = cd
    response.mimetype = 'text/csv'

    return response


def fetch_owner_accounts():
    """
    Fetches the owner accounts from the Tapkey Web API.

    Returns:
        list: The list of owner accounts.
    """
    resp = oauth.tapkey.get('Owners')
    owner_accounts = resp.json()
    return owner_accounts


def fetch_locks(owner_account_id):
    """
    Fetches the locks associated with the owner account from the Tapkey Web API.

    Args:
        owner_account_id (str): The ID of the owner account.

    Returns:
        list: The list of locks.
    """
    resp = oauth.tapkey.get(f"Owners/{owner_account_id}/BoundLocks")
    locks = resp.json()
    return locks


def fetch_contacts(owner_account_id):
    """
    Fetches the contacts associated with the owner account from the Tapkey Web API.

    Args:
        owner_account_id (str): The ID of the owner account.

    Returns:
        list: The list of contacts.
    """
    resp = oauth.tapkey.get(f"Owners/{owner_account_id}/Contacts?$select=id,identifier")
    contacts = resp.json()
    return contacts


def fetch_cards(owner_account_id):
    """
    Fetches the cards associated with the owner account from the Tapkey Web API.

    Args:
        owner_account_id (str): The ID of the owner account.

    Returns:
        list: The list of cards.
    """
    resp = oauth.tapkey.get(f"Owners/{owner_account_id}/BoundCards?$select=id,title")
    bound_cards = resp.json()
    return bound_cards


def fetch_log_entries(owner_account_id):
    """
    Fetches the log entries associated with the owner account from the Tapkey Web API.

    Args:
        owner_account_id (str): The ID of the owner account.

    Returns:
        list: The list of log entries.
    """
    batch_size = 500
    log_entries = []

    i = 0
    while True:
        i += 1
        skip = batch_size * (i - 1)
        top = batch_size

        resp = oauth.tapkey.get(f"Owners/{owner_account_id}/LogEntries?"
                                f"$skip={skip}&$top={top}&"
                                f"$filter=logType eq 'Command' and command eq 'TriggerLock'&"
                                f"$select=id,entryNo,lockTimestamp,receivedAt,boundLockId,boundCardId,contactId&")

        if resp.status_code != 200:
            abort(500)

        next_log_entries = resp.json()

        if not isinstance(next_log_entries, list):
            abort(500)

        log_entries.extend(next_log_entries)

        if len(next_log_entries) < batch_size:
            break

    return log_entries


def to_readable_lock_id(physical_lock_id):
    """
    Converts a base64 encoded physical lock ID to a readable format.

    Args:
        physical_lock_id (str): The base64 encoded physical lock ID.

    Returns:
        str: The readable lock ID.
    """
    decoded_bytes = base64.b64decode(physical_lock_id)

    # Remove the first two bytes, which represents the length of the ID
    decoded_bytes = decoded_bytes[2:]

    # Convert the decoded bytes to hex and separate with "-"
    hex_string = '-'.join(format(byte, '02x') for byte in decoded_bytes)

    return hex_string
