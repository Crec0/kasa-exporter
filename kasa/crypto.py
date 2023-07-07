import json
from base64 import b64encode, b64decode
from typing import Mapping

import pkcs7 as pkcs7
from Cryptodome.Cipher import AES
from hashlib import sha1


class TpLinkCipher:
    def __init__(self, key: bytes, iv: bytes):
        self.key = key
        self.iv = iv

    def encrypt(self, data: Mapping[str, str | int]):
        json_data = json.dumps(data)
        data: str = pkcs7.PKCS7Encoder().encode(json_data)
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        encrypted = aes.encrypt(data.encode("UTF-8"))
        return b64encode(encrypted).decode("UTF-8").replace("\r\n", "")

    def decrypt(self, data: str) -> Mapping[str, str | int]:
        aes = AES.new(self.key, AES.MODE_CBC, self.iv)
        pad_text = aes.decrypt(b64decode(data.encode("UTF-8"))).decode("UTF-8")
        decrypted_json = pkcs7.PKCS7Encoder().decode(pad_text)
        return json.loads(decrypted_json)


def encrypt_email(email: str):
    email_hex = sha1(email.encode("UTF-8")).digest().hex()
    return b64encode(email_hex.encode("UTF-8")).decode("UTF-8")


def encrypt_password(password: str):
    return b64encode(password.encode("UTF-8")).decode("UTF-8")
