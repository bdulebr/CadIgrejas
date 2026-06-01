# SYSTEM ARCHITECTURE - PV ENSEADA INTRANET
**Target Audience:** AI Assistants / LLMs (Future Code Audits and Features)
**Version:** 1.0 (Zero-Trust Security Standard)
**Language:** Python 3.12, Django 6.0.5

## 1. Overview
The PV Enseada Intranet is a monolithic ERP tailored for church management, combining advanced zero-trust architecture, member management, scalable role-based access control (RBAC), LGPD compliance, and asset tracking.
- **Frontend Stack:** HTML5, TailwindCSS (CDN), Alpine.js (Lightweight reactivity), Lucide Icons, HTMX (for dynamic data loading and modals).
- **Backend Stack:** Django 6.x.
- **Database:** SQLite (File-based, `db.sqlite3`).
- **Production Server (Windows):** Waitress + WhiteNoise (for static files).

## 2. Core Concepts & Security (Zero-Trust)
### 2.1 Role-Based Access Control (RBAC)
The system operates on a strictly tiered `nivel_hierarquico` defined in the `core.Membro` model.
- **`user`**: Basic access. Can only view public events, their own scales, and sign LGPD terms.
- **`lider`**: Department-level access. Can view members within their allocated departments, manage sub-scales, and send basic notifications.
- **`lider_global`**: Has broader access across multiple departments but no system-wide configuration powers.
- **`super_admin`**: God mode. Can access the `Sysadmin` module, `Django Admin`, zero the database, manage the `.env` settings directly from the UI, and view the global Member Management panel.

### 2.2 Global Middlewares
- **`MaintenanceMiddleware`**: Checks the `ConfiguracaoSistema` table. If `is_maintenance` is True, it locks out everyone EXCEPT `super_admin`.
- **`ForcarTrocaSenhaMiddleware`**: Forces users with `senha_padrao=True` to change their passwords immediately before accessing any authenticated route.
- **`RequestMiddleware`**: Injects the HTTP request into a thread-local variable `_thread_locals`. Used primarily by the Audit Log model to automatically grab the user performing an action without passing `request` to every `save()` method.

### 2.3 Immutable Audit Logging (`core.LogAuditoria`)
Every database modification triggers an Audit Log via Django Signals (`core/signals.py`). The log implements a **Hash Chain** (Blockchain-like concept) where `hash_atual = SHA256(data + hash_anterior)`. This ensures that even if someone manually edits the SQLite file, the audit trail will break, exposing the tampering.

## 3. Database Schema (Key Apps)

### 3.1 Core (`core/models.py`)
- **`Membro`**: Overrides Django's `AbstractUser`. Stores deep personal data (CPF, RG, marital status, allergies, baptism date, etc.). Linked to `status_conta` (Ativo, Inativo, Bloqueado).
- **`ConfiguracaoSistema`**: Singleton model (ID=1). Stores global flags like Maintenance Mode, Email Enable/Disable, Church Name/CNPJ.
- **`LinkRapido`**: Models quick shortcuts rendered dynamically in the sidebar. Icons are dynamically fetched via Google Favicon API using the URL.

### 3.2 Gestão de Membros (`gestao_membros/models.py`)
- **`Departamento`**: Cost centers / Ministries. Members can be linked as normal participants, leaders, or sub-leaders.
- **`Habilidade` / `Funcao`**: Skills required to execute tasks in scales.
- **`AvisoMural`**: Broadcasting system to send alerts and trigger real SMTP emails.

### 3.3 Escalas (`escalas/models.py`)
- **`Escala` / `CompetenciaEscala`**: Roster management. Users are allocated to `Funcoes` on specific dates (`CultoEvento`).

### 3.4 Almoxarifado (`almoxarifado/models.py`)
- **`Ativo`**: Physical items tracking.
- **`Emprestimo`**: Checkout system for assets.
- **`AlimentoLote` / `TransacaoAlimento`**: Controls food inventory (FIFO / validity dates).

### 3.5 Mídia & LGPD (`midia_lgpd/models.py`)
- **`PastaVirtual` / `ArquivoMidia`**: Emulates a Google Drive folder structure locally.
- **`TermoLGPD` / `AssinaturaLGPD`**: Digital signature tracking. Records IP and timestamp of acceptance.

## 4. Known Workarounds & System Behaviors
- **Waitress Auto-Restart**: Waitress on Windows does not support hot-reloading. The Sysadmin module (`sysadmin_toggle_debug` and `sysadmin_salvar_env`) forcefully kills the python process (`os._exit(0)`). The `run_prod.bat` file runs in an infinite loop (`goto start`), ensuring the server immediately boots back up with the new variables.
- **Email Dispatching**: Emails are sent via `intranet.services.gmail_service`. This module checks the global kill-switch (`envios_email_ativos`) before doing SMTP transactions. If the kill-switch is active, it silently returns `True` and prints to console.

## 5. Deployment & Execution
To start the system in production mode on Windows:
```bat
run_prod.bat
```
This activates the virtual environment, reads the `.env` file, prints the current security status, and launches Waitress on port `8000`.

## 6. Audit & Verification Status
- **Models sync**: All models are synced with Django Admin (`admin.py`).
- **Mocks**: No significant UI mocks remain. `enviar_email_html` is fully implemented and bridged.
- **Database Integrity**: `makemigrations` and `check` commands return cleanly.
