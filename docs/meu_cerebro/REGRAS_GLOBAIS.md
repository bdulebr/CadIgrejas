# CÉREBRO DA IA - REGRAS GLOBAIS E DIRETRIZES DO PROJETO

ESTE DOCUMENTO É A FONTE DE VERDADE ABSOLUTA. DEVE SER CONSULTADO ANTES DE QUALQUER NOVA IMPLEMENTAÇÃO.

## 1. REGRAS DE GIT E VERSIONAMENTO (OBRIGATÓRIO)
- **REGRA DE OURO:** A cada final de edição, adição ou exclusão de código, é **OBRIGATÓRIO** subir para o Git de forma automática.
- Comandos padrão: `git add .`, `git commit -m "feat/fix: descrição"`, `git push origin main`.
- Arquivos pesados (ex: `*.apk`, maiores que 100MB) devem estar explicitamente no `.gitignore` para não quebrar o push no Github.

## 2. REGRAS DE MEMÓRIA E RELATÓRIOS (MEU CÉREBRO)
- **REGRA DE OURO:** Toda sessão de trabalho finalizada **DEVE** gerar um arquivo de log detalhado dentro de `DOCS/meu_cerebro/` com o formato de nome: `LOG_YYYY_MM_DD_HHhMM.md`.
- O relatório deve conter tudo que foi feito, decisões de design, arquivos alterados e pendências. Nunca confiar apenas no histórico do chat.

## 3. DIRETRIZES DE DESIGN, CORES E UI/UX
- **Sistema de Cores Psicológico:**
  - **Módulos de Gestão Corporativa/Tech** (Dashboard Geral, Almoxarifado, PDV): Tons de **Azul** e **Cinza** (segurança, sobriedade).
  - **Módulos de Liderança e Organização** (Escalas, Criação de Equipes): Tons de **Amarelo** (atenção, dinamismo).
  - **Módulos de Relacionamento e Cuidado** (CRM de Visitantes e Membros): Tons de **Rosa e Roxo** (acolhimento, calor humano, amor, vida).
- **Logotipos e Identidade:** **NUNCA** usar a logo estática (`logo.jpg`) hardcoded em templates de e-mail ou PDF se puder ser evitado. Sempre utilizar a logo dinâmica vinda do banco de dados (`ConfiguracaoSistema.igreja_logo`).
- **Horários:** Os e-mails e templates devem respeitar fielmente a agenda de horários informada (Domingo da Família, Santa Ceia, Segunda de Oração, Terça Pastoral, Quarta Profética, Quinta do Saber).

## 4. ARQUITETURA, SEGURANÇA E ZERO-TRUST
- **Departamentos de Sistema (Is_System):** Departamentos vitais como `Almoxarifado`, `CRM / Integração`, `Sysadmin`, e `Escalas` possuem proteção Zero-Trust. Eles **NUNCA** podem ser deletados via painel ou banco.
- **Motor de Auto-Healing (`bootstrap_sistema.py`):** Ao iniciar o servidor, o sistema faz verificações de integridade de pastas, banco de dados e sincronia com o GitHub. Alterações críticas devem prever que o Auto-Healing não destrua dados locais ou apague o módulo `urls.py`.
- **Pre-commit Hooks:** Existem ganchos de validação ativos (Flake8, Whitespace). Qualquer código gerado deve ser limpo e não conter espaços em branco sobrando nas quebras de linha para evitar falha no commit.

## 5. REGRAS DE ROTAS E DJANGO
- Toda nova "App" (Módulo) criada via `startapp` deve ser obrigatoriamente:
  1. Adicionada em `intranet/settings.py` (`INSTALLED_APPS`).
  2. Roteada em `intranet/urls.py`.
  3. Ter seu link registrado condicionalmente em `core/templates/core/base.html` (Sidebar).
  4. Testada utilizando o motor E2E `run_spider.py`.



Gemini, quero que voce seja uma desenvolvedora senior com experiencia e conhecimento na area de desenvolvimentos de sistemas e engenharia de software e ciencia de dados.
quero que voce desenvolva para mim tod oum sistema que iremos criar para igreja Palavra de Vida Enseada.

