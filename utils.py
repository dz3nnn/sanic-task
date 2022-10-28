import uuid
from Crypto.Hash import SHA1
from sanic.response import json


def success_json():
    return json({"success": "true"})


def fake_encode_password(some_pass):
    return some_pass


def fake_decode_password(some_pass):
    return some_pass


def check_hashed_pass(plain_password, encoded_pass):
    if fake_encode_password(plain_password) == encoded_pass:
        return True
    return False


def generate_uuid():
    return str(uuid.uuid4())


def validate_signature(secret_key, json_dict):

    #     {
    #     "signature": "3e3f27b1507f4b766009ee63e41331c0d503916f",
    #     "transaction_id": 1,
    #     "user_id": 1,
    #     "bill_id": 1,
    #     "amount": 100
    # }

    if all(
        k in json_dict
        for k in ("signature", "transaction_id", "user_id", "bill_id", "amount")
    ):
        signature = SHA1.new()
        signature.update(
            f"{secret_key}:{json_dict['transaction_id']}:{json_dict['user_id']}:{json_dict['bill_id']}:{json_dict['amount']}".encode()
        )
        signature_ready = signature.hexdigest()
        return signature_ready == json_dict["signature"]
    return False


def prepare_signature(secret_key, json_dict):
    signature = SHA1.new()
    signature.update(
        f"{secret_key}:{json_dict['transaction_id']}:{json_dict['user_id']}:{json_dict['bill_id']}:{json_dict['amount']}".encode()
    )
    signature_ready = signature.hexdigest()

    return signature_ready
