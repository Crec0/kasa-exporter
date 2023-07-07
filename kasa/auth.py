from base64 import b64decode

from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.PublicKey.RSA import RsaKey, generate as gen_rsa_key
from httpx import Client

from kasa.crypto import TpLinkCipher, encrypt_email, encrypt_password

ENDPOINT = "https://eu-wap.tplinkcloud.com"

ERROR_CODES = {
    0: "Success",
    -1002: "Incorrect Request",
    -1003: "JSON formatting error",
    -1010: "Invalid Public Key Length",
    -1012: "Invalid terminalUUID",
    -1501: "Invalid Request or Credentials",
}


class Auth:
    def __init__(self, ip: str):
        self.__client = Client(base_url=f"http://{ip}", timeout=3, headers={
            'user-agent': "kasa-exporter/1.0"
        })
        self.__cipher = None

    @property
    def client(self):
        return self.__client

    @property
    def cipher(self):
        return self.__cipher

    def handshake(self):
        private_key = gen_rsa_key(1024)
        public_key = private_key.public_key().export_key("PEM").decode("UTF-8")

        payload = {
            "method": "handshake",
            "params": {
                "key": public_key,
                "requestTimeMils": 0
            }
        }

        response = self.client.post("/app", json=payload)

        encrypted_key = response.json()["result"]["key"].encode("UTF-8")
        self.__cipher = self.__decode_public_key_and_generate_cipher(private_key, encrypted_key)

        try:
            self.client.headers.update({
                "Cookie": f"TP_SESSIONID={response.cookies['TP_SESSIONID']}"
            })
        except KeyError:
            error_code = response.json()["error_code"]
            error_message = ERROR_CODES[error_code]
            raise Exception(f"Error Code ({error_code}): {error_message}")

    def login(self, email: str, password: str) -> None:
        response = self.send_request({
            "method": "login_device",
            "params": {
                "username": encrypt_email(email),
                "password": encrypt_password(password),
            },
            "requestTimeMils": 0,
        })

        try:
            self.client.params = {"token": response["result"]["token"]}
        except KeyError:
            error_code = response["error_code"]
            error_message = ERROR_CODES[error_code]
            raise Exception(f"Error Code ({error_code}): {error_message}")

    def encrypt_and_wrap_payload(self, payload: dict) -> dict:
        return {
            "method": "securePassthrough",
            "params": {
                "request": self.cipher.encrypt(payload)
            }
        }

    def send_request(self, payload: dict) -> dict:
        encrypted_payload = self.encrypt_and_wrap_payload(payload)
        response_json = self.client.post("/app", json=encrypted_payload).json()
        response_data = self.cipher.decrypt(response_json["result"]["response"])
        return response_data

    @staticmethod
    def __decode_public_key_and_generate_cipher(private_key: RsaKey, key: bytes):
        cipher = PKCS1_v1_5.new(private_key)
        decrypted_key = cipher.decrypt(b64decode(key), None)

        if decrypted_key is None:
            raise ValueError("Handshake key decryption failed!")

        return TpLinkCipher(decrypted_key[:16], decrypted_key[16:32])
