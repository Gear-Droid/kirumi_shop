import logging
import requests

from django.conf import settings
from django.core.cache import cache


error_file_logger = logging.getLogger('django')


def get_SDEK_auth_token(url="https://api.cdek.ru", test=False):

    SDEK_auth_token = cache.get('SDEK_auth_token')
    if SDEK_auth_token is None:
        if test:
            SDEK_URL = "https://api.edu.cdek.ru"
            request_data = {
                "grant_type": "client_credentials",
                "client_id": "EMscd6r9JnFiQ3bLoyjJY6eM78JrJceI",
                "client_secret": "PjLZkKBHEiLK3YsjtNrt3TGNG0ahs3kG",
            }
        else:
            SDEK_URL = url
            request_data = {
                "grant_type": "client_credentials",
                "client_id": settings.SDEK_ACCOUNT,
                "client_secret": settings.SDEK_PASSWORD,
            }
        r = requests.post(f"{ SDEK_URL }/v2/oauth/token?parameters", data=request_data)
        SDEK_auth_token = r.json().get("access_token")

        cache.set('SDEK_auth_token', SDEK_auth_token, 60*30)

    return SDEK_auth_token


def get_delivery_calculation(
    to_location, hoodie_packages_count, shirt_packages_count, url="https://api.cdek.ru"):
    try:
        SDEK_access_token = get_SDEK_auth_token()
    except requests.exceptions.RequestException as error:
        error_file_logger.error('SDEK auth request fail: {}'.format(error))
        return None

    request_url = f"{ url }/v2/calculator/tariff"
    headers = {"Authorization": f"Bearer { SDEK_access_token }"}
    hoodie_package = {
        "weight": 1200,
        "length": 30,
        "width": 29,
        "height": 15,
    }
    shirt_package = {
        "weight": 1200,
        "length": 30,
        "width": 29,
        "height": 15,
    }
    request_data = {
        "type": "1",
        "currency": "1",
        # "tariff_code": "233",
        "tariff_code": "137",
        "from_location": {
            "address": "г Москва, ул Сретенка",
            # "postal_code": "142701",
            # "address": "Московская обл, г Видное, ул Завидная, д 4",
        },
        "to_location": {
            "address": to_location,
        },
        "packages": [ hoodie_package for _ in range(hoodie_packages_count) ]
    }
    return requests.post(request_url, headers=headers, json=request_data).json()
