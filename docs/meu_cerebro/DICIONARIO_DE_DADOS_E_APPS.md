# Dicionário de Dados e Apps

A Intranet está dividida nos seguintes Módulos de Negócios (Apps do Django). Cada app possui um papel específico e suas próprias tabelas no banco de dados.

## 1. Módulo: `core`
**Responsabilidade:** Infraestrutura base, Autenticação e Segurança Zero-Trust.
**Modelos Principais:**
- `Membro (AbstractUser)`: Tabela de usuários. Possui controle de acesso, dados pessoais, hierarquia (`NIVEL_CHOICES`), vinculação conjugal, filhos e habilidades.
- `LogAuditoria` / `LogImutavel`: Logs imutáveis usando Hash em cadeia (estilo blockchain) para evitar que alterações críticas sejam feitas sem rastreio.
- `ConfiguracaoSistema`: Tabela de configuração global (logo da igreja, envio de e-mails, modo manutenção).
- `AIEngineerLog`: Tabela que registra os reparos automáticos feitos pela Inteligência Artificial no código.

## 2. Módulo: `gestao_membros`
**Responsabilidade:** Estruturação da Igreja em Pastas/Departamentos.
**Modelos Principais:**
- `Departamento`: Equipes, Setores, Ministérios. Pode ter sub-líderes.
- `Funcao` / `Habilidade`: Relaciona quais habilidades são exigidas para certas funções dentro de um departamento.
- `AcaoDisciplinar`: Advertências e Suspensões registradas na ficha do membro.
- `AvisoMural`: Quadro de avisos dinâmico por departamento.

## 3. Módulo: `escalas`
**Responsabilidade:** Geração de Escalas, Check-ins e Prevenção de Conflitos.
**Modelos Principais:**
- `CultoEvento`: Os cultos padrão que ocorrem recorrentemente (Domingos, Quartas).
- `CompetenciaEscala`: Bloco mensal (ex: 06/2026) que guarda as escalas de um departamento.
- `Escala`: Tabela que cruza *Membro + Dia + Horário + Função*. **Possui UniqueConstraint nativa** no banco que impede de salvar a mesma pessoa no mesmo horário em dois lugares (Zero-Trust).

## 4. Módulo: `pdv` (Frente de Caixa e Estoque Rápido)
**Responsabilidade:** Loja da igreja, Cantina e Livraria. Focado em UX de acesso rápido (Touch, sem e-mail/senha).
**Modelos Principais:**
- `Produto`: Preço de custo, venda e códigos NFC-e (impostos).
- `OperadorCaixa` e `Caixa`: O fluxo de trabalho (Abertura com saldo inicial, Fechamento com F10). O login é feito por um PIN de 4 dígitos.
- `Venda` / `ItemVenda`: Transação financeira.
- `MovimentoCaixa`: Entradas (Suprimento) e Saídas (Sangria/Despesas avulsas).

## 5. Módulo: `almoxarifado`
**Responsabilidade:** Controle de Ativos (Câmeras, Microfones) e Itens de Consumo (Alimentos).
**Modelos Principais:**
- `ItemAlmoxarifado`: Cada item recebe um UUID (`ALM-XXXXX`) ou código de barras real. Pode ser Permanente ou de Consumo.
- `MovimentacaoAlmoxarifado`: Retiradas e Devoluções. Requer aprovação para itens sensíveis e possui um Log de assinatura digital na movimentação.

## 6. Módulo: `tesouraria`
**Responsabilidade:** Fluxo de Caixa, Lançamentos Financeiros (Pagar/Receber).
**Modelos Principais:**
- `Lancamento`: Registra a entrada/saída de dinheiro, parcelamentos, impostos e possui um hash em cascata que é salvo no `LogImutavel` de forma que ninguém consiga editar sem ser auditado.
- `CategoriaTesouraria` e `TagTesouraria`: Classificadores financeiros.
- `ConfiguracaoTesouraria`: Configura o envio de relatórios e Excel automatizado para a sede nacional.

## 7. Módulo: `visitantes`
**Responsabilidade:** CRM de Recepção e Acompanhamento Pastoral inicial.
**Modelos Principais:**
- `Visitante`: Pessoas recém-chegadas ou Novos Convertidos.
- `VisitaCulto`: Log das vezes em que o visitante veio (presencial ou na Live).
- `RegistroAcompanhamento`: Diário do líder sobre as ligações/visitas feitas para integrar aquela pessoa à igreja.

## 8. Módulo: `atendimento_pastoral`
**Responsabilidade:** Prontuário Confidencial do Gabinete Pastoral.
**Modelos Principais:**
- `PessoaAtendimento`: Perfil isolado da tabela de `Membros` para garantir sigilo sobre não-membros também.
- `AgendamentoPastoral`: Horários da agenda do pastor.
- `SessaoAtendimento`: Prontuário médico-pastoral. Possui Nível de Crise (1 a 5) e integração com Gemini IA, que emite uma "Análise Comportamental Inteligente". Essa tabela pode ter RLS (Row-Level Security) ativo que barra até o SuperAdmin de ler.

## 9. Módulo: `ministerio_casais`
**Responsabilidade:** Turmas, Aconselhamento conjugal, Trilhas e Gamificação.
**Modelos Principais:**
- `Casal`: Agrupa dois membros/pessoas. Controla a etapa da "Trilha de Noivos".
- `TurmaCurso`, `MatriculaCursoCasal`, `AulaTurma`: Sistema LMS/EAD interno (Diário de Classe, Notas, Entregas, Frequência Mínima, Limite de Faltas).
- `HistoricoAconselhamentoCasal`: Registro de sessões conjugais.

## 10. Módulo: `midia_lgpd`
**Responsabilidade:** Sistema de Arquivos em Nuvem (PV Drive) e Conformidade Legal.
**Modelos Principais:**
- `TermoLGPD` / `AssinaturaLGPD`: Termos de uso de imagem dinâmicos, que barram o usuário até que sejam assinados e registra o IP na assinatura.
- `PastaVirtual` / `ArquivoMidia`: Cria o ecossistema "Google Drive" local. Suporta aninhamento infinito (Parent) e Permissões modulares (`PermissaoPVDrive`).

## 11. Módulo: `permissoes`
**Responsabilidade:** RBAC (Role-Based Access Control) Dinâmico e Desacoplado.
**Modelos Principais:**
- `ModuloSistema`: Ex (`slug='tesouraria'`).
- `PerfilAcesso`: Perfis gerais.
- `PermissaoMembro` / `PermissaoDepartamento`: Permissões granulares contendo CRUD, Ações Customizadas via JSON e Escopo de Dados (Global, Departamento ou Próprio).
