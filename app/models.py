from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome

class Jogo(models.Model):
    nome = models.CharField(max_length=200) 
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    descricao = models.TextField()
    icone = models.ImageField(
        upload_to='icones/'
        # Por padrão, null=False e blank=False.
        # Você pode ser explícito, se preferir:
    )
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL,  # ou models.PROTECT se preferir, se a categoria for deletada os jogos não são
        null=True, 
        blank=True,
        related_name='jogos'  # opcional: para acessar jogos de uma categoria
    )
    
    def __str__(self):
        return self.nome


class Compra(models.Model):
    # Status da compra
    STATUS_CHOICES = [
        ('pendente', 'Pendente'), # Funciona como CARRINHO
        ('aprovado', 'Aprovado'), # Funciona como HISTÓRICO
        ('cancelado', 'Cancelado'),
        ('entregue', 'Entregue'),
    ]
    
    jogos = models.ManyToManyField(Jogo, through='ItemCompra', related_name='compras')  # Adicionado through
    data_compra = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='carrinho'  # Alterado default para 'carrinho'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='minhas_compras',
        verbose_name='Client'
    )
    
    def __str__(self):
        return f"Compra #{self.id} - {self.usuario}"
    
    def atualizar_total(self):
        """Atualiza o valor total baseado nos itens"""
        total = sum(item.subtotal() for item in self.itens.all())
        self.valor_total = total
        self.save()
    
# Seu models.py (ADIÇÃO)

class ItemCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='itens')
    jogo = models.ForeignKey(Jogo, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        unique_together = ['compra', 'jogo']  # Um jogo só pode aparecer uma vez por compra
    
    def subtotal(self):
        return self.preco_unitario * self.quantidade
    
    def __str__(self):
        return f"{self.quantidade}x {self.jogo.nome}"
