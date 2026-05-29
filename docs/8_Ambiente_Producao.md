# Como Executar o Sistema em Produção

## O que é o Modo de Produção?
Diferente do ambiente de desenvolvimento (`python manage.py runserver`), o ambiente de produção utiliza o servidor **Waitress** e desativa o modo `DEBUG=False` por segurança extrema.

## Iniciando o Servidor
Para ligar o sistema localmente em modo seguro na intranet da igreja, basta dar duplo clique no arquivo:

```bash
run_prod.bat
```

Este script ativa automaticamente o Ambiente Virtual (venv), roda migrações pendentes, coleta os arquivos estáticos de forma otimizada via WhiteNoise e sobe o servidor na porta `8000` (http://localhost:8000).

## Parando o Servidor
Para derrubar a conexão, basta focar na tela preta do terminal do Waitress e pressionar `CTRL+C` simultaneamente.
