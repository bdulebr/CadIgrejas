# Reestruturação do Módulo Mídia & LGPD

**Data:** 19/06/2026
**Objetivo:** Transformar o antigo módulo de "Mídia e LGPD" (que estava pausado) em um **Centro de Compliance Jurídico** da Igreja, desvinculando-o totalmente do PV Drive e blindando a instituição quanto à Lei 13.709/2018.

## O que foi feito?

1. **Novos Modelos de Dados (`midia_lgpd.models.py`)**
   - Criação da entidade principal `RegistroAceiteLGPD` para rastrear qualquer pessoa que dê um aceite de imagem (Membro, Criança ou Visitante).
   - O campo `tipo` foi adicionado à tabela `TermoLGPD` para segmentar três termos padrão: Membro/Voluntário, Visitante Geral e Criança/Menor de Idade.
   - Foram inseridos textos jurídicos rigorosos de consentimento para esses três perfis usando o script `seed_lgpd.py`.

2. **Novas Abas e Dashboard (`midia_lgpd/views.py`)**
   - **Dashboard Principal (`/lgpd/painel/`)**: Mostra métricas de Aceites e Pendências (somando os membros da Intranet e solicitações manuais).
   - **Envio Rápido (`/lgpd/enviar-solicitacao/`)**: Aba para a equipe de mídia digitar os dados de uma pessoa na porta do evento (Nome, CPF e email opcional) e gerar imediatamente um "Link Mágico" que pode ser compartilhado via WhatsApp.
   - **Histórico**: Tabela com todos os registros, status (Aceito, Recusado, Pendente) e botão para baixar o comprovante legal em PDF.

3. **Geração de PDF com Valor Probatório**
   - Quando o visitante ou membro clica em "SIM, EU ACEITO", a view `processar_aceite_lgpd` gera automaticamente um documento PDF contendo o texto legal, carimbo de tempo, IP de registro e User-Agent.
   - Usado a biblioteca nativa `xhtml2pdf` para montar um documento A4 assinado.

4. **Intranet e Permissões Integradas**
   - Corrigido o decorador de permissão do módulo, que agora exige `@requer_permissao('midia', ...)` para validar contra a tabela `ModuloSistema` oficial.
   - O botão do Sidebar só aparece se o usuário for superusuário ou líder responsável pelo Ministério da Mídia (filosofia *Zero-Trust*).
   - A página de aceite interno dos usuários logados (`ler_assinar_termo`) agora aponta diretamente para a engine `RegistroAceiteLGPD`, integrando as estatísticas e garantindo a geração de PDF para membros logados!

## Conclusões
O sistema está 100% blindado para coletas de termos. Todas as alterações foram commitadas no repositório `main`.
