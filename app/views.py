from django.shortcuts import render, get_object_or_404, redirect
from .models import *  # 1. Importar
from django.contrib.auth.forms import UserCreationForm #formulário de criação de usuário
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group # <-- Importação para cadastro usuario do grupo Cliente

def home_view(request):
    context = {
        'jogo': Jogo.objects.all,
        'categorias': Categoria.objects.all
    }
    return render(
        request,
        'home.html',
        context
    )

def cadastro_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # --- LÓGICA DE GRUPO ---
            # Pega o grupo "Client". 
            grupo_client = Group.objects.get(name='Client')
            user.groups.add(grupo_client)

            # Login automático
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm() # Se a informação for inválida
    
    return render(request,'registration/cadastro.html',{'form': form})

@login_required
def adicionar_carrinho(request, jogo_id):
    """View SIMPLES que funciona"""
    try:
        # 1. Encontra o jogo
        jogo = Jogo.objects.get(id=jogo_id)
        
        # 2. Pega ou cria carrinho (simplificado)
        carrinho, created = Compra.objects.get_or_create( #created verifica se já existe um carrinho
            usuario=request.user,
            status='carrinho',
            defaults={'valor_total': 0}
        )
        
        # 3. Adiciona item (simplificado)
        item, item_created = ItemCompra.objects.get_or_create(
            compra=carrinho,
            jogo=jogo,
            defaults={'preco_unitario': jogo.preco, 'quantidade': 1}
        )
        
        if not item_created:
            item.quantidade += 1
            item.save()
        
        # 4. Atualiza total
        total = sum(item.subtotal() for item in carrinho.itens.all())
        carrinho.valor_total = total
        carrinho.save()
        
        print(f"Item adicionado! Carrinho ID: {carrinho.id}, Itens: {carrinho.itens.count()}")
        
    except Exception as e:
        print(f"Erro: {e}")
    
    # 5. REDIRECIONA CORRETAMENTE
    return redirect('/')

def carrinho_view(request):
    #Página para visualizar o carrinho ativo
    # Busca o carrinho ativo (status='carrinho')
    carrinho = Compra.objects.filter(
        usuario=request.user,
        status='carrinho'
    ).first()
    
    # Se não existir carrinho, cria um vazio
    if not carrinho:
        carrinho = Compra.objects.create(
            usuario=request.user,
            status='carrinho',
            valor_total=0
        )
    
    # Pega todos os itens do carrinho
    itens_carrinho = carrinho.itens.all() if carrinho else []
    
    # Calcula total (pode usar o valor_total salvo ou recalcular)
    total = carrinho.valor_total if carrinho else 0
    
    context = {
        'carrinho': carrinho,
        'itens': itens_carrinho,
        'total': total,
    }


    return render(
        request,
        'carrinho.html',
        context
    )