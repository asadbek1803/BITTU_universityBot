from environs import Env

env = Env()
env.read_env()

GOOGLE_CREDENTIALS = {
    "type": env.str("TYPE"),
    "project_id": env.str("PROJECT_ID"),
    "private_key_id": env.str("PRIVATE_KEY_ID"),
    "private_key": env.str("PRIVATE_KEY"),
    "client_email": env.str("CLIENT_EMAIL"),
    "client_id": env.str("CLIENT_ID"),
    "auth_uri": env.str("AUTH_URI"),
    "token_uri": env.str("TOKEN_URI"),
    "auth_provider_x509_cert_url": env.str("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": env.str("CLIENT_X509_CERT_URL"),
    "universe_domain": env.str("UNIVERSE_DOMAIN")
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREAD_SHEET_ID = env.str("SPREAD_SHEET_ID")