Regras:
1. Sempre criar o codigo completo de forma que ele seja auto testavel, e auto corrigivel des do inicio para criar um motor de auto correção de banco de dados e sistema que iremos desenvolver.
2. Auto teste, debug do codigo e Auto correção sempre que voce estiver terminando um sprint.
3. Sempre que terminar os testes correção, adicionar em documento de .md para sempre ter um registro do que foi feito com ID, Data e Hora e tudo que foi feito com detalhes bem descrito para vocer mesmo consultar para não haver erro, e que cada arquivo de codigo dentro deste sistema tenha LOG completo no topo para um leitura perfieta que voce vai criar e manter aqui C:\Users\MarcosLira\Desktop\Marcos\Projeto
4. O sistema sera desvolvido em uma maquina WIndows 10 PRO porem sera a produção sera posta em uma VPS linux ubuntu server 24.04.02 PRO usando dns pvenseada.org
5. Todos sistema tera e sera personalizavel da forma que precisarmos para auterar qualquer função, banco de dados hibrido não importando o peso ou não
6. VPS tera 32GB ram 8vCPU 400GB NMVE
7. Sempre olhar C:\Users\MarcosLira\Desktop\Marcos\Projeto, aqui vai esta todas as regras e objeticos, informações importantes para desenvolver
8. DIRETRIZ DE INICIALIZAÇÃO OBRIGATÓRIA E LEITURA DE CONTEXTO (PRE-FLIGHT CHECK):
Antes de iniciar qualquer análise, planejamento de sprint, alteração de banco de dados ou geração de código, o motor de desenvolvimento (Antigravity/IA) DEVE, obrigatoriamente e sem exceções, ler e processar todos os documentos base do sistema (Tecnologias, Modulos, UI-Designer, Integracao, BancoDeDados_Modelagem, Metodologias_Arquitetura, etc.), além de ler as credenciais dos usuários administradores.
Mais importante ainda: a IA deve ler todos os arquivos de LOG (.md) já gerados dentro do diretório C:\Users\MarcosLira\Desktop\Marcos\Projeto para entender exatamente o estado atual do projeto antes de prosseguir. Nenhuma ação será executada baseada em suposições, apenas na leitura direta dessa pasta raiz.

/////////////////////////////////////////////////////////////////////


NOME DO SISTEMA: "Palavra de Vida Enseada - Intranet"
Versão: "0.0.1"
Dev: "Marcos Roberto Lira"
Setor: "Servidores da Palavra"
email: "marcos@pvenseada.org"

/////////////////////////////////////////////////////////////////////

OBJETIVO:
Desenvolver um sistema de gestão para nossa Igreja voltado para membros que servem, gestão financeira e ativos, escalas. parte tecnica que fica em oculto.
Nosso principal hoje sera 4 Gestão de membros Voluntarios, Escala, Almoxarifado,Agerndda da Igreja.
Esse 4 Modulos são o calcanhar do sistema. para depois quando precisar criar mais eles serão os que vão liderar
O sistema precisa ser intuitivo, lembrando que Jovens, Meia Idade e Idosos que tem e não tem facilidade com tecnologia, as cores do sistema não podem se mistrurar com o fundo e virse e versa. as letras precisam ser legiveis e fontes intendiveis para humanos.


/////////////////////////////////////////////////////////////////////


HIRAQUIA - NIVEL DE ACESSO

Super-admin: Acesso total
Pastor Regente: Pastor Chefe que manda na Igreja e Tem acesso a Tudo, pode fazer tudo
Pastor: Tem o mesmo poder de um lider
Missionario: Tem o Mesmo poder de um lider
Lider: Comanda um ou mais ministerio, pode adicionar membros Voluntarios, subir nivel de Hiraquia, Criar Escalas, Editar, excluir e Adicionar onde ele for lider
Sub-lider: Pode Editar escalas na qual ele é sub-lider, Pode editar esclas mas não pode excluir ou criar.
Membro Voluntario: Pode ver suas escalas, adicionar informações de retirada no livro do almoxarifado/ativos, pedir folga de escala, avisar de indiponibilidade para dias esqpecificos, ver e editar seu proprio perfil.
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!

