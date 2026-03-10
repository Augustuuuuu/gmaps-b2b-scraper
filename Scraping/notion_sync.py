"""
notion_sync.py
──────────────────────────────────────────────────────────────────
Módulo de integração entre o Google Maps Scraper e o Notion API.
Importe este arquivo no seu script principal.

SETUP (uma vez só):
  1. pip install requests python-dotenv
  2. Crie um arquivo .env na mesma pasta com:
       NOTION_TOKEN=secret_xxxxxxxxxxxx
       DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  3. Siga o passo a passo no README abaixo para obter os dois valores.

COMO OBTER O NOTION_TOKEN:
  1. Acesse https://www.notion.so/my-integrations
  2. Clique em "New integration"
  3. Dê um nome (ex: "LeadScraper") e clique em Submit
  4. Copie o "Internal Integration Token" → cole no .env como NOTION_TOKEN

COMO OBTER O DATABASE_ID:
  1. Abra sua Base de Leads no Notion pelo navegador
  2. A URL será algo como:
     https://www.notion.so/SEU-NOME/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...
  3. O DATABASE_ID é a sequência de 32 caracteres após a última barra (/)
     e antes do "?" — cole no .env como DATABASE_ID

COMO CONECTAR A INTEGRAÇÃO AO BANCO:
  1. Abra sua Base de Leads no Notion
  2. Clique nos "..." (três pontos) no canto superior direito
  3. Vá em "Connections" → "Connect to" → selecione "LeadScraper"
  4. Confirme — sem isso a API retornará erro 404
"""

import os
import re
import time
import requests
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID  = os.getenv("DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type":  "application/json",
    "Notion-Version": "2022-06-28",
}

# Nomes dos campos exatamente como estão no seu Notion
CAMPOS = {
    "empresa":     "Empresa",          # Tipo: Title
    "segmento":    "Segmento",         # Tipo: Select
    "cidade":      "Cidade",           # Tipo: Text
    "whatsapp":    "WhatsApp",         # Tipo: Phone
    "instagram":   "Instagram",        # Tipo: URL
    "responsavel": "Responsável",      # Tipo: Text  ← acento
    "etapa":       "Etapa",            # Tipo: Select
    "rodada":      "Rodada",           # Tipo: Select  ← adicione no Notion se quiser
    "temperatura": "Temperatura",      # Tipo: Select
    "data":        "Data 1° Contato",  # Tipo: Date    ← símbolo °
    "link_maps":   "Link Maps",        # Tipo: URL     ← adicione no Notion
    "observacoes": "Observações",      # Tipo: Text    ← acento
}


# ──────────────────────────────────────────────
# FUNÇÃO PRINCIPAL
# ──────────────────────────────────────────────

def adicionar_lead(
    empresa:     str,
    cidade:      str  = "",
    whatsapp:    str  = "",
    segmento:    str  = "",
    instagram:   str  = "",
    responsavel: str  = "",
    rodada:      str  = "",
    link_maps:   str  = "",
    observacoes: str  = "",
) -> bool:
    """
    Cria um novo card na sua Base de Leads do Notion.
    Retorna True se criou com sucesso, False se falhou.

    A etapa inicial é sempre 'Prospectado' e a temperatura 'Frio',
    pois o lead acabou de ser encontrado — você ajusta manualmente
    conforme for conversando com o cliente.
    """
    if not NOTION_TOKEN or not DATABASE_ID:
        print("  ⚠️  NOTION_TOKEN ou DATABASE_ID não configurados no .env")
        return False

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            CAMPOS["empresa"]: {
                "title": [{"text": {"content": empresa[:200]}}]
            },
            CAMPOS["etapa"]: {
                "select": {"name": "🔍 Prospectado"}
            },
            CAMPOS["temperatura"]: {
                "select": {"name": "❄️ Frio"}
            },
            CAMPOS["data"]: {
                "date": {"start": date.today().isoformat()}
            },
        }
    }

    # Adiciona campos opcionais apenas se preenchidos
    if cidade:
        payload["properties"][CAMPOS["cidade"]] = {
            "rich_text": [{"text": {"content": cidade[:200]}}]
        }
    if whatsapp:
        payload["properties"][CAMPOS["whatsapp"]] = {
            "phone_number": whatsapp
        }
    if segmento:
        payload["properties"][CAMPOS["segmento"]] = {
            "select": {"name": segmento[:100]}
        }
    if instagram:
        payload["properties"][CAMPOS["instagram"]] = {
            "url": instagram
        }
    if responsavel:
        payload["properties"][CAMPOS["responsavel"]] = {
            "rich_text": [{"text": {"content": responsavel[:200]}}]
        }
    if rodada:
        payload["properties"][CAMPOS["rodada"]] = {
            "select": {"name": rodada[:100]}
        }
    if link_maps:
        payload["properties"][CAMPOS["link_maps"]] = {
            "url": link_maps
        }
    if observacoes:
        payload["properties"][CAMPOS["observacoes"]] = {
            "rich_text": [{"text": {"content": observacoes[:2000]}}]
        }

    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=15,
    )

    if response.status_code == 200:
        return True
    else:
        # Mostra o erro detalhado para facilitar debug
        erro = response.json().get("message", response.text)
        print(f"  ⚠️  Notion API erro {response.status_code}: {erro}")
        return False


# ──────────────────────────────────────────────
# VERIFICAÇÃO DE DUPLICATA
# ──────────────────────────────────────────────

def ja_existe(nome_empresa: str) -> bool:
    """
    Consulta o Notion para checar se a empresa já foi cadastrada.
    Evita duplicatas quando você roda o script várias vezes
    no mesmo nicho ou mesma cidade.
    """
    if not NOTION_TOKEN or not DATABASE_ID:
        return False

    payload = {
        "filter": {
            "property": CAMPOS["empresa"],
            "title": {"equals": nome_empresa}
        }
    }

    try:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers=HEADERS,
            data=json.dumps(payload),
            timeout=10,
        )
        if response.status_code == 200:
            return len(response.json().get("results", [])) > 0
    except Exception:
        pass

    return False


# ──────────────────────────────────────────────
# ENVIO DE LOTE COM PROTEÇÃO CONTRA DUPLICATA
# ──────────────────────────────────────────────

def enviar_lote_para_notion(df, nicho: str, rodada: str = "") -> None:
    """
    Recebe o DataFrame gerado pelo scraper e envia apenas os leads
    SEM SITE para o Notion, com verificação de duplicata.

    Args:
        df:     DataFrame retornado pela função scrape_google_maps()
        nicho:  Nicho buscado (ex: "Dentistas") — vira o campo Segmento
        rodada: Identificador do lote (ex: "Lote 01 - Março")
    """
    # Filtra apenas os leads sem site — são os seus alvos
    sem_site = df[df["Status do Site"] == "Não Tem"].copy()

    if sem_site.empty:
        print("\n  ℹ️  Nenhum lead sem site encontrado para enviar ao Notion.")
        return

    total  = len(sem_site)
    ok     = 0
    pulado = 0
    erro   = 0

    print(f"\n📤 Enviando {total} lead(s) sem site para o Notion...\n")

    for idx, (_, row) in enumerate(sem_site.iterrows(), 1):
        nome = row.get("Nome", "").strip()
        if not nome:
            continue

        print(f"  [{idx:03}/{total}] {nome}", end=" ")

        # Checa duplicata antes de inserir
        if ja_existe(nome):
            print("→ ⚠️  já existe, pulando.")
            pulado += 1
            continue

        # Extrai cidade do endereço (pega a parte após a última vírgula)
        endereco = row.get("Endereço", "")
        cidade_extraida = _extrair_cidade(endereco)

        sucesso = adicionar_lead(
            empresa   = nome,
            cidade    = cidade_extraida or endereco,
            whatsapp  = row.get("Telefone", ""),
            segmento  = nicho,
            link_maps = row.get("Link do Maps", ""),
            rodada    = rodada,
            observacoes = f"Endereço completo: {endereco}" if endereco else "",
        )

        if sucesso:
            print("→ ✅ adicionado!")
            ok += 1
        else:
            print("→ ❌ erro.")
            erro += 1

        # Respeita o rate limit da API do Notion (3 req/s)
        time.sleep(0.4)

    print(f"\n{'─'*45}")
    print(f"  ✅ Adicionados:  {ok}")
    print(f"  ⚠️  Já existiam: {pulado}")
    print(f"  ❌ Com erro:     {erro}")
    print(f"{'─'*45}\n")


def _extrair_cidade(endereco: str) -> str:
    """
    Tenta extrair só a cidade de um endereço completo.
    Ex: 'Rua das Flores, 123, Jardim Paulista, São Paulo - SP, 01310-000'
    → 'São Paulo - SP'
    """
    if not endereco:
        return ""
    # Padrão: cidade - UF (ex: São Paulo - SP ou São Paulo, SP)
    match = re.search(r'([A-ZÀ-Ú][a-zà-ú\s]+)\s*[-,]\s*([A-Z]{2})', endereco)
    if match:
        return f"{match.group(1).strip()} - {match.group(2)}"
    # Fallback: retorna os últimos 2 fragmentos do endereço
    partes = [p.strip() for p in endereco.split(",") if p.strip()]
    return partes[-2] if len(partes) >= 2 else endereco
