# Banco de Dados em Detalhes

## Arquitetura Principal
O sistema utiliza **SQLite3** local, modelado sob o ORM (Object-Relational Mapping) do Django. O banco foi estruturado focado em alto desempenho e na integridade total dos dados.

## Segurança e Zero-Trust
O diferencial do banco de dados deste sistema é a tabela de **LogAuditoria**.
Foi implementada uma arquitetura "Zero-Trust" baseada em Blockchain. Toda ação crítica de inserção, modificação ou exclusão nos registros (Membros, Escalas, Estoque, etc) gera um log imutável.
- **Hash Chain**: Cada registro no `LogAuditoria` é assinado com SHA-256. O `hash_atual` é gerado concatenando os dados do evento + o `hash_anterior`. Se um dado histórico for adulterado diretamente no banco, toda a corrente criptográfica se quebra, alertando o SysAdmin.

## Modelagem Relacional (Schemas Principais)

1. **Autenticação (Membro)**
   - Extensão nativa do `AbstractUser` do Django. 
   - Contém o controle de cargo (`NIVEL_CHOICES`: Super Admin, Lider, Voluntário, etc), foto de perfil, bloqueios de segurança e vínculo multi-departamental.

2. **Gestão Estrutural**
   - **Departamento / Função**: Tabelas unidas para gerir Ministérios (Ex: Louvor, Mídia, Kids) e suas respectivas funções (Ex: Baterista, Câmera, Professor).

3. **Escalas**
   - **CompetenciaEscala**: O "Cabeçalho" do mês (ex: Maio 2026), ligada a um departamento e mantendo o PDF consolidado em anexo.
   - **Escala (Slots)**: Relacionamento cruzado conectando `Membro` <-> `Função` <-> `Competencia`, armazenando horários, datas e tipo de culto.

4. **Almoxarifado**
   - **ItemEstoque / LoteAlimento**: Separa itens gerais de alimentos perecíveis (com controle de validade e lotes).
   - **TransacaoEstoque / EmprestimoEquipamento**: Auditoria rastreável para itens que entram, saem ou são emprestados, com vinculação direta a quem retirou.

5. **Mídia e LGPD**
   - **DocumentoMembro**: Sistema de cofre virtual conectando o `Membro` a arquivos físicos (PDF, JPG) gerados, armazenando chaves de acesso únicas (`token_acesso`) para links dinâmicos de assinatura.
