import json
from django.utils import timezone
from core.models import Membro
from escalas.models import CompetenciaEscala, Escala, CultoEvento
from gestao_membros.models import Departamento
from ministerio_casais.models import HistoricoAconselhamentoCasal, Casal

def gerenciar_membros(user, acao: str, nome: str = None, email: str = None, telefone: str = None) -> str:
    """
    Ferramenta para gerenciar Membros e Voluntários. Permite listar ou criar um membro.
    :param user: O usuário logado que invocou a ferramenta (injetado automaticamente).
    :param acao: 'listar' ou 'criar'
    :param nome: Nome completo do membro (para criar ou buscar).
    :param email: E-mail do membro (opcional na criação).
    :param telefone: Telefone (opcional na criação).
    """
    if not user.has_perm('core.add_membro') and not user.has_perm('core.view_membro'):
        return "Deus tá vendo! Você não tem autorização para gerenciar membros do sistema."

    if acao == 'listar':
        qs = Membro.objects.all()
        if nome:
            qs = qs.filter(first_name__icontains=nome)
        membros = list(qs.values('id', 'first_name', 'last_name', 'email')[:10])
        return f"Lista de Membros (Top 10): {json.dumps(membros)}"

    elif acao == 'criar':
        if not user.has_perm('core.add_membro'):
            return "Acesso negado: Você não tem permissão de adicionar membros."
        if not nome:
            return "Erro: O nome é obrigatório para criar um membro."

        nomes = nome.split()
        first_name = nomes[0]
        last_name = " ".join(nomes[1:]) if len(nomes) > 1 else ""
        username = email if email else f"{first_name.lower()}{timezone.now().timestamp()}"

        novo_membro = Membro.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email or "",
            telefone=telefone or ""
        )
        return f"Membro criado com sucesso! ID: {novo_membro.id}, Nome: {novo_membro.get_full_name()}"

    return "Ação inválida. Use 'listar' ou 'criar'."


def gerenciar_escalas(user, acao: str, departamento_id: int = None, mes_ano: str = None, membro_id: int = None, data_escala: str = None, horario_inicio: str = "19:30:00", horario_fim: str = "21:30:00", tipo_evento: str = "1") -> str:
    """
    Ferramenta para gerenciar as Escalas de Voluntários.
    :param user: Usuário logado.
    :param acao: 'listar' ou 'criar_escala_membro'
    :param departamento_id: ID do departamento da escala.
    :param mes_ano: Competência (ex: 06/2026).
    :param membro_id: ID do membro a ser escalado.
    :param data_escala: Data da escala (ex: 2026-06-25).
    :param horario_inicio: Horário de início (ex: 19:30:00).
    :param horario_fim: Horário de término.
    :param tipo_evento: ID do Culto/Evento ou string.
    """
    if not user.has_perm('escalas.view_escala') and not user.has_perm('escalas.add_escala'):
        return "Você não possui permissão para acessar o módulo de Escalas."

    if acao == 'listar':
        qs = Escala.objects.select_related('membro_escalado').all()
        if mes_ano:
            qs = qs.filter(competencia__mes_ano=mes_ano)
        if departamento_id:
            qs = qs.filter(departamento_alocado_id=departamento_id)

        escalas = []
        for e in qs[:15]:
            escalas.append({
                'id': e.id,
                'membro': e.membro_escalado.get_full_name(),
                'data': str(e.data_escala),
                'inicio': str(e.horario_inicio)
            })
        return f"Lista de Escalas: {json.dumps(escalas)}"

    elif acao == 'criar_escala_membro':
        if not user.has_perm('escalas.add_escala'):
            return "Acesso negado: Você não pode criar escalas."
        if not all([departamento_id, mes_ano, membro_id, data_escala]):
            return "Erro: departamento_id, mes_ano, membro_id e data_escala são obrigatórios para criar escala."

        # Validar líder de departamento
        lider = Departamento.objects.filter(id=departamento_id, lideres=user).exists()
        if not lider and not user.is_superuser:
            return "Acesso negado: Você só pode escalar voluntários em departamentos que você lidera."

        try:
            competencia, _ = CompetenciaEscala.objects.get_or_create(
                departamento_id=departamento_id,
                mes_ano=mes_ano,
                defaults={'status': 'rascunho'}
            )

            nova_escala = Escala.objects.create(
                competencia=competencia,
                membro_escalado_id=membro_id,
                departamento_alocado_id=departamento_id,
                data_escala=data_escala,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_evento=tipo_evento,
                status='confirmado'
            )
            return f"Escala confirmada com sucesso para o membro ID {membro_id} no dia {data_escala}."
        except Exception as e:
            return f"Erro ao criar escala (Possível conflito de horário): {str(e)}"

    return "Ação inválida."


