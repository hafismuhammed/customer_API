from django.urls import path, include
from customers import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'customer', views.UserManagementAPIView, basename='customer_management')
router.register(r'product', views.ProductAPIView, basename='customer_management')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.LoginAPIView.as_view()),
    path('register/', views.RegisterAPIView.as_view()),
]

