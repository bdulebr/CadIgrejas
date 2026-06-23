# Refatoração do Painel do Líder e Integração Escalas/Vagas

## Data: 23/06/2026

## O que foi feito?
A view `painel_lider` foi profundamente reformulada para focar na operação diária e gestão de pessoas (UI em abas), mantendo total integração com o "Gerenciador de Escala" e com as recém-criadas "Vagas" e "Eventos Internos".

## 1. Gerenciador de Escalas e Analytics
A view original do Painel do Líder trazia os "Próximos Cultos" e "Rascunhos". Tudo isso foi mantido e integrado na Aba "Visão Geral" e "Caixa de Entrada".
Foi introduzido um painel de **Analytics**:
- **Taxa de Assiduidade**: Calculada filtrando as últimas 100 escalas do departamento e gerando a porcentagem de `status='presente' / ('presente' + 'substituido' + 'falta_justificada' + 'confirmado')`. (Nota: O status `confirmado` numa escala com data no passado significa que não houve check-in).
- **Alerta de Faltas**: Conta se membros faltaram (status "confirmado" em escalas passadas) nos últimos 30 dias.

## 2. Vagas e Ensaios
Aproveitando os Models introduzidos anteriormente em `gestao_membros/models.py`:
- `VagaSetor` e `CandidaturaVaga`:
- `EventoInternoSetor`:
Estes models foram injetados no contexto via `prefetch_related('vagas_abertas__candidaturas', 'eventos_internos')` na query `Departamento.objects.get` da view `painel_lider`.

## 3. UI/UX
Utilizado `Alpine.js` (`x-data="{ activeTab: 'visao' }"`) na template `painel_lider.html` para particionar em:
- Aba 1: Visão Geral (Analytics, Eventos Oficiais, Ensaios, Mural, Ausências confirmadas de 30 dias).
- Aba 2: Minha Equipe (Lista de membros, modal de configuração de nível, atalhos de anotação de feedback e atestado de indisponibilidade).
- Aba 3: Caixa de Entrada (Pedidos de Entrada no setor via código fixo, Candidaturas pendentes e Rascunhos de escala prontos para publicar).

## 4. Otimização de Performance
Forte uso de `prefetch_related` e `select_related` nas chamadas ao Model `Departamento`, a fim de evitar loops N+1 ao popular listagens de membros, vagas e eventos no frontend.

## Observações LGPD e Cérebro
Nenhuma alteração afeta a LGPD, os logs de aceite no PV Drive permanecem inalterados e gerenciados pelos módulos respectivos (PV Drive / Mídia & LGPD). As anotações de liderança (`anotacoes_lideranca`) no Membro continuam restritas e não são exibidas fora do nível adequado.
