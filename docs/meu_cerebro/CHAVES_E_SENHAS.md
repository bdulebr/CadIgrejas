# CHAVES, SENHAS E CREDENCIAIS DO SISTEMA
**Aviso de Segurança:** Como este repositório é privado e o `.env` está sendo sincronizado no Git, este documento serve exclusivamente como espelho das configurações para a IA (Cão de Guarda) ter contexto absoluto ao realizar manutenções e deploys a partir de outras máquinas.

## 1. Chaves de Inteligência Artificial
- **OpenAI (ChatGPT):** `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` (Principal Motor de RAG)
- **Google Gemini:** `AIzaSyBLNh7SeHwhr61kcX_twQn1sALYSVc8ttc` (Motor de Fallback)
- **Groq API:** `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` (Para inferências rápidas ou uso legado)

## 2. Configurações de E-mail (SMTP)
Usado para envio de comunicações, alertas de escala, 2ª via da LGPD e resets de senha.
- **Servidor SMTP:** `smtp.gmail.com`
- **Porta:** `587`
- **Usuário:** `marcos@pvenseada.org`
- **Senha de Aplicativo:** `rukhvrwyvcfoqpbv`

## 3. Integração Google Workspace (Drive & Agenda)
- **Google Calendar ID:** `c_c6f5beb74d5fe805ca3fd54eea369a3a926587cc3998348158141932d423b9fa@group.calendar.google.com`
- **Pasta Root do PV Drive:** `0AJ9AzzNIVmUbUk9PVA`
- **Sub-pasta de Usuários (LGPD, Documentos):** `1TrKlPmBEaNBz3tWsnzhAGvLe_RFDN0nW`
- **Sub-pasta de Departamentos:** `18zXOCxU8SKTvhYe7jXWoEOGEvLUo33rW`

## 4. Chaves Base do Django
- **SECRET_KEY:** `pvenseada-3x!9k*5z@p#a1v&q^m$7w)4n(2b_8y-6c+5d=9f*1g@0h`
- **BASE_URL:** `https://intranet.pvenseda.org`

## Nota sobre a Mudança de Máquina
As chaves acima refletem o que está contido no arquivo `.env`. Na nova máquina, certifique-se de que o `.env` acompanha o código (o que já foi forçado no último push para a branch `main`). Caso o `.env` seja perdido, a IA poderá recriá-lo com 100% de precisão baseada neste documento.
