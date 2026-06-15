from django import forms
from .models import Lancamento, CategoriaTesouraria, TagTesouraria

class LancamentoForm(forms.ModelForm):
    anexos = forms.FileField(required=False, label="Comprovantes e Documentos (Anexos)")
    tags = forms.ModelMultipleChoiceField(
        queryset=TagTesouraria.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False
    )

    class Meta:
        model = Lancamento
        fields = [
            'tipo', 'valor', 'data_vencimento', 'data_lancamento', 'status', 'categoria',
            'descricao', 'observacoes', 'tags', 'forma_pagamento', 'impostos',
            'is_parcelado', 'numero_parcelas', 'parcela_atual'
        ]
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'data_lancamento': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
        self.fields['anexos'].widget.attrs.update({'multiple': 'multiple'})
