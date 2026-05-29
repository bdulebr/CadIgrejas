# Módulos em Detalhes

## 1. Módulo Core (Coração do Sistema)
Responsável por orquestrar todo o ecossistema.
- **Autenticação Avançada**: Recuperação de senha autossuficiente via e-mail dinâmico. Proteção contra Brute Force (bloqueio por 10 tentativas).
- **SysAdmin Dashboard**: Painel de Deus (God Mode). Acesso total às Variáveis de Ambiente (`BASE_URL`, configurações de E-mail, Chave do Gemini), edição nativa de Templates HTML de e-mails, botão de "Reset de Banco de Dados" global (preservando contas de admins) e painel de Inteligência de Negócios (B.I.).
- **Auditoria**: Rastreador invisível e gerador do "Hash Chain".

## 2. Módulo Gestão de Membros
Onde a igreja gerencia seu rebanho humano.
- Controle unificado de dados cadastrais, cargo hierárquico e vínculo em N departamentos simultaneamente.
- Motor de comunicação interna (Broadcast de Avisos), possibilitando que o líder do departamento dispare comunicados em massa para a caixa de e-mail da equipe.

## 3. Módulo Escalas (Ponto Focal)
Projetado para extinguir o caos de planilhas do Excel soltas.
- **Drag & Drop e Editor Visual**: Criação de competências mensais (Ex: Louvor Maio/2026).
- **Prevenção de Burnout**: O sistema bloqueia ou alerta quando um voluntário excede mais de 5 atuações no mês.
- **Exportação Universal**: PDF Generator (ReportLab) que transforma a grade complexa num PDF elegante que é salvo localmente e enviado no e-mail de todos os escalados.
- **Minhas Escalas**: Painel pessoal mobile-friendly para o membro consultar seus dias exatos de servir e a cópia da escala.

## 4. Módulo Mídia & LGPD
Voltado para segurança jurídica e fluxos sem papel.
- Upload de PDF dinâmico e geração de Termos de Consentimento (LGPD) e Cessão de Imagem.
- **Automação de Assinaturas**: Dispara um link único criptografado (`token_acesso`) via WhatsApp/Email. Quando o voluntário clica no celular e aceita os termos digitais, o sistema registra o aceite com timestamp e anexa a prova no cofre (pasta `media/`).

## 5. Módulo Almoxarifado
Controle de estoque, validades e patrimônio.
- **Controle de Equipamentos (Patrimônio)**: Cadastro de câmeras, projetores, etc. Rastreamento de empréstimos com prazos.
- **Alimentos e Vencimento (Cantina/Doações)**: Controle rigoroso com alertas automáticos (visuais) se lotes estiverem estragando. Gestão e salvamento de Notas Fiscais diretamente no banco/pasta media.
