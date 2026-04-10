from django.urls import path, include
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profiles/', views.game_profiles_list, name='game_profiles_list'),
    path('profiles/create/', views.game_profile_create, name='game_profile_create'),
    path('profiles/<int:profile_id>/stats/', views.game_profile_stats, name='game_profile_stats'),
    path('subscription/', views.subscription_view, name='subscription'),
    path('subscription/checkout/', views.subscription_checkout_view, name='subscription_checkout'),
    path('subscription/success/', views.subscription_success_view, name='subscription_success'),
    path('payment/2checkout/ipn/', views.twocheckout_ipn_view, name='twocheckout_ipn'),
    path('payment/robokassa/result/', views.robokassa_result_view, name='robokassa_result'),
    path('payment/robokassa/success/', views.robokassa_success_view, name='robokassa_success'),
    path('payment/robokassa/fail/', views.robokassa_fail_view, name='robokassa_fail'),
    path('register/', RedirectView.as_view(pattern_name='account_signup', permanent=False), name='register'),
    path('', include('allauth.urls')),
]
