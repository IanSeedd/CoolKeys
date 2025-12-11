from django import forms
from .models import *

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['jogo', 'quantidade']  # Removemos usuário e valor_total
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantidade'].widget = forms.HiddenInput()  # Esconde quantidade se for sempre 1
        self.fields['quantidade'].initial = 1