def gerenciar_dossie(user, acao: str, casal_id: int = None, pastor: str = None, observacoes: str = None, nivel_crise: int = 1, atendimento_para: str = 'Casal') -> str:
    """
    Ferramenta para gerenciar Dossiês de Atendimento Pastoral e Aconselhamento.
    :param user: Usuário logado.
    :param acao: 'listar' ou 'criar'
    :param casal_id: ID do casal atendido.
    :param pastor: Nome do pastor conselheiro.
    :param observacoes: Anotações da sessão do dossiê.
    :param nivel_crise: 1 a 5 (5 sendo o mais crítico).
    :param atendimento_para: 'Casal', 'Apenas Cônjuge 1' ou 'Apenas Cônjuge 2'.
    """
    if not user.has_perm('ministerio_casais.add_historicoaconselhamentocasal'):
        return "Deus tá vendo! Você não é Pastor/Conselheiro para acessar dossiês confidenciais."

    if acao == 'listar':
        qs = HistoricoAconselhamentoCasal.objects.all()
        if casal_id:
            qs = qs.filter(casal_id=casal_id)

        logs = []
        for h in qs.order_by('-data_sessao')[:5]:
            logs.append({
                'casal': h.casal.nomes_juntos,
                'data': str(h.data_sessao),
                'pastor': h.pastor_conselheiro,
                'crise': h.nivel_crise
            })
        return f"Dossiês: {json.dumps(logs)}"

    elif acao == 'criar':
        if not casal_id or not observacoes:
            return "Erro: casal_id e observacoes são obrigatórios para registrar um dossiê."

        try:
            Dossie = HistoricoAconselhamentoCasal.objects.create(
                casal_id=casal_id,
                pastor_conselheiro=pastor or user.get_full_name(),
                observacoes=observacoes,
                nivel_crise=nivel_crise,
                atendimento_para=atendimento_para
            )
            return f"Dossiê pastoral arquivado com sucesso e de forma confidencial. ID: {Dossie.id}"
        except Exception as e:
            return f"Erro ao arquivar dossiê: {e}"

    return "Ação inválida."


def gerenciar_drive(user, acao: str, nome: str = None, pasta_id: int = None, arquivo_id: int = None, membro_alvo_id: int = None, nivel_permissao: str = 'leitor') -> str:
    """
    Ferramenta para gerenciar o PV Drive (Arquivos, Pastas e Compartilhamento).
    :param user: Usuário logado.
    :param acao: 'listar', 'criar_pasta', 'renomear_pasta', 'excluir_pasta', 'excluir_arquivo', 'compartilhar_pasta', 'mover_anexo'
    :param nome: Nome para nova pasta ou novo nome para renomear.
    :param pasta_id: ID da pasta (usado para listar, excluir, pai da nova pasta, ou destino do anexo).
    :param arquivo_id: ID do ArquivoMidia a ser excluído ou movido.
    :param membro_alvo_id: ID do membro para compartilhar.
    :param nivel_permissao: 'leitor', 'editor' ou 'admin'.
    """
    from midia_lgpd.models import PastaVirtual, ArquivoMidia, PermissaoPVDrive

    # Verifica permissão básica de acesso ao app midia_lgpd
    if not user.has_perm('midia_lgpd.view_pastavirtual'):
        return "Deus tá vendo! Você não tem autorização para acessar o PV Drive."

    if acao == 'listar':
        pastas = PastaVirtual.objects.filter(is_excluida=False)
        # Filtro simples: Se for superuser vê tudo, senão só as públicas/pessoais/departamento dele (simplificado para IA)
        res = [{"id": p.id, "nome": p.nome, "tipo": p.tipo_pasta} for p in pastas[:20]]
        return f"Conteúdo do Drive (Pastas recentes): {json.dumps(res)}"

    elif acao == 'criar_pasta':
        if not nome:
            return "Preciso de um nome para criar a pasta."
        nova = PastaVirtual.objects.create(nome=nome, criado_por=user, dono_membro=user, tipo_pasta='usuario', parent_id=pasta_id)
        return f"Pasta '{nome}' criada com sucesso! ID: {nova.id}"

    elif acao == 'renomear_pasta':
        if not pasta_id or not nome:
            return "Falta pasta_id ou novo nome."
        PastaVirtual.objects.filter(id=pasta_id).update(nome=nome)
        return f"Pasta ID {pasta_id} renomeada para '{nome}'."

    elif acao == 'excluir_pasta':
        if not pasta_id:
            return "Falta pasta_id."
        PastaVirtual.objects.filter(id=pasta_id).update(is_excluida=True, data_exclusao=timezone.now())
        return f"Pasta ID {pasta_id} movida para a lixeira."

    elif acao == 'excluir_arquivo':
        if not arquivo_id:
            return "Falta arquivo_id."
        ArquivoMidia.objects.filter(id=arquivo_id).update(is_excluido=True, data_exclusao=timezone.now())
        return f"Arquivo ID {arquivo_id} excluído."

    elif acao == 'compartilhar_pasta':
        if not pasta_id or not membro_alvo_id:
            return "Falta pasta_id ou membro_alvo_id."
        p = PermissaoPVDrive.objects.create(pasta_id=pasta_id, alvo_membro_id=membro_alvo_id, nivel=nivel_permissao, concedido_por=user)
        return f"Pasta ID {pasta_id} compartilhada com Membro ID {membro_alvo_id} como {nivel_permissao}."

    elif acao == 'mover_anexo':
        if not arquivo_id or not pasta_id:
            return "Falta arquivo_id ou pasta_id para mover o anexo."
        ArquivoMidia.objects.filter(id=arquivo_id).update(pasta_id=pasta_id)
        return f"Anexo ID {arquivo_id} movido permanentemente para a Pasta ID {pasta_id} do PV Drive."

    return "Ação do Drive não reconhecida."


EVERSINHO_TOOLS_REGISTRY = [
    gerenciar_membros,
    gerenciar_escalas,
    gerenciar_dossie,
    gerenciar_drive
]
