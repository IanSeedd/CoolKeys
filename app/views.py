from django.shortcuts import render, get_object_or_404, redirect
from .models import *  # 1. Importar
from django.contrib.auth.forms import UserCreationForm #formulário de criação de usuário
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group # <-- Importação para cadastro usuario do grupo Cliente

def home_view(request):
    # 1. Jogos do Banner Principal (Carrossel do topo)
    banner_games = Jogo.objects.filter(banner=True, deletado=False)
    
    # 2. Jogo do Banner Secundário (O roxo de Pré-Venda)
    # AQUI ESTÁ A MUDANÇA: Busca APENAS um jogo da categoria 'pre_lancamento'
    # Se não tiver nenhum jogo nessa categoria, a variável será None e o banner não aparecerá no HTML.
    destaque_secundario = Jogo.objects.filter(pre_lancamento=True, deletado=False).last()

    context = {
        'categorias': Categoria.objects.all(),
        'banner_games': banner_games,
        'destaque_secundario': destaque_secundario, # Se for None, o {% if %} do HTML esconde o banner
    }
    
    return render(request, 'home.html', context)


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



# CARRINHO FUNÇÕES
@login_required
def adicionar_carrinho(request, jogo_id):
    try:
        # 1. Encontra o jogo
        jogo = Jogo.objects.get(id=jogo_id)
        
        # 2. Pega ou cria carrinho (simplificado)
        carrinho, created = Compra.objects.get_or_create( #created verifica se já existe um carrinho
            usuario=request.user,
            status='pendente',
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
    return redirect('home')
@login_required
def remover_carrinho(request, item_id):
    # Verifica também se o item pertence a um carrinho do usuário atual (segurança)
    item = get_object_or_404(ItemCompra, id=item_id, compra__usuario=request.user)
    
    # Pega o carrinho antes de deletar o item para poder atualizar o total depois
    carrinho = item.compra
    
    # Deleta o item
    if item.quantidade > 1:
        item.quantidade -= 1
        item.save()
    else:
        item.delete()
    
    # Recalcula o valor total do carrinho
    # (Soma os subtotais dos itens restantes)
    carrinho.valor_total = sum(i.subtotal() for i in carrinho.itens.all())
    carrinho.save()
    return redirect('carrinho')
# CARRINHO VIEW
@login_required(login_url='login')
def carrinho_view(request):
    # Busca o carrinho ativo (status='pendente')
    carrinho = Compra.objects.filter(usuario=request.user, status='pendente').first()

    # Se não existir carrinho, cria um vazio
    if not carrinho:
        carrinho = Compra.objects.create(usuario=request.user, status='pendente', valor_total=0)
    else:
        # Se já existe, não faz nada, apenas atualiza os itens
        carrinho.limpar_jogos_deletados()
        carrinho.atualizar_total()

    # Pega todos os itens do carrinho
    itens_carrinho = carrinho.itens.all()
    # Preço antes dos descontos
    subtotal_sem_desconto = 0
    for item in itens_carrinho:
        if item.jogo:
            # Preço original do jogo × quantidade
            subtotal_sem_desconto += float(item.jogo.preco) * item.quantidade
        else:
            # Usa preco_unitario salvo
            subtotal_sem_desconto += float(item.preco_unitario or 0) * item.quantidade

    valor_descontado = 0  # Valor do desconto (porcentagem aplicada ao preço )
    
    for item in itens_carrinho:
        if item.jogo:
            # Desconto (convertendo Decimal para float)
            desconto_unidade = float(item.jogo.valor_desconto)
            valor_descontado += desconto_unidade * item.quantidade
    
    # Calcula total
    total = carrinho.valor_total

    context = {
        'carrinho': carrinho,
        'itens': itens_carrinho,
        'total': total,
        'subtotal_sem_desconto': subtotal_sem_desconto,
        'valor_descontado': valor_descontado,
    }
    return render(request, 'carrinho.html', context)
# Finalizar compra
def finalizar_compra_view(request): 
    # Apenas processa a requisição se for um POST (enviado pelo formulário)
    if request.method == 'POST':
        try:
            # 1. Busca a compra mais recente do usuário que ainda não está finalizada.
            # Assumimos que o status inicial de um carrinho é 'aberta'.
            carrinho = Compra.objects.filter(
                usuario=request.user,
                status='pendente'
            ).order_by('-data_compra').first()
            
            if carrinho:
                # 2. Atualiza o status para 'finalizada'
                carrinho.status = 'finalizada'
                carrinho.save()
                for item in carrinho.itens.all():
                    # Garante o snapshot após o salvamento
                    item.save()
                
                # 3. Redireciona o usuário (ex: para a página de perfil ou confirmação)
                return redirect('perfil') 
            else:
                # Se não houver carrinho aberto, apenas redireciona de volta
                return redirect('carrinho')
                
        except Exception as e:
            # Trata qualquer erro (como se o modelo Compra não existisse)
            print(f"Erro ao finalizar a compra: {e}")
            return redirect('carrinho')
            
    # Se a função for acessada via GET (diretamente pela URL), redireciona
    return redirect('carrinho')


# 
def detalhe_categoria_view(request, id):
    # Pega a categoria atual (ex: RPG)
    categoria = get_object_or_404(Categoria, id=id)
    
    # Pega os jogos dessa categoria
    jogos = categoria.jogos.filter(deletado=False)
    
    # Pegamos TODAS as categorias para o menu do topo funcionar
    todas_categorias = Categoria.objects.all()
    
    return render(request, 'categoria_detalhe.html', {
        'categoria': categoria,
        'jogos': jogos,
        'categorias': todas_categorias  # Enviamos para o HTML aqui com o nome que o base.html espera
    })

def jogo_detalhe_view(request, id):
    jogo = get_object_or_404(Jogo, id=id)
    
    # Adicionei .order_by('?') para deixar aleatório
    jogos_relacionados = Jogo.objects.filter(
        categoria=jogo.categoria,
        deletado=False
    ).exclude(
        id=id
    ).order_by('?')[:4] 
    
    # Categorias para o menu
    todas_categorias = Categoria.objects.all()

    return render(request, 'jogo_detalhe.html', {
        'jogo': jogo,
        'jogos_relacionados': jogos_relacionados,
        'categorias': todas_categorias
    })

@login_required
def perfil_view(request): 
    # --- LÓGICA DE UPLOAD DE FOTO ---
    if request.method == 'POST' and request.FILES.get('foto_perfil'):
        foto = request.FILES['foto_perfil']
        
        # Pega ou cria o perfil de foto do usuário
        perfil_foto, created = FotoPerfil.objects.get_or_create(usuario=request.user)
        
        # Atualiza a foto
        perfil_foto.foto_perfil = foto
        perfil_foto.save()
        
        # Recarrega a página para mostrar a foto nova
        return redirect('perfil')

    # --- LÓGICA NORMAL DE EXIBIÇÃO ---
    compras_finalizadas = Compra.objects.filter(
        usuario=request.user,
        status='finalizada'
    ).order_by('-data_compra')

    # Sempre pega ou cria o FotoPerfil (já que tem default)
    foto_perfil, created = FotoPerfil.objects.get_or_create(usuario=request.user)

    return render(request, 'perfil.html', {
        'compras_finalizadas': compras_finalizadas,
        'foto_perfil': foto_perfil,
    })

# Pagina de ADM
@login_required
def dashboard_admin_view(request):
    # Verifica se o usuário pertence ao grupo 'adm'
    if not request.user.groups.filter(name='adm').exists():
        return redirect('home')  # Redireciona para home se não for admin
    
    # Estatísticas básicas
    total_compras = Compra.objects.filter(status='finalizada').count()
    total_jogos = Jogo.objects.filter(deletado=False).count()
    compras_recentes = Compra.objects.all().order_by('-data_compra')[:5]
    
    context = {
        'user': request.user,
        'total_compras': total_compras,
        'total_jogos': total_jogos,
        'compras_recentes': compras_recentes,
    }
    
    return render(request, 'admin/dashboard.html', context)