/////////////////////////////////////////////////////////////////////

GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS

Grupos e Ministerios são area dentro da igreja que não são tecnicas
Setor é uma area tecnica
Toda a igreja é dividida por esses 4 tipos, e todos seguem o mesmo papel e facilidade, todos os departamentos são perosnalizados e todos eles quando são criados precisam geraqr um ID unico fixo para que quando o membro for se cadastrar pela primeira vez ja se cadastrar usando o codigo do local e ja entrar direto como se fosse um codigo de convite
cada ministerio/grupo/setor/departamento pode ter suas proprias categorias de habilidades, copetencias e funções, para que na hora da escala não tenha duvida para que aquela pessoa foi chamada. que sejam tudo personalizado de acordo com cada pratica, area, grupo, departamento e setor
Alem disso,
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!

/////////////////////////////////////////////////////////////////////


PERFIL DE ACESSO/Membro

Na teoria, pastor, lider, sub-lider, pessoas que trabalham para igreja são Membros e todos eles podem editar suas informações, independente.
Nome completo, Data de nascimento, data de casamento, Com quem é casado, se tem filhos, nomes dos filhos, foto, CPF, RG, email, usuario e senha.
Aqui tambem a pessoa pode alterar sua senha, colocar seus dias que não da para ir caso tenha, colocar foto, atualizar ela se precisar.
Cada membro tera um dashboard interativo mostrando as escalas que ele esta, as datas do cultos e eventos para as proximas semanas, tera um local onde ele ve o dashboard do GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS que ele faz parte que pode sim se mais de um, e para isso precisa existir um inteligencia no sistema que não deixe repetir escala para os mesmos dias, exemplo: João ta escalo dia 13 paqra midia, mas dia 13 ele tambem esta na portaria, precisa se atentar o sistema para não cometer esse tipo de erro de escala, outra coisa, o sistema não pode ser comprometido.
Lideres podem ser membros de outros ministerios e serem lideres de mais de um por isso é portante existir um dashboard so para lideres e sub-liders para que eles tenha a opção de escoher qual eles querem editar para não ter erro.
No menu principal teremos um botão de login interativo e loga abaixo um auto cadastro somente com, nome, telefone, email e o codigo obrigatorio de GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS.
Todo o GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS tera um quadro de avisos onde sera postado para todos a quem pertecem a eles mensagens, avisos, lembretes, com pop-up e notificação real.
Todos os GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS terão um dashboard individual para mostrar informações de escala, para o membro ele podera vizualisar todas as informações referente a Escala, Mural de recados, avisos e lembrentes.
todos os GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS para lideres e sub-lideres ele poderão personalizar tudo ali dentro, postar informações para membros, caso ele tenha mais de um GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS ele pode selecionar a qual ele quer visualizar e editar.
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!




/////////////////////////////////////////////////////////////////////

ESCALAS:

O Sistema de criação de escala sera feito de 3 formas, automatica, onde o sistema escolhe quem é daquele departamento que não servil o suficiente respeitando limites de escala para não cansar o membro, respeitando as dastas colocadas de indisponibilidade e gera para o mes todo de acordo com os cultos.
de forma Manual, onde o lider e sub-lider conseuge escala de forma que arrasta e solta nome das pessoas gerando assim escala para o mes todo de forma padronizada e forma por escaner de exel onde o motor com ajuda da IA gemini gratuita vai fazer o OCR e ler o arquivo e gerar as escalas com os nomes que estão lá.
Os cultos eles são padronizados: Quarta: (20:00 as 22:00) e Domingo: (09:30 as 11:30 e 19:30 as 21:30) Lembrando que sempre na segunda semana no domingo sera santa ceia nos dois horarios.
Escala de eventos so da para fazer de forma manual.
Tdodas as escalas precisam ser gerardas ao final em PDF e XLSX, CSV para enviar via email e por whatsapp pra que os lideres e sub-lideres entreghuem via grupo mou individual.
Membro pode servir em mais de um GRUPOS, SETORES, MINISTERIOS E DEPARTAMENTOS.
Sistema de escala pecisa ser intuitivo, facil e escalonavel
Programações extras da igreja são: que não precisa ter escala mas pode deixar para escalar como opcional:
Segunda: Culto de Oração: 19:30 as 20:30
Terça: Atendimento Pastorial: 09:30 as 18:30
Quinta: Quinta do Saber 19:30 as 20:30
Tem os ensaios que reuniões que a liderança e sub-liderança marca e isso totalmente opcional.
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!


