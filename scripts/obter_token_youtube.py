"""Gera o YT_REFRESH_TOKEN uma única vez (alternativa ao OAuth Playground do README).

Uso (num computador, ou no celular pelo Termux):
    pip install google-auth-oauthlib
    python scripts/obter_token_youtube.py client_secret.json

O client_secret.json é baixado no Google Cloud Console (credencial do tipo "App para computador").
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

ESCOPOS = ["https://www.googleapis.com/auth/youtube.upload"]

if len(sys.argv) != 2:
    sys.exit(__doc__)

fluxo = InstalledAppFlow.from_client_secrets_file(sys.argv[1], ESCOPOS)
cred = fluxo.run_local_server(port=8765, open_browser=True, prompt="consent", access_type="offline")
print("\nCopie estes três valores para os Secrets do GitHub:\n")
print("YT_CLIENT_ID      =", cred.client_id)
print("YT_CLIENT_SECRET  =", cred.client_secret)
print("YT_REFRESH_TOKEN  =", cred.refresh_token)
