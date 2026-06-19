# Correções Críticas nos Módulos BI e LGPD

**Data:** 19/06/2026
**Módulos Afetados:** `core/views.py` (BI) e `midia_lgpd/views.py` (LGPD)

## 1. Módulo LGPD & PV Drive
Foi identificado que o uso da classe `PermissaoPVDrive` para gerar links de compartilhamento avançados estava quebrando com um `NameError` interno. Isso ocorria porque a classe existia e era estruturalmente correta no banco de dados (`midia_lgpd.models`), porém **não havia sido importada** no topo de `midia_lgpd/views.py`.
- **Correção:** A importação `from .models import ..., PermissaoPVDrive` foi adicionada na linha 18.

## 2. Módulo de Relatórios (B.I.)
Devido à evolução arquitetural dos outros módulos (como Patrimônio, Casais e Visitantes), as views de BI em `core/views.py` (especificamente `bi_data_async`) continuavam apontando para campos e modelos fantasmas que haviam sido refatorados, resultando em múltiplos erros 500 no carregamento via HTMX:
- **Almoxarifado:** O campo `valor_estimado` foi corrigido para `valor_monetario`.
- **Almoxarifado (Painel Depreciação):** O campo `data_aquisicao` foi corrigido para `data_entrada`.
- **Almoxarifado (Índice de Retenção):** O campo de tracking das retiradas foi re-escrito. Em vez de usar `devolvido` e `membro_solicitante`, a lógica foi adaptada para `tipo='retirada'` e agrupada pelo membro do empréstimo (`membro_vinculado__first_name`), evitando dependências circulares.
- **Família & Casais:** O antigo modelo `MatriculaCurso` foi atualizado para referenciar o modelo correto `MatriculaCursoCasal`. As tags de status também foram atualizadas para refletir as novas escolhas do sistema (`status_matricula='Aprovado'` e `'Desistente'`).
- **Integração & CRM:** O campo de localidade `bairro` havia sido suprimido da entidade Visitante. Para o gráfico geográfico, passamos a usar as amostras do campo descritivo livre `endereco`.

A auditoria unitária simulando os endpoints (via RequestFactory + Super Admin) provou que 100% dos relatórios agora operam de forma isolada, gerando seus DataFrames e alimentando o Cérebro I.A perfeitamente.
