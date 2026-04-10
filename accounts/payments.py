"""
Платёжные провайдеры: 2Checkout (Кыргызстан, международные) и Robokassa (СНГ).
"""
import hashlib
from decimal import Decimal
from django.conf import settings


# Цены подписки (USD для 2Checkout, можно конвертировать для Robokassa в рубли)
PRICE_MONTHLY_USD = Decimal('6.00')
PRICE_YEARLY_USD = Decimal('55.00')
# Для Robokassa можно задать в рублях или брать из настроек
PRICE_MONTHLY_RUB = Decimal('590')   # примерный курс
PRICE_YEARLY_RUB = Decimal('5390')


def get_2checkout_config():
    sid = getattr(settings, 'TWOCHECKOUT_SID', '').strip()
    secret = getattr(settings, 'TWOCHECKOUT_SECRET_WORD', '').strip()
    return sid, secret


def get_robokassa_config():
    login = getattr(settings, 'ROBOKASSA_LOGIN', '').strip()
    p1 = getattr(settings, 'ROBOKASSA_PASSWORD1', '').strip()
    p2 = getattr(settings, 'ROBOKASSA_PASSWORD2', '').strip()
    return login, p1, p2


def build_2checkout_form_data(pending_id, plan, user_email, success_url):
    """Параметры формы POST для редиректа в 2Checkout."""
    sid, _ = get_2checkout_config()
    if not sid:
        return None
    price = PRICE_YEARLY_USD if plan == 'yearly' else PRICE_MONTHLY_USD
    name = 'FC Arena PRO — 1 год' if plan == 'yearly' else 'FC Arena PRO — 1 месяц'
    data = {
        'sid': sid,
        'mode': '2CO',
        'li_0_type': 'product',
        'li_0_name': name,
        'li_0_product_id': str(pending_id),
        'li_0_quantity': '1',
        'li_0_price': str(price),
        'li_0_tangible': 'N',
        'merchant_order_id': str(pending_id),
        'x_receipt_link_url': success_url,
        'email': user_email or '',
        'currency_code': 'USD',
    }
    if getattr(settings, 'TWOCHECKOUT_DEMO', False):
        data['demo'] = 'Y'
    return data


def verify_2checkout_return(order_number, total, key, merchant_order_id):
    """Проверка подписи возврата 2Checkout. key = UPPERCASE(MD5(secret + sid + order_number + total))."""
    sid, secret = get_2checkout_config()
    if not sid or not secret:
        return False
    # Demo sales use "1" instead of order_number in hash
    from django.conf import settings as s
    demo = getattr(s, 'TWOCHECKOUT_DEMO', False)
    order_for_hash = '1' if demo else str(order_number)
    s = f'{secret}{sid}{order_for_hash}{total}'
    expected = hashlib.md5(s.encode()).hexdigest().upper()
    return key and key.upper() == expected and str(merchant_order_id).isdigit()


def build_robokassa_form_data(pending_id, plan, user_email, result_url, success_url, fail_url):
    """Параметры формы POST для редиректа в Robokassa. Подпись с SuccessUrl2/FailUrl2."""
    login, p1, p2 = get_robokassa_config()
    if not login or not p1:
        return None
    amount = PRICE_YEARLY_RUB if plan == 'yearly' else PRICE_MONTHLY_RUB
    desc = 'FC Arena PRO — 1 год' if plan == 'yearly' else 'FC Arena PRO — 1 месяц'
    # Подпись с модификаторами: FailUrl2Method, FailUrl2, SuccessUrl2Method, SuccessUrl2 (порядок из доки)
    success_url = success_url or ''
    fail_url = fail_url or ''
    sig_parts = [login, str(amount), str(pending_id), 'GET', fail_url, 'GET', success_url, p1]
    s = ':'.join(sig_parts)
    signature = hashlib.md5(s.encode()).hexdigest().upper()
    data = {
        'MerchantLogin': login,
        'OutSum': str(amount),
        'InvId': pending_id,
        'Description': desc[:100],
        'SignatureValue': signature,
        'Encoding': 'utf-8',
        'Culture': 'ru',
        'IsTest': '1' if getattr(settings, 'ROBOKASSA_TEST', True) else '0',
    }
    if result_url:
        data['ResultUrl'] = result_url
    if success_url:
        data['SuccessUrl2'] = success_url
        data['SuccessUrl2Method'] = 'GET'
    if fail_url:
        data['FailUrl2'] = fail_url
        data['FailUrl2Method'] = 'GET'
    if user_email:
        data['Email'] = user_email
    return data


def verify_robokassa_result(out_sum, inv_id, signature):
    """Проверка подписи Result URL Robokassa. Signature = MD5(OutSum:InvId:Password2)."""
    _, _, p2 = get_robokassa_config()
    if not p2:
        return False
    s = f'{out_sum}:{inv_id}:{p2}'
    expected = hashlib.md5(s.encode()).hexdigest().upper()
    return signature and signature.upper() == expected


def verify_2checkout_ipn(post_data, signature_sha2_256):
    """
    Проверка подписи IPN 2Checkout (HMAC-SHA256).
    post_data — словарь параметров IPN; signature_sha2_256 — полученная подпись.
    """
    import hmac as hm
    _, secret = get_2checkout_config()
    if not secret:
        return False
    # 2Checkout: подпись = HMAC-SHA256(secret, sorted params: len+value)
    keys = sorted(k for k in post_data if k != 'SIGNATURE_SHA2_256' and post_data[k])
    message = ''.join(f'{len(str(post_data[k]).encode("utf-8"))}{post_data[k]}' for k in keys)
    expected = hm.new(secret.encode('utf-8'), message.encode('utf-8'), 'sha256').hexdigest()
    return hm.compare_digest(expected, signature_sha2_256 or '')
