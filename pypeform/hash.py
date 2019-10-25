import hmac
import hashlib
import base64


def compute_signature(message: str, api_secret: str) -> str:
    signature = hmac.new(
        key=api_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return 'sha256=' + base64.b64encode(signature).decode('utf-8')
