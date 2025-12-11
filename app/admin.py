from django.contrib import admin
from .models import *  # 1. Importe o Model que você criou

# Register your models here.
admin.site.register(Jogo)
admin.site.register(Categoria)
admin.site.register(Compra)