/////////////////////////////////////////////////////////////////////


MIDIA:

Hoje a midia tem um problema com pessoas que precisam aceitar os termos de compartilhamento de dados, para postagem em redes sociais, aparecer a imagem na Live que fica garvada depois no youtube, voz e video.
precisamos criar um local onde armazena os aceites destas pessoas, a midia vai gerar o documento, vai enviar de forma automatica para o email da pessoa, a pessoa aceita os termos e retorna para a o sistema que a pessoa aceito os termos.
precisa ter um historico, e se precisar anexar mais documentos que tenha a opção de anexar junto a aquele aceite que foi dado.
Esses documentos precisam ser facilmente editavel pela equipe da midia para que eles enviem tambem outros tipos de documentos para outras pessoas e assim vai!
lembrando que documentos ja gerados e ja criados assinados pelo usuario não podem ser mexidos por nada, somente serem anexados mais documentos e depois poder baixar eles quando precisar!


/////////////////////////////////////////////////////////////////////


Almoxarifado:
Aqui é o coração da gestão de tudo que tem dentro da igreja, esse modulo precisa ser dado atenção aqui, mas muita mesmo...
teremos aqui um livro que quam for retirar algo (qualquer um cadastrado no sistema) precisa registrar saida do material com o consentimento do lider ou sub-lider deste setor,
esse setor ele vai controlar todos os ativos da igreja, não so eletronicos mas tambem materias descartaveis, alimentos tudo.
Alimentos: O controle de alimento precisa ser objetivo e detalhado, com data de vencimento, uma locla so para monitorar eles, para ver quando vai vencer, para onde foi, quem retirou, se foi vendido, etc...
Ativos da igreja geral: Asism como allimentos, precisamos ver anexar documetnos, ou seja um sistema de almoxarifado completo e complexo para gestão de todo o material da igreja sem exeções
Qr code e codigo de barras, IDs unicos: Vamos usar essa forma para controle e gestão, assim como fica para o livro do almoxarifado de retirada para preenchimento via qr code que alguem vai ler e precher e retirar, assim que ler vai para o lider ou sub-lier ele ve quem retirou via notificação e email no web-app dele.
Tera umdashboard proprio
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!


/////////////////////////////////////////////////////////////////////


INTERGRAÇÂO

existe um JSON da Google Workspaces e Google Cloud na pasta C:\Users\MarcosLira\Desktop\Marcos\Projeto
Faça leitura dele sempre, precisamos da agenda, google drive, gmail e meet
eles são os principais opção de intergração
RESPEITE SEMPRE OS NIVEIS HIERARQUICOS!

/////////////////////////////////////////////////////////////////////

SEGURANÇA:
O sistema usara hash nas senhas, LOGs imutaveis e consultaveis para ver oque fezm quando fez e data e hora. o sistema tera um auto sistema de correção de bugs e dados e bugs, o sistema tera bootstrap para inicializar de forma sempre correta e se faltar algo ele vai criar, vai fazr acontecer.
o sistema usara ZERO-TRUST, tera um local para fazer backup automatico, um local para botar o sistema em mautenção e retirar depois, derrubar todos os que estão logados, tera anti, aplicara todas as regras de LGPD 2026 em todo o sistema.
Quando qualquer usuario se cadatsar tera que da uma aceite em termos do site para coleta de dados, vai mexer com informações pessoais escalas e documentos que não pode ser compartilhados sem autorização da igreja e assim vai tudo seguindo regras juridicas e LGDP e entendivel com leis e normas.




Chave de API
AIzaSyBLNh7SeHwhr61kcX_twQn1sALYSVc8ttc

Nome
Gemini API Key

Nome do projeto
projects/32022447872

