from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import login, logout, get_user_model
from django.conf import settings
from .forms import RegisterForm, LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile, GameProfile, ProfileStats, PendingSubscriptionPayment
from .services import user_is_pro, get_or_create_default_game_profile, get_profiles_for_user, can_add_game_profile
from . import payments

User = get_user_model()


def register_view(request):
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Регистрация успешна. Добро пожаловать!')
            return redirect('index')
        messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Вход в аккаунт."""
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f'Вы вошли как {user.username}.')
            next_url = request.GET.get('next') or 'index'
            return redirect(next_url)
        messages.error(request, 'Неверный логин или пароль.')
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Выход."""
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта.')
    return redirect('index')


@login_required
def profile_view(request):
    """Профиль и подписка."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    payment_success = request.GET.get('payment') == 'success'
    return render(request, 'accounts/profile.html', {'profile': profile, 'payment_success': payment_success})


def subscription_view(request):
    """Тарифы: оплата через 2Checkout (Кыргызстан/мир) или Robokassa (СНГ)."""
    has_2checkout = bool(getattr(settings, 'TWOCHECKOUT_SID', '').strip() and getattr(settings, 'TWOCHECKOUT_SECRET_WORD', '').strip())
    has_robokassa = bool(getattr(settings, 'ROBOKASSA_LOGIN', '').strip() and getattr(settings, 'ROBOKASSA_PASSWORD1', '').strip())
    payment_fail = request.GET.get('payment') == 'fail'
    return render(request, 'accounts/subscription.html', {
        'has_2checkout': has_2checkout,
        'has_robokassa': has_robokassa,
        'has_payment': has_2checkout or has_robokassa,
        'payment_fail': payment_fail,
    })


@login_required
def subscription_checkout_view(request):
    """Редирект на 2Checkout или Robokassa: создаём PendingSubscriptionPayment и отдаём форму POST."""
    if request.method != 'POST':
        return redirect('subscription')
    plan = request.POST.get('plan')
    provider = request.POST.get('provider')
    if plan not in ('monthly', 'yearly'):
        messages.error(request, 'Выберите тариф: месяц или год.')
        return redirect('subscription')
    if provider not in ('2checkout', 'robokassa'):
        messages.error(request, 'Выберите способ оплаты.')
        return redirect('subscription')

    amount = payments.PRICE_YEARLY_USD if plan == 'yearly' else payments.PRICE_MONTHLY_USD
    if provider == 'robokassa':
        amount = payments.PRICE_YEARLY_RUB if plan == 'yearly' else payments.PRICE_MONTHLY_RUB

    pending = PendingSubscriptionPayment.objects.create(
        user=request.user,
        plan=plan,
        provider=provider,
        amount=amount,
    )
    user_email = getattr(request.user, 'email', '') or ''

    if provider == '2checkout':
        sid, _ = payments.get_2checkout_config()
        if not sid:
            pending.delete()
            messages.info(request, 'Оплата 2Checkout временно недоступна.')
            return redirect('subscription')
        success_url = request.build_absolute_uri('/accounts/subscription/success/')
        form_data = payments.build_2checkout_form_data(pending.id, plan, user_email, success_url)
        if not form_data:
            pending.delete()
            return redirect('subscription')
        checkout_url = getattr(settings, 'TWOCHECKOUT_CHECKOUT_URL', 'https://www.2checkout.com/checkout/purchase')
        return render(request, 'accounts/payment_redirect.html', {
            'form_data': form_data,
            'form_action': checkout_url,
            'provider_name': '2Checkout',
        })

    if provider == 'robokassa':
        login_r, _ = payments.get_robokassa_config()
        if not login_r:
            pending.delete()
            messages.info(request, 'Оплата Robokassa временно недоступна.')
            return redirect('subscription')
        base = request.build_absolute_uri('/').rstrip('/')
        result_url = base + '/accounts/payment/robokassa/result/'
        success_url = base + '/accounts/payment/robokassa/success/'
        fail_url = base + '/accounts/subscription/'
        form_data = payments.build_robokassa_form_data(
            pending.id, plan, user_email, result_url, success_url, fail_url
        )
        if not form_data:
            pending.delete()
            return redirect('subscription')
        robokassa_url = getattr(settings, 'ROBOKASSA_URL', 'https://auth.robokassa.ru/Merchant/Index.aspx')
        return render(request, 'accounts/payment_redirect.html', {
            'form_data': form_data,
            'form_action': robokassa_url,
            'provider_name': 'Robokassa',
        })

    pending.delete()
    return redirect('subscription')


def subscription_success_view(request):
    """Возврат после оплаты 2Checkout: проверка key (MD5), активация подписки по merchant_order_id."""
    # 2Checkout возвращает GET (Header Redirect) или POST с order_number, total, key, merchant_order_id
    order_number = request.GET.get('order_number') or request.POST.get('order_number')
    total = request.GET.get('total') or request.POST.get('total')
    key = request.GET.get('key') or request.POST.get('key')
    merchant_order_id = request.GET.get('merchant_order_id') or request.POST.get('merchant_order_id')

    if not order_number or not key or not merchant_order_id:
        messages.info(request, 'Неверные параметры возврата.')
        return redirect('subscription' + '?payment=fail')

    if not payments.verify_2checkout_return(order_number, total, key, merchant_order_id):
        messages.warning(request, 'Проверка подписи оплаты не пройдена. Попробуйте снова или выберите другой способ.')
        return redirect('subscription' + '?payment=fail')

    try:
        pending = PendingSubscriptionPayment.objects.get(
            id=int(merchant_order_id),
            provider=PendingSubscriptionPayment.PROVIDER_2CHECKOUT,
        )
    except (ValueError, PendingSubscriptionPayment.DoesNotExist):
        messages.warning(request, 'Платёж не найден или уже обработан.')
        return redirect('subscription' + '?payment=fail')

    profile, _ = UserProfile.objects.get_or_create(user=pending.user)
    if pending.plan == 'yearly':
        profile.plan = UserProfile.PLAN_YEARLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=365)
    else:
        profile.plan = UserProfile.PLAN_MONTHLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=30)
    profile.subscription_type = 'PRO'
    profile.save(update_fields=['plan', 'subscription_ends_at', 'subscription_type'])
    pending.delete()
    messages.success(request, 'Оплата прошла успешно. Подписка PRO активирована.')
    return redirect('profile' + '?payment=success')


@csrf_exempt
@require_http_methods(['POST'])
def twocheckout_ipn_view(request):
    """
    Webhook IPN 2Checkout: мгновенная активация подписки после оплаты.
    Ожидает ORDERSTATUS=COMPLETE или PAYMENT_RECEIVED, MESSAGE_TYPE=ORDER_CREATED/APPROVED.
    Идентификатор платежа: IPN_PID[0] или MERCHANT_ORDER_ID (наш pending_id).
    """
    post_data = dict(request.POST.items()) if request.POST else {}
    # Нормализуем: QueryDict может отдавать списки для ключей с []
    data = {}
    for k, v in post_data.items():
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ''
        data[k] = str(v) if v is not None else ''

    order_status = (data.get('ORDERSTATUS') or '').strip().upper()
    if order_status not in ('COMPLETE', 'PAYMENT_RECEIVED', 'PAYMENT_AUTHORIZED'):
        return HttpResponse('skip', status=200)

    merchant_order_id = data.get('MERCHANT_ORDER_ID') or data.get('REFNOEXT')
    if not merchant_order_id and 'IPN_PID[0]' in data:
        merchant_order_id = data['IPN_PID[0]']
    if not merchant_order_id and 'IPN_PID' in data:
        merchant_order_id = data['IPN_PID']
    if not merchant_order_id:
        return HttpResponse('no id', status=400)

    try:
        pending_id = int(merchant_order_id)
    except (TypeError, ValueError):
        return HttpResponse('bad id', status=400)

    signature = data.get('SIGNATURE_SHA2_256') or data.get('SIGNATURE_SHA3_256')
    if signature and payments.verify_2checkout_ipn(data, signature) is False:
        return HttpResponse('bad sign', status=400)

    try:
        pending = PendingSubscriptionPayment.objects.get(
            id=pending_id,
            provider=PendingSubscriptionPayment.PROVIDER_2CHECKOUT,
        )
    except PendingSubscriptionPayment.DoesNotExist:
        return HttpResponse(f'OK{pending_id}', status=200)

    profile, _ = UserProfile.objects.get_or_create(user=pending.user)
    if pending.plan == 'yearly':
        profile.plan = UserProfile.PLAN_YEARLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=365)
    else:
        profile.plan = UserProfile.PLAN_MONTHLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=30)
    profile.subscription_type = 'PRO'
    profile.save(update_fields=['plan', 'subscription_ends_at', 'subscription_type'])
    pending.delete()
    return HttpResponse(f'OK{pending_id}', status=200)


@csrf_exempt
@require_http_methods(['POST'])
def robokassa_result_view(request):
    """Result URL Robokassa: серверный callback, проверка подписи, активация подписки. Ответ: OK<InvId>."""
    out_sum = request.POST.get('OutSum', '')
    inv_id = request.POST.get('InvId', '')
    signature = request.POST.get('SignatureValue', '')

    if not out_sum or not inv_id or not signature:
        return HttpResponse('bad request', status=400)

    if not payments.verify_robokassa_result(out_sum, inv_id, signature):
        return HttpResponse('bad sign', status=400)

    try:
        pending = PendingSubscriptionPayment.objects.get(
            id=int(inv_id),
            provider=PendingSubscriptionPayment.PROVIDER_ROBOKASSA,
        )
    except (ValueError, PendingSubscriptionPayment.DoesNotExist):
        return HttpResponse(f'OK{inv_id}')  # уже обработан

    profile, _ = UserProfile.objects.get_or_create(user=pending.user)
    if pending.plan == 'yearly':
        profile.plan = UserProfile.PLAN_YEARLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=365)
    else:
        profile.plan = UserProfile.PLAN_MONTHLY
        profile.subscription_ends_at = timezone.now() + timedelta(days=30)
    profile.subscription_type = 'PRO'
    profile.save(update_fields=['plan', 'subscription_ends_at', 'subscription_type'])
    pending.delete()
    return HttpResponse(f'OK{inv_id}')


def robokassa_success_view(request):
    """Success URL Robokassa: редирект пользователя после успешной оплаты."""
    inv_id = request.GET.get('InvId', '')
    if inv_id:
        messages.success(request, 'Оплата прошла успешно. Подписка PRO активирована.')
    return redirect('profile' + '?payment=success')


def robokassa_fail_view(request):
    """Fail URL Robokassa: редирект при отмене/ошибке."""
    messages.warning(request, 'Оплата отменена или не завершена. Вы можете попробовать снова.')
    return redirect('subscription' + '?payment=fail')


@login_required
def game_profiles_list(request):
    """Список игровых профилей. FREE — один; PRO — несколько, можно добавить."""
    profiles = get_profiles_for_user(request.user)
    if not profiles:
        get_or_create_default_game_profile(request.user)
        profiles = get_profiles_for_user(request.user)
    can_add = can_add_game_profile(request.user)
    return render(request, 'accounts/game_profiles_list.html', {
        'profiles': profiles,
        'can_add': can_add,
        'is_pro': user_is_pro(request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def game_profile_create(request):
    """PRO: создать новый игровой профиль. FREE — редирект."""
    if not user_is_pro(request.user):
        messages.info(request, 'Несколько профилей доступны по подписке PRO.')
        return redirect('game_profiles_list')
    if not can_add_game_profile(request.user):
        messages.info(request, 'Достигнут лимит профилей.')
        return redirect('game_profiles_list')
    if request.method == 'POST':
        nickname = (request.POST.get('nickname') or '').strip()
        if not nickname:
            messages.error(request, 'Введите никнейм.')
            return redirect('game_profile_create')
        if GameProfile.objects.filter(user=request.user, nickname=nickname).exists():
            messages.error(request, 'Профиль с таким никнеймом уже есть.')
            return redirect('game_profile_create')
        profile = GameProfile.objects.create(user=request.user, nickname=nickname, is_primary=False)
        ProfileStats.objects.get_or_create(game_profile=profile)
        messages.success(request, f'Профиль «{nickname}» создан.')
        return redirect('game_profiles_list')
    return render(request, 'accounts/game_profile_create.html')


@login_required
def game_profile_stats(request, profile_id):
    """Статистика профиля. Базовая — для всех; детальная — только PRO."""
    profile = get_object_or_404(GameProfile, id=profile_id, user=request.user)
    try:
        stats = profile.stats
    except ProfileStats.DoesNotExist:
        stats = None
    return render(request, 'accounts/game_profile_stats.html', {
        'game_profile': profile,
        'stats': stats,
        'show_detailed': user_is_pro(request.user),
    })
