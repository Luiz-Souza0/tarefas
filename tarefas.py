import streamlit as st
import uuid
from datetime import date
from supabase import create_client, Client

# -------------------------------
# CONFIGURAÇÃO SUPABASE
# -------------------------------
SUPABASE_URL = "https://ydzpvmvhytmndphblzrg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkenB2bXZoeXRtbmRwaGJsenJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE4MzYwOTQsImV4cCI6MjA3NzQxMjA5NH0.sQ-QtSyeMyXQ8O267_ePadlVlmRedF4HtrCLRIIN2ok"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# FUNÇÕES SUPABASE
# -------------------------------
def carregar_tarefas():
    """Carrega todas as tarefas do banco."""
    try:
        response = supabase.table("tarefas").select("*").execute()
        tarefas = {}
        for t in response.data:
            tarefas[t["id"]] = {
                "texto": t["texto"],
                "concluida": t["concluida"],
                "data_inicio": t["data_inicio"],
                "data_conclusao": t["data_conclusao"] or "",
            }
        return tarefas
    except Exception as e:
        st.warning(f"Erro ao carregar tarefas: {e}")
        return {}


def adicionar_tarefa(texto, data_inicio):
    """Adiciona uma nova tarefa."""
    id_tarefa = str(uuid.uuid4())
    tarefa = {
        "id": id_tarefa,
        "texto": texto,
        "concluida": False,
        "data_inicio": str(data_inicio),
        "data_conclusao": None,
    }
    supabase.table("tarefas").insert(tarefa).execute()
    return id_tarefa, tarefa


def atualizar_tarefa(id_tarefa, campo, valor):
    """Atualiza um campo específico de uma tarefa."""
    supabase.table("tarefas").update({campo: valor}).eq("id", id_tarefa).execute()


def excluir_tarefa(id_tarefa):
    """Exclui uma tarefa."""
    supabase.table("tarefas").delete().eq("id", id_tarefa).execute()

# -------------------------------
# CALLBACK DO CHECKBOX
# -------------------------------
def marcar_concluida(id_tarefa):
    """Marca ou desmarca uma tarefa como concluída."""
    concluida = st.session_state[f"chk_{id_tarefa}"]
    st.session_state.tarefas[id_tarefa]["concluida"] = concluida

    if concluida:
        data_conclusao = str(date.today())
        st.session_state.tarefas[id_tarefa]["data_conclusao"] = data_conclusao
        atualizar_tarefa(id_tarefa, "concluida", True)
        atualizar_tarefa(id_tarefa, "data_conclusao", data_conclusao)
    else:
        st.session_state.tarefas[id_tarefa]["data_conclusao"] = ""
        atualizar_tarefa(id_tarefa, "concluida", False)
        atualizar_tarefa(id_tarefa, "data_conclusao", None)

# -------------------------------
# INICIALIZAÇÃO STREAMLIT
# -------------------------------
st.set_page_config(page_title="Gerenciador de Tarefas", layout="centered")
st.title("📝 Gerenciador de Tarefas")

if "tarefas" not in st.session_state:
    st.session_state.tarefas = carregar_tarefas()
if "editando" not in st.session_state:
    st.session_state.editando = None

# -------------------------------
# FORMULÁRIO DE NOVA TAREFA
# -------------------------------
with st.form("nova_tarefa_form"):
    nova_tarefa = st.text_input("Digite uma nova tarefa:")
    data_inicio = st.date_input("Data de início:", value=date.today())
    submit = st.form_submit_button("Adicionar")

if submit and nova_tarefa.strip():
    id_tarefa, tarefa = adicionar_tarefa(nova_tarefa, data_inicio)
    st.session_state.tarefas[id_tarefa] = tarefa
    st.success("✅ Tarefa adicionada com sucesso!")
    st.experimental_rerun()

# -------------------------------
# LISTAGEM DE TAREFAS
# -------------------------------
st.subheader("📋 Lista de Tarefas")

if not st.session_state.tarefas:
    st.info("Nenhuma tarefa adicionada ainda.")
else:
    for id_tarefa, tarefa in list(st.session_state.tarefas.items()):
        cols = st.columns([0.05, 0.35, 0.25, 0.15, 0.2])

        with cols[0]:
            st.checkbox(
                "Concluída",
                value=tarefa["concluida"],
                key=f"chk_{id_tarefa}",
                label_visibility="collapsed",
                on_change=marcar_concluida,
                args=(id_tarefa,),
            )

        with cols[1]:
            if st.session_state.editando == id_tarefa:
                novo_texto = st.text_input(
                    "Editar tarefa:", tarefa["texto"], key=f"edit_text_{id_tarefa}"
                )
            else:
                if tarefa["concluida"]:
                    st.markdown(f"✅ ~~{tarefa['texto']}~~")
                else:
                    st.markdown(tarefa["texto"])

        with cols[2]:
            st.write(f"🕒 Início: {tarefa['data_inicio']}")
            if tarefa["data_conclusao"]:
                st.write(f"🏁 Conclusão: {tarefa['data_conclusao']}")

        with cols[3]:
            if st.session_state.editando == id_tarefa:
                if st.button("Salvar", key=f"save_{id_tarefa}"):
                    novo_texto = st.session_state.get(f"edit_text_{id_tarefa}", tarefa["texto"])
                    st.session_state.tarefas[id_tarefa]["texto"] = novo_texto
                    atualizar_tarefa(id_tarefa, "texto", novo_texto)
                    st.session_state.editando = None
                    st.experimental_rerun()
            else:
                if st.button("Editar", key=f"edit_{id_tarefa}"):
                    st.session_state.editando = id_tarefa
                    st.experimental_rerun()

        with cols[4]:
            if st.button("Excluir", key=f"del_{id_tarefa}"):
                excluir_tarefa(id_tarefa)
                del st.session_state.tarefas[id_tarefa]
                if st.session_state.editando == id_tarefa:
                    st.session_state.editando = None
                st.experimental_rerun()
