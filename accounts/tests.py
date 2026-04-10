# -*- coding: utf-8 -*-
"""
Критические тесты: активация подписки (Robokassa, 2Checkout IPN), показ рекламы для PRO.
"""
import hashlib
from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from .models import UserProfile, PendingSubscriptionPayment
from . import payments
from .context_processors import saas_context

User = get_user_model()


@override_settings(
    ROBOKASSA_LOGIN='test_merchant',
    ROBOKASSA_PASSWORD1='pass1',
    ROBOKASSA_PASSWORD2='pass2',
)
class RobokassaResultTest(TestCase):
    """Активация подписки по Result URL Robokassa: проверка подписи и установка PRO."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='t@t.com', password='testpass123')
        UserProfile.objects.get_or_create(user=self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def _build_signature(self, out_sum, inv_id):
        _, _, p2 = payments.get_robokassa_config()
        s = f'{out_sum}:{inv_id}:{p2}'
        return hashlib.md5(s.encode()).hexdigest().upper()

    def test_robokassa_result_activates_subscription(self):
        """Валидный Result URL активирует подписку и возвращает OK<InvId>."""
        pending = PendingSubscriptionPayment.objects.create(
            user=self.user,
            plan=UserProfile.PLAN_MONTHLY,
            provider=PendingSubscriptionPayment.PROVIDER_ROBOKASSA,
            amount=payments.PRICE_MONTHLY_RUB,
        )
        out_sum = str(payments.PRICE_MONTHLY_RUB)
        inv_id = str(pending.id)
        signature = self._build_signature(out_sum, inv_id)
        response = self.client.post(
            reverse('robokassa_result'),
            data={'OutSum': out_sum, 'InvId': inv_id, 'SignatureValue': signature},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), f'OK{inv_id}')
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_type, 'PRO')
        self.assertEqual(self.user.profile.plan, UserProfile.PLAN_MONTHLY)
        self.assertFalse(PendingSubscriptionPayment.objects.filter(id=pending.id).exists())

    def test_robokassa_result_bad_signature_rejected(self):
        """Неверная подпись — 400, подписка не активируется."""
        pending = PendingSubscriptionPayment.objects.create(
            user=self.user,
            plan=UserProfile.PLAN_MONTHLY,
            provider=PendingSubscriptionPayment.PROVIDER_ROBOKASSA,
            amount=payments.PRICE_MONTHLY_RUB,
        )
        response = self.client.post(
            reverse('robokassa_result'),
            data={
                'OutSum': str(payments.PRICE_MONTHLY_RUB),
                'InvId': str(pending.id),
                'SignatureValue': 'WRONGSIGN',
            },
        )
        self.assertEqual(response.status_code, 400)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_type, 'FREE')
        self.assertTrue(PendingSubscriptionPayment.objects.filter(id=pending.id).exists())


class TwoCheckoutIPNTest(TestCase):
    """Активация подписки по IPN 2Checkout (без проверки HMAC в тесте — без секрета)."""

    def setUp(self):
        self.user = User.objects.create_user(username='ipnuser', email='ipn@t.com', password='testpass123')
        UserProfile.objects.get_or_create(user=self.user)

    def test_twocheckout_ipn_activates_subscription(self):
        """POST с ORDERSTATUS=COMPLETE и MERCHANT_ORDER_ID активирует PRO (без подписи в тесте)."""
        pending = PendingSubscriptionPayment.objects.create(
            user=self.user,
            plan=UserProfile.PLAN_YEARLY,
            provider=PendingSubscriptionPayment.PROVIDER_2CHECKOUT,
            amount=payments.PRICE_YEARLY_USD,
        )
        # Явно form-urlencoded, как реальный IPN 2Checkout
        response = self.client.post(
            reverse('twocheckout_ipn'),
            data='ORDERSTATUS=COMPLETE&MERCHANT_ORDER_ID=' + str(pending.id),
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200, msg=response.content.decode())
        body = response.content.decode()
        self.assertIn(str(pending.id), body, msg='Expected OK<pending_id>, got %s' % body)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_type, 'PRO')
        self.assertEqual(self.user.profile.plan, UserProfile.PLAN_YEARLY)
        self.assertFalse(PendingSubscriptionPayment.objects.filter(id=pending.id).exists())

    def test_twocheckout_ipn_skip_wrong_status(self):
        """ORDERSTATUS не COMPLETE/PAYMENT_RECEIVED — 200 skip, подписка не меняется."""
        pending = PendingSubscriptionPayment.objects.create(
            user=self.user,
            plan=UserProfile.PLAN_MONTHLY,
            provider=PendingSubscriptionPayment.PROVIDER_2CHECKOUT,
            amount=payments.PRICE_MONTHLY_USD,
        )
        response = self.client.post(
            reverse('twocheckout_ipn'),
            data={'ORDERSTATUS': 'PENDING', 'MERCHANT_ORDER_ID': str(pending.id)},
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'skip')
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.subscription_type, 'FREE')
        self.assertTrue(PendingSubscriptionPayment.objects.filter(id=pending.id).exists())


class AdsContextProcessorTest(TestCase):
    """Проверка: для PRO пользователя show_ads = False."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_pro_user_has_show_ads_false(self):
        """У пользователя с subscription_type=PRO реклама скрыта."""
        user = User.objects.create_user(username='prouser', email='pro@t.com', password='testpass123')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.subscription_type = 'PRO'
        profile.save()
        request = self.factory.get('/')
        request.user = user
        ctx = saas_context(request)
        self.assertFalse(ctx['show_ads'])
        self.assertTrue(ctx['is_pro'])

    def test_free_user_has_show_ads_true(self):
        """У пользователя FREE реклама показывается."""
        user = User.objects.create_user(username='freeuser', email='free@t.com', password='testpass123')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.subscription_type = 'FREE'
        profile.save()
        request = self.factory.get('/')
        request.user = user
        ctx = saas_context(request)
        self.assertTrue(ctx['show_ads'])

    def test_anonymous_has_show_ads_true(self):
        """Гость видит рекламу."""
        request = self.factory.get('/')
        request.user = AnonymousUser()
        ctx = saas_context(request)
        self.assertTrue(ctx['show_ads'])
