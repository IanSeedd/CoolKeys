from django.urls import path
from . import views 
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('categoria/<int:id>/', views.detalhe_categoria_view, name='detalhe_categoria'),
    path('add/<int:jogo_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('remove/<int:item_id>/', views.remover_carrinho, name='remover_carrinho'), 
    path('carrinho/finalizar/', views.finalizar_compra_view, name='finalizar_compra'),
    path('carrinho/', views.carrinho_view, name='carrinho'),
    path('jogo/detalhe/<int:id>/', views.jogo_detalhe_view, name='jogo_detalhe'),
    path('control/painel/', views.dashboard_admin_view, name='dashboard_admin'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
]
