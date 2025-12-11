from django.db import models

# Create your models here.

class Jogo(models.Model):
    nome = models.CharField(max_length=200) 
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    descricao = models.TextField()
    icone = models.ImageField(
        upload_to='icones/'
        # Por padrão, null=False e blank=False.
        # Você pode ser explícito, se preferir:
    )
    
    def __str__(self):
        return self.nome
