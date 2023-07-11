# Log Export Add-On

The Log Export Add-On is an exemplary Tapkey add-on that demonstrates how to use the Tapkey Web API to build a web
application that allows users to download a CSV of their Tapkey access log. This documentation provides instructions on
how to set up and run the application.

## Requirements

Before using the Log Export Add-On, make sure you have created
an [Authorization Code Client](https://developers.tapkey.io/api/authentication/registration/#authorization-code) with
the following scopes:

- Core Entities: `ReadOnly`
- Logs: `ReadOnly`
- Owners: `ReadOnly`

During development, set the redirect URI to `https://<your-domain>/tapkey/callback`, for
example, `http://127.0.0.1:3000/tapkey/callback`.

For more information on authentication, the Tapkey Management API, and setting up your API clients, visit
the [Tapkey Developer Portal](https://developers.tapkey.io).

## Usage

The Log Export Add-On is written in Python 3 and uses the Flask web framework. All the code can be found in the `app.py`
file and has been tested with Python 3.11.

### Configuration

The application can be configured using environment variables. The following environment variables are required and must
be set:

| Environment Variable | Description                                                                                                                       |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| TAPKEY_CLIENT_ID     | The ID of the OAuth client created upfront (refer to [Requirements](#Requirements)).                                              |
| TAPKEY_CLIENT_SECRET | The client secret of the created OAuth client. Keep this secret and do not share it with anyone.                                  |
| APP_SECRET_KEY       | A strong random string used by Flask to encrypt [user sessions](https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions). |

### Running the Application Locally (Linux, Unix)

To run the application locally, it is recommended to use `venv`. Follow these steps:

1. Create a new Python environment:
   ```
   $ python3 -m venv "venv"
   ```

2. Activate the virtual environment:
   ```
   $ source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   $ pip install -r requirements.txt
   ```

4. Configure the application via environment variables. The method for setting environment variables may vary depending
   on your operating system and shell. Set the following variables:
   ```
   export APP_SECRET_KEY= # a random string
   export TAPKEY_CLIENT_ID= # your client id
   export TAPKEY_CLIENT_SECRET= # your client secret
   ```

5. Start the application using the following command:
   ```
   $ flask run --port 3000
   ```

### Running the Application Locally (Windows)

To run the application locally on Windows, follow these steps:

1. Create a new Python environment:
   ```
   $ python -m venv venv
   ```

2. Activate the virtual environment:
   ```
   $ venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   $ pip install -r requirements.txt
   ```

4. Configure the application via environment variables. The method for setting environment variables may vary depending on your command prompt. Set the following variables:
   ```
   $env:APP_SECRET_KEY="# a random string"
   $env:TAPKEY_CLIENT_ID="# your client id"
   $env:TAPKEY_CLIENT_SECRET="# your client secret"
   ```

5. Start the application using the following command:
   ```
   $ flask run --port 3000
   ```

### Running the Application in Docker

To run the application in a Docker container, a Dockerfile is provided. Follow these steps:

1. Build the Docker container:
   ```
   $ docker build . -t tapkey-addons-logexport
   ```

2. Configure the application using a `Docker.env` file. This file will be used to set the environment variables when
   running the Docker container.

3. Run the Docker container using the following command:
   ```
   $ docker run -p 127.0.0.1:3000:3000 --rm --env-file=Docker.env tapkey-addons-logexport
   ```

   Note: If you modify the `app.py` file, you will need to rebuild the Docker image to apply the changes.

### Opening the Application

To access the Log Export Add-On application, open your browser and navigate to http://127.0.0.1:3000/tapkey.

You will be redirected to login.tapkey.com, where you can authenticate as a Tapkey user and authorize the add-on to
access your Tapkey account. Once authenticated, you can choose to download access logs as a CSV file for the locking
system.