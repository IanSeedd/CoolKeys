from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.apps import apps # Importação necessária para buscar models
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import Group



try:
    # Estas models contêm o seu Jogo, Categoria, Compra e ItemCompra
    Jogo = apps.get_model('app', 'Jogo')
    Compra = apps.get_model('app', 'Compra')
    Categoria = apps.get_model('app', 'Categoria')
    ItemCompra = apps.get_model('app', 'ItemCompra') # Também necessário para o carrinho
    ImagemExtra = apps.get_model('app', 'ImagemExtra')
except LookupError:
    # Se der erro, definimos como None (o que causará falha controlada nas views)
    Jogo, Compra, Categoria, ItemCompra = None, None, None, None

@login_required
@staff_member_required
def admin_dashboard(request):
    # Verifica se o usuário pertence ao grupo 'adm'
    if not request.user.groups.filter(name='admin_staff').exists():
        return redirect('home')  # Redireciona para home se não for admin
    
    # Validação de segurança se as models não foram encontradas
    if not all([Jogo, Compra, User]):
        messages.error(request, "Erro de configuração: Modelos de dados não encontrados.")
        return redirect('home')
    
    # Estatísticas básicas
    jogos = Jogo.objects.all()
    total_compras = Compra.objects.filter(status='finalizada').count()
    total_jogos = Jogo.objects.filter(deletado=False).count()
    total_users = User.objects.count()
    compras_recentes = Compra.objects.filter(status='finalizada').order_by('-data_compra')[:5]
    
    context = {
        'jogos': jogos,
        'user': request.user,
        'total_compras': total_compras,
        'total_jogos': total_jogos,
        'total_users': total_users,
        'compras_recentes': compras_recentes,
    }
    
    return render(request, 'dashboard.html', context)
@login_required
@staff_member_required
def criar_jogo_view(request):
    # Verificação de grupo (conforme seu código original)
    if not request.user.groups.filter(name='admin_staff').exists():
        return redirect('home')


    if request.method == 'POST':
        # 1. Captura de dados simples do formulário
        nome = request.POST.get('nome')
        preco = request.POST.get('preco')
        descricao = request.POST.get('descricao')
        autoria = request.POST.get('autoria', 'CoolKeys')
        lancamento = request.POST.get('lancamento')
        desconto = request.POST.get('desconto', 0)
        
        # 2. Captura de booleanos (switches)
        banner = request.POST.get('banner') == 'on'
        pre_lancamento = request.POST.get('pre_lancamento') == 'on'
        deletado = request.POST.get('deletado') == 'on'

        # 3. Captura de Arquivos
        icone = request.FILES.get('icone')
        imagens_extras = request.FILES.getlist('imagens_extras')

        # 4. Captura de categorias (M2M)
        categoria_ids = request.POST.getlist('categoria')

        try:
            # Usamos transação atômica para garantir que o jogo só seja criado se tudo der certo
            with transaction.atomic():
                # Criação do Objeto Jogo
                novo_jogo = Jogo.objects.create(
                    nome=nome,
                    preco=preco,
                    descricao=descricao,
                    banner=banner,
                    pre_lancamento=pre_lancamento,
                    deletado=deletado,
                    autoria=autoria,
                    lancamento=lancamento,
                    desconto=desconto,
                    icone=icone,
                )

                # Salva as categorias (ManyToManyField)
                if categoria_ids:
                    novo_jogo.categoria.set(categoria_ids)

                # Salva a Galeria (ImagemExtra)
                for i, img in enumerate(imagens_extras):
                    ImagemExtra.objects.create(
                        jogo=novo_jogo,
                        imagem=img,
                        ordem=i + 1
                    )

            messages.success(request, f"O jogo '{nome}' foi criado com sucesso!")
            # Redireciona para o nome da URL do dashboard
            return redirect('dashboard_admin') 

        except Exception as e:
            messages.error(request, f"Erro ao criar jogo: {e}")

    return render(request, 'criar_jogo.html')