Número do projeto
32022447872


curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: AIzaSyBLNh7SeHwhr61kcX_twQn1sALYSVc8ttc' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'




  NOME DO ARQUIVO: Integracao.txt
PROJETO: Palavra de Vida Enseada - Intranet (Versão 0.0.1) [cite: 7]
OBJETIVO: Mapear todas as comunicações externas e APIs ligadas ao sistema.

1. WORKSPACE E GOOGLE CLOUD:
- O sistema fará a leitura obrigatória e contínua do arquivo de credenciais JSON fornecido e armazenado em C:\Users\MarcosLira\Desktop\Marcos\Projeto[cite: 39].

2. SERVIÇOS DO GOOGLE INTEGRADOS:
- Google Agenda (Calendar): Gerenciamento do módulo "Agenda da Igreja", sincronizando eventos, cultos e reuniões extraoficiais[cite: 7, 39].
- Google Drive: Serviço de armazenamento imutável para os documentos PDF gerados pelo Módulo de Mídia e arquivos anexados do Almoxarifado[cite: 35, 37, 39].
- Gmail: Motor de disparo automático de e-mails para envio de PDFs de escalas (também via CSV/XLSX), termos de aceite de LGPD para membros e notificações de retiradas no Almoxarifado para líderes[cite: 28, 32, 38, 39].
- Google Meet: Integração nativa para criação de links de reuniões de liderança e atendimentos[cite: 39].

3. INTEGRAÇÃO COM INTELIGÊNCIA ARTIFICIAL:
- Motor OCR de Escalas: Utilização da API gratuita da IA Gemini para ler e interpretar planilhas Excel submetidas por upload, gerando as escalas automaticamente dentro do sistema[cite: 25].




NOME DO ARQUIVO: Metodologias_Arquitetura.txt
PROJETO: Palavra de Vida Enseada - Intranet (Versão 0.0.1)
OBJETIVO: Estabelecer as regras de estruturação de arquivos, design patterns, metodologias de código e localização (i18n).

1. METODOLOGIAS DE DESENVOLVIMENTO:
- DRY (Don't Repeat Yourself): Nenhuma lógica de negócio ou bloco de interface (HTML/HTMX) deve ser duplicada. Se um código é usado mais de uma vez, ele obrigatoriamente vira uma função utilitária, um mixin, ou um componente (partial) isolado.
- KISS (Keep It Simple, Stupid): A complexidade deve existir apenas onde é estritamente necessária (como no motor de resolução de escalas). A legibilidade do código está acima de "truques" de programação. Qualquer desenvolvedor deve ler e entender a lógica de imediato.

2. ESTRUTURA MODULAR E PASTAS:
O sistema Django será rigorosamente particionado. Cada módulo (ex: Gestao_Membros, Escalas, Almoxarifado, Midia_LGPD) será um "App" independente contendo a seguinte estrutura obrigatória:
/nome_do_modulo/
  ├── __init__.py
  ├── admin.py
  ├── apps.py
  ├── models/          # Entidades do banco de dados separadas por arquivos (se complexo) ou models.py único.
  ├── views/           # Lógica de controle separada em arquivos descritivos.
  ├── urls/            # Roteamento exclusivo do módulo.
  ├── tests/           # Scripts de TDD e testes unitários automatizados para o motor de autocorreção.
  ├── services/        # Regras de negócio pesadas (onde o DRY atua fortemente).
  ├── i18n/            # Arquivos JSON de tradução exclusivos deste módulo (ex: pt_br.json).
  └── templates/
      └── nome_do_modulo/
          ├── pages/   # Telas completas.
          └── partials/# Fragmentos HTMX e componentes reutilizáveis.

3. REGRAS DE IDIOMA E FORMATAÇÃO DE DADOS:
- Linguagem de Código e UI: Português do Brasil (pt-BR) simplificado, objetivo, formal e absolutamente sem gírias.
- Tratamento de Datas:
  * Banco de Dados: Armazenamento em formato ISO ou padrão relacional (timestamp).
  * Exibição (Front-end e Inputs): O formato de interação humana será estritamente dd/mm/aaaa hh:mm.
- Internacionalização (i18n): O sistema utilizará dicionários JSON modulares para carregar textos, permitindo rápida correção ou adição de novos idiomas sem alterar o código estrutural.

4. PADRÃO INEGOCIÁVEL DE ARQUIVOS E LOGS:
- Arquivo Completo: O desenvolvimento ocorre apenas com entregas de código de ponta a ponta. Nenhum arquivo será fornecido ou atualizado com partes ocultas ou "snippets".
- Cabeçalho de Autoria e Log: TODO arquivo (seja .py, .html, .js ou .json) deve obrigatoriamente iniciar com um bloco de comentários contendo:
  /*
  * PROJETO: Palavra de Vida Enseada - Intranet
  * ARQUIVO: [Nome do Arquivo]
  * DESCRIÇÃO: [O que este arquivo faz]
  * DEV: Marcos Roberto Lira (marcos@pvenseada.org)
  * VERSÃO: 0.0.1
  * DATA DA ÚLTIMA ALTERAÇÃO: [dd/mm/aaaa hh:mm]
  * LOG DE ALTERAÇÕES:
  * - [dd/mm/aaaa hh:mm]: Criação inicial / Atualização X
  */





  NOME DO ARQUIVO: Modulos.txt
PROJETO: Palavra de Vida Enseada - Intranet (Versão 0.0.1) [cite: 7]
OBJETIVO: Definir as regras de negócio e limites dos quatro módulos principais.

0. SEGURANÇA E HIERARQUIA (ZERO-TRUST) - APLICA-SE A TODOS OS MÓDULOS[cite: 42]:
- Todo acesso valida o nível do usuário: Super-admin, Pastor Regente, Pastor, Missionário, Líder, Sub-líder e Membro Voluntário[cite: 10, 11].
- O sistema usará hash nas senhas, e toda ação sensível criará Logs Imutáveis para auditoria (quem fez, quando e onde)[cite: 40].
- Aplicação rigorosa das diretrizes da LGPD (2026) em formulários e coleta de dados[cite: 42].

1. GESTÃO DE MEMBROS VOLUNTÁRIOS:
- Cadastro interativo que exige a vinculação com o ID único gerado pelos Grupos, Setores, Ministérios ou Departamentos[cite: 12, 20].
- Edição de perfil contendo: Nome completo, data de nascimento/casamento, dependentes, fotos, CPF, RG, e-mail e senha[cite: 16].
- O membro pode definir dias de indisponibilidade e solicitar folgas[cite: 11, 17].

2. ESCALAS:
- Prevenção de Conflitos: O motor possui inteligência para impedir que um membro seja escalado para o mesmo horário em funções/departamentos distintos (ex: Mídia e Portaria)[cite: 18, 60].
- 3 Métodos de Criação:
  a) Automática: Preenche o mês inteiro baseando-se no limite de cansaço, indisponibilidades e histórico do membro[cite: 24].
  b) Manual: Líderes e sub-líderes usam uma interface "arrastar e soltar"[cite: 25].
  c) Excel OCR: Upload de planilha e leitura via inteligência artificial[cite: 25].
- Horários Padronizados: Quarta (20h às 22h), Domingo (09:30 às 11:30 e 19:30 às 21:30)[cite: 26].
- Geração de arquivos finais em PDF, XLSX e CSV[cite: 28].

3. ALMOXARIFADO E ATIVOS:
- Gestão e controle rigoroso de eletrônicos, descartáveis e alimentos[cite: 36].
- Módulo de Alimentos: Monitoramento de lotes, datas de vencimento e destino[cite: 37].
- Retiradas: O preenchimento da saída do material é feito por leitura de QR Code ou Código de Barras via câmera do PWA[cite: 37, 51].
- A cada retirada, o líder ou sub-líder do setor recebe um alerta por notificação direta (push) e e-mail[cite: 38].

4. MÍDIA E ACEITE LGPD:
- Sistema de geração de documentos para uso de imagem/dados. O sistema envia automaticamente para o e-mail do membro[cite: 32].
- O usuário aceita os termos, o que gera um hash único no banco de dados vinculando o aceite[cite: 57].
- O PDF gerado é travado contra edições e salvo de forma imutável, permitindo apenas anexar novos documentos se necessário[cite: 35, 58].



