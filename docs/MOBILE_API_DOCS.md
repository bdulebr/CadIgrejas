# Documentação Oficial de Integração API - Intranet PV Enseada

## 📌 Contexto para IA
Você está atuando como Engenheiro Mobile / Frontend. O sistema backend já está construído e rodando sob **Django 6** com **Django REST Framework (DRF)**. O objetivo deste documento é fornecer as diretrizes absolutas de como se conectar à Intranet, realizar autenticação e consumir os dados para o Aplicativo Mobile.

### Stack Tecnológica do Backend
- **Linguagem:** Python 3.12+
- **Framework:** Django 6.0 + Django REST Framework
- **Autenticação Mobile:** JWT (JSON Web Tokens) usando `djangorestframework-simplejwt`
- **Banco de Dados:** SQLite (com suporte nativo de concorrência)
- **CORS:** Ativado para todas as origens (permitindo fácil desenvolvimento Mobile via localhost/Expo)

---

## 🔒 1. Fluxo de Autenticação (JWT)

A Intranet **NÃO** utiliza cookies ou sessões HTML para o Aplicativo Mobile. Toda requisição privada deve conter o cabeçalho HTTP:
`Authorization: Bearer <ACCESS_TOKEN>`

### Obter o Token (Login)
**Endpoint:** `POST /api/auth/login/`
**Body (JSON):**
```json
{
  "email": "membro@pvenseada.org",
  "password": "senha_segura"
}
```
**Resposta de Sucesso (200 OK):**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI..."
}
```
*O `access` token tem validade de 1 hora. O `refresh` token dura 7 dias. O aplicativo deve armazená-los localmente (ex: AsyncStorage).*

### Renovar o Token Vencido (Refresh)
**Endpoint:** `POST /api/auth/refresh/`
**Body (JSON):**
```json
{
  "refresh": "<SEU_REFRESH_TOKEN_AQUI>"
}
```
**Resposta (200 OK):**
```json
{
  "access": "NOVO_ACCESS_TOKEN"
}
```

---

## 📡 2. Endpoints Base

O módulo central da API reside na pasta `/api/` do Django. 

### Perfil do Usuário Logado
**Endpoint:** `GET /api/perfil/me/`
**Headers:** `Authorization: Bearer <ACCESS_TOKEN>`
**Descrição:** Retorna os dados completos do Membro autenticado.
**Exemplo de Resposta (200 OK):**
```json
{
  "id": 1,
  "first_name": "Marcos",
  "last_name": "Lira",
  "email": "membro@pvenseada.org",
  "telefone": "(11) 99999-9999",
  "nivel_hierarquico": "super_admin",
  "nivel_display": "Super Administrador",
  "departamentos": [
    {
      "id": 1,
      "nome": "Servidores da Palavra",
      "categoria": "apoio"
    }
  ]
}
```

---

## 🏗 3. Estrutura de Banco de Dados (Resumo)

Caso você (IA) precise solicitar a criação de novos endpoints para o Engenheiro Backend, entenda como o sistema está modelado:

1. **`core.Membro`**: Tabela central (User Customizado). Possui campos como `nivel_hierarquico` (`super_admin`, `lider`, `sub_lider`, `membro_voluntario`), foto de perfil e relacionamentos com Departamentos.
2. **`gestao_membros.Departamento`**: Centros de custo/serviço da igreja (ex: Mídia, Louvor, Servidores). Líderes e Membros são atrelados a departamentos.
3. **`escalas.CompetenciaEscala`**: Agrupador mensal de escalas (ex: "Escala Mídia - Maio/2026").
4. **`escalas.SlotEscala`**: O "plantão" em si, contendo data, horário, membro escalado e função.
5. **`almoxarifado.ItemAlmoxarifado`**: Itens do patrimônio da igreja, sujeitos a empréstimos e devoluções monitoradas.

---

## 🛠 4. Como Expandir a API (Instrução para IA Backend)

Se o usuário solicitar a criação de uma nova tela no App Mobile (exemplo: "Tela de ver Minhas Escalas"), a IA que está lidando com o Backend Django deve seguir este fluxo **OBRIGATÓRIO**:

1. **NUNCA** crie views baseadas em template (HTML) dentro do app `api`.
2. Vá para o arquivo `api/serializers.py` e crie o Serializer necessário (ex: `SlotEscalaSerializer`).
3. Vá para o arquivo `api/views.py` e crie uma classe baseada em `APIView` ou `ModelViewSet`, sempre protegida por `permission_classes = [IsAuthenticated]`.
4. Registre a rota em `api/urls.py`.
5. Comunique a estrutura do JSON resultante para o Desenvolvedor Mobile.