# Editar jogo
@staff_member_required
def editar_jogo(request, jogo_id):
    jogo = get_object_or_404(Jogo, id=jogo_id)
    
    if not request.user.groups.filter(name='admin_staff').exists():
        return redirect('home')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                jogo.nome = request.POST.get('nome')
                jogo.preco = request.POST.get('preco')
                jogo.descricao = request.POST.get('descricao')
                jogo.autoria = request.POST.get('autoria', 'CoolKeys')
                jogo.lancamento = request.POST.get('lancamento')
                jogo.desconto = request.POST.get('desconto', 0)
                jogo.banner = request.POST.get('banner') == 'on'
                jogo.pre_lancamento = request.POST.get('pre_lancamento') == 'on'
                jogo.deletado = request.POST.get('deletado') == 'on'

                if request.FILES.get('icone'):
                    jogo.icone = request.FILES.get('icone')

                jogo.save()
                jogo.categoria.set(request.POST.getlist('categoria'))

                for img in request.FILES.getlist('imagens_extras'):
                    ImagemExtra.objects.create(jogo=jogo, imagem=img)

            messages.success(request, f"Jogo '{jogo.nome}' atualizado!")
            return redirect('dashboard_admin')
        except Exception as e:
            messages.error(request, f"Erro: {e}")

    # Correção no render: Passando tudo num único dicionário de contexto
    return render(request, 'editar_jogo.html', {
        'jogo': jogo,
        'categorias': Categoria.objects.all(),
    })
@staff_member_required
def gerenciar_categorias(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        if nome:
            Categoria.objects.create(nome=nome, descricao=descricao)
            messages.success(request, "Categoria criada com sucesso!")
        else:
            messages.error(request, "O nome da categoria é obrigatório.")
        return redirect('gerenciar_categorias')

    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'categorias.html', {'categorias': categorias})
@staff_member_required
def gerenciar_categorias(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        if nome:
            Categoria.objects.create(nome=nome, descricao=descricao)
            messages.success(request, "Categoria criada com sucesso!")
        else:
            messages.error(request, "O nome da categoria é obrigatório.")
        return redirect('gerenciar_categorias')

    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'categorias.html', {'categorias': categorias})

@staff_member_required
def editar_categoria(request, cat_id):
    if request.method == 'POST':
        cat = get_object_or_404(Categoria, id=cat_id)
        cat.nome = request.POST.get('nome')
        cat.descricao = request.POST.get('descricao')
        cat.save()
    return redirect('gerenciar_categorias')

@staff_member_required
def deletar_categoria(request, cat_id):
    cat = get_object_or_404(Categoria, id=cat_id)
    cat.delete()
    return redirect('gerenciar_categorias')

@staff_member_required
def gerenciar_usuarios(request):
    # Verifica se o usuário logado pertence ao grupo admin_staff
    if not request.user.groups.filter(name='admin_staff').exists():
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    
    usuarios = User.objects.all().order_by('-date_joined')
    return render(request, 'usuarios.html', {'usuarios_lista': usuarios})

@staff_member_required
def alterar_grupo_usuario(request, user_id):
    if request.method == 'POST':
        usuario_alvo = get_object_or_404(User, id=user_id)
        grupo_nome = request.POST.get('grupo')
        
        # Garante que o grupo 'admin_staff' existe no banco
        grupo_admin, created = Group.objects.get_or_create(name='admin_staff')

        if grupo_nome == 'admin_staff':
            usuario_alvo.groups.add(grupo_admin)
            usuario_alvo.is_staff = True # Necessário para acessar o painel
            messages.success(request, f"{usuario_alvo.username} agora é Staff.")
        else:
            usuario_alvo.groups.remove(grupo_admin)
            usuario_alvo.is_staff = False
            messages.warning(request, f"{usuario_alvo.username} removido do Staff.")
        
        usuario_alvo.save()
        
    return redirect('gerenciar_usuarios')
@staff_member_required
@staff_member_required
def deletar_usuario(request, user_id):
    if not request.user.groups.filter(name='admin_staff').exists():
        return redirect('dashboard')
    
    usuario = get_object_or_404(User, id=user_id)
    # Impede que você delete a si próprio
    if request.user.id != usuario.id:
        usuario.delete()
        messages.success(request, "Usuário removido com sucesso.")
    else:
        messages.error(request, "Você não pode remover sua própria conta.")
        
    return redirect('gerenciar_usuarios')