NOME DO ARQUIVO: Tecnologias.txt
PROJETO: Palavra de Vida Enseada - Intranet (Versão 0.0.1)
OBJETIVO: Definir o stack tecnológico e regras de infraestrutura para o desenvolvimento.

1. LINGUAGENS E FRAMEWORKS:
- Back-end: Desenvolvido inteiramente em Python utilizando o framework Django.
- Front-end: Utilização de Django Templates aliados ao Tailwind CSS para estilização rápida e acessível.
- Reatividade Front-end: Implementação de HTMX + Alpine.js para criar uma experiência de Single Page Application (SPA), garantindo fluidez sem recarregar a tela inteira, mantendo a lógica no Python para facilitar o debug.
- Web-App (PWA): O sistema possuirá um Service Worker para funcionar como aplicativo instalável em smartphones, permitindo o uso de câmera nativa e recebimento de notificações push.

2. BANCO DE DADOS:
- Ambiente de Desenvolvimento (Local): SQLite3 em máquina Windows 10 PRO.
- Ambiente de Produção: PostgreSQL 18.

3. INFRAESTRUTURA DE PRODUÇÃO:
- Servidor: VPS Linux Ubuntu Server 24.04.02 PRO.
- Hardware da VPS: 32GB RAM, 8vCPU, 400GB NVMe.
- Domínio de Produção: pvenseada.org.

4. MOTOR DE AUTO-CORREÇÃO E PADRÃO DE CÓDIGO:
- Padrão inegociável de entrega: Arquivo Completo (Zero snippets), garantindo que o código não quebre o ambiente.
- O sistema terá um bootstrap de inicialização que utilizará migrations e fixtures para se reconstruir automaticamente caso haja falhas no banco ou seja instalado em uma máquina nova.
- Todo final de sprint exige a criação de testes unitários automatizados.
- Todas as alterações devem ser rigorosamente documentadas em arquivos `.md` na pasta raiz (C:\Users\MarcosLira\Desktop\Marcos\Projeto), contendo ID, Data, Hora e logs detalhados de cada alteração para consultas futuras.





NOME DO ARQUIVO: UI-Designer.txt
PROJETO: Palavra de Vida Enseada - Intranet (Versão 0.0.1) [cite: 7]
OBJETIVO: Diretrizes visuais e de experiência de usuário (UX/UI).

1. ACESSIBILIDADE E CLAREZA:
- As cores da interface não podem se misturar ou gerar baixo contraste com os fundos de tela[cite: 8].
- A tipografia deve utilizar fontes inteligíveis, com letras legíveis e de fácil leitura, garantindo que membros de todas as idades (jovens a idosos) compreendam o sistema sem dificuldades[cite: 8, 9].
- Utilização exclusiva do Tailwind CSS para manter a consistência deste design system responsivo[cite: 48].

2. COMPORTAMENTO E NAVEGAÇÃO:
- A interface não pode travar. O sistema deve usar HTMX para funcionar de maneira fluida (SPA), sem carregamentos brutos de tela inteira[cite: 49, 50].
- O login principal deve ser interativo com opção de auto-cadastro imediatamente abaixo[cite: 20].

3. DASHBOARDS E ESPAÇOS DE TRABALHO:
- Membros: Dashboard pessoal com resumo de escalas em que estão envolvidos e eventos das próximas semanas[cite: 18].
- Departamentos/Grupos: Cada área possuirá um painel individualizado com as escalas do setor, mural de recados e gestão de permissões para os líderes e sub-líderes[cite: 22, 23].
- Se um líder gerencia múltiplos departamentos, a UI deve apresentar um seletor visual claro para que ele alterne entre eles sem risco de editar o local errado[cite: 19, 23].

4. NOTIFICAÇÕES (PWA):
- O design deve suportar alertas visuais pop-up na tela[cite: 21].
- Suporte nativo para Notificações Push via Service Worker para chamados de mural, recados de liderança e retiradas no almoxarifado[cite: 21, 51].
