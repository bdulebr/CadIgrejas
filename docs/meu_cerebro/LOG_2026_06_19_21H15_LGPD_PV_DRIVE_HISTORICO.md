# Integração LGPD com Histórico Lógico e PV Drive Automático

**Data:** 19/06/2026
**Objetivo:** Atender as regras de compliance absolutas: Trilha de Auditoria com Histórico JSON para re-aceites/rejeições e salvamento automático em Nuvem PV Drive.

## Modificações Realizadas

### 1. Histórico de Auditoria Lógica (`RegistroAceiteLGPD`)
- O campo `historico_alteracoes = models.JSONField()` foi adicionado ao banco de dados.
- Toda vez que uma pessoa entra no link mágico e clica em **Aceitar** ou **Recusar**, o sistema agora anexa no JSON o log imutável contendo:
  - `data`
  - `acao`
  - `ip`
  - `user_agent`
- O status principal é subscrito para refletir a última decisão, mas o passado jamais é apagado.

### 2. Geração de PDF e 2ª Via por E-mail (Inclusive Recusas)
- Agora, até mesmo quando o membro ou visitante diz **"NÃO ACEITO"**, o sistema gera o PDF oficial carimbado com o IP, declarando em vermelho "TERMO RECUSADO PELO TITULAR".
- Imediatamente, esse PDF é disparado via e-mail para a pessoa, garantindo a segunda via legal do documento assinado (seja positivo ou negativo).

### 3. Integração Profunda com PV Drive
Todo documento PDF gerado pelo LGPD agora é injetado silenciosamente no ecossistema de arquivos da Intranet:
- **Visitantes e Crianças:** O sistema busca automaticamente o Departamento "Mídia & LGPD". Dentro da raiz dele, cria uma subpasta exclusiva com o Nome Completo do Visitante e deposita o `ArquivoMidia` lá dentro.
- **Membros / Voluntários Oficiais:** O sistema pula a pasta do departamento e vai direto na "Raiz Pessoal" desse membro (a PastaVirtual de `tipo_pasta='usuario'`) e deposita o documento lá para fácil acesso vitalício do membro aos seus próprios contratos da igreja.

### 4. Regras Globais do Agente
- Atualizamos as regras base do arquivo de Agentes (`AGENTS.md`) estipulando que:
  > Toda ação de LGPD agora é vinculada ao Histórico JSON e salva no PV Drive. O Agente jamais deve desenhar novas features do LGPD sem PV Drive.
