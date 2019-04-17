# Log Export Add-On

This exemplary Tapkey add-on demonstrates how to use the Tapkey Management API
to build a web application allowing users to download a CSV of their Tapkey
access log. The example uses OAuth2 (Authorization Code Flow) to authenticate
against the Tapkey Management API.

The application is written in Python 3, using
[Flask](https://github.com/pallets/flask) as web framework.

You can find this application running on
https://tapkey-addons-logexport.azurewebsites.net/tapkey

## Developer Setup

All code can be found in `application.py`. You can install dependencies using

```
$ pip install -r requirements.txt
```
You may want to use `venv`.

## Requirements

You need a Tapkey Management API client (Authorization Code Flow) with the following permissions:

- Core Entities: `ReadOnly`
- Logs: `ReadOnly`
- Owners: `ReadOnly`

Use `https://<your-domain>/tapkey/callback` as redirect URI, e.g.
`http://127.0.0.1:3000/tapkey/callback` during development.

See https://developers.tapkey.io for more information about Authentication, the Tapkey Management
API and how to set up your own API clients.

The following environment variables are required:

```
APP_SECRET_KEY= # a random string
TAPKEY_CLIENT_ID= # your client id
TAPKEY_CLIENT_SECRET= # your client secret
TAPKEY_AUTHORIZATION_ENDPOINT=https://login.tapkey.com/connect/authorize
TAPKEY_TOKEN_ENDPOINT=https://login.tapkey.com/connect/token
TAPKEY_BASE_URI=https://my.tapkey.com
```

## Usage

Run the application

```
FLASK_APP=application.py
FLASK_ENV=development
FLASK_DEBUG=0

$ ... venv\Scripts\python.exe -m flask run --port 3000
```

and navigate to http://127.0.0.1:3000/tapkey in your browser.

You will be forwarded to login.tapkey.com where you can authenticate as a
Tapkey user and authorize the add-on to access your Tapkey account. Afterwards,
you can choose to download access logs as CSV for each of your registered
locking devices.
