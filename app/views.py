from django.shortcuts import render, get_object_or_404, redirect
from .models import *  # 1. Importar
from django.contrib.auth.forms import UserCreationForm #formulário de criação de usuário
from django.contrib.auth import login
from django.contrib.auth.models import Group # <-- Importação para cadastro usuario do grupo Cliente

def home_view(request):
    return render(
        request,
        'home.html',
        {'jogos': Jogo.objects.all}
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

