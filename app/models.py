from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
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
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('cancelado', 'Cancelado'),
        ('entregue', 'Entregue'),
    ]
    
    jogos = models.ManyToManyField(Jogo, related_name='compras') #cria relação de muitos-para-muitos logo é possivel uma compra ter muitos jogos e muitos jogos terem muitas compras
    data_compra = models.DateTimeField(auto_now_add=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pendente'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ou User se preferir
        on_delete=models.CASCADE,   # Se usuário for deletado, deleta suas compras
        related_name='minhas_compras',  # user.minhas_compras.all()
        verbose_name='Client'
    )
    
    def __str__(self):
        return self.id