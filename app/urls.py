from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home_view, name='app'),
    path('add/<int:jogo_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
]