"""
=============================================================================
  Google Maps B2B Lead Scraper  ·  com integração Notion
  Descrição: Extrai dados de estabelecimentos no Google Maps, identifica
             leads prioritários (sem website) e os envia automaticamente
             para o Notion. Gera também um formulário preenchido para
             criação de sites, pronto para usar no Claude.ai.

  INSTALAÇÃO DAS DEPENDÊNCIAS:
  pip install playwright pandas requests python-dotenv
  playwright install chromium

  CONFIGURAÇÃO DO NOTION (.env na mesma pasta):
  NOTION_TOKEN=secret_xxxxxxxxxxxx
  DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
=============================================================================
"""

import time
import re
import sys
import os
from datetime import datetime
from urllib.parse import quote

# ── Integração com Notion ────────────────────────────────────────────────────
try:
    from notion_sync import enviar_lote_para_notion
    NOTION_DISPONIVEL = True
except ImportError:
    NOTION_DISPONIVEL = False
    print("⚠️  notion_sync.py não encontrado — scraping funcionará normalmente,")
    print("   mas os leads NÃO serão enviados ao Notion.\n")

# ── Playwright ───────────────────────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("❌ Playwright não encontrado. Execute: pip install playwright && playwright install chromium")
    sys.exit(1)

import pandas as pd


# ============================================================================
#  CONFIGURAÇÕES GLOBAIS
# ============================================================================

TIMEOUT_PADRAO = 8_000
PAUSA_SCROLL   = 0.8
PAUSA_CLIQUE   = 1.0
PAUSA_DETALHE  = 0.5
MAX_RESULTADOS = 100

# ============================================================================
#  SELETORES CSS
# ============================================================================

SEL_LISTA_RESULTADOS = 'div[role="feed"]'
SEL_ITEM_LISTA       = 'div[role="feed"] > div > div[jsaction]'
SEL_LINK_ITEM        = 'a[href*="/maps/place/"]'
SEL_NOME             = 'h1.DUwDvf'
SEL_ENDERECO         = 'button[data-item-id="address"]'
SEL_TELEFONE         = 'button[data-item-id^="phone:"]'
SEL_WEBSITE          = 'a[data-item-id="authority"]'


# ============================================================================
#  FUNÇÕES DE SCRAPING
# ============================================================================

def limpar_texto(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto.strip())


def obter_link_maps(page) -> str:
    url   = page.url
    match = re.search(r'(https://www\.google\.com/maps/place/[^?]+)', url)
    return match.group(1) if match else url


def extrair_detalhes(page) -> dict:
    dados = {
        "Nome":           "",
        "Endereço":       "",
        "Telefone":       "",
        "Website":        "",
        "Status do Site": "",
        "Link do Maps":   "",
    }

    try:
        elemento_nome  = page.wait_for_selector(SEL_NOME, timeout=TIMEOUT_PADRAO)
        dados["Nome"]  = limpar_texto(elemento_nome.inner_text())
    except PlaywrightTimeoutError:
        return dados

    try:
        el_end = page.query_selector(SEL_ENDERECO)
        if el_end:
            dados["Endereço"] = limpar_texto(el_end.get_attribute("aria-label") or el_end.inner_text())
            dados["Endereço"] = re.sub(r'^Endereço:\s*', '', dados["Endereço"])
    except Exception:
        pass

    try:
        el_tel = page.query_selector(SEL_TELEFONE)
        if el_tel:
            aria = el_tel.get_attribute("aria-label") or ""
            dados["Telefone"] = re.sub(r'^Telefone:\s*', '', aria).strip()
    except Exception:
        pass

    try:
        el_site = page.query_selector(SEL_WEBSITE)
        if el_site:
            href      = el_site.get_attribute("href") or ""
            match_url = re.search(r'[?&](?:q|url)=([^&]+)', href)
            if match_url:
                from urllib.parse import unquote
                dados["Website"] = unquote(match_url.group(1))
            else:
                dados["Website"] = href
    except Exception:
        pass

    dados["Status do Site"] = "Não Tem" if not dados["Website"] else "Tem"
    dados["Link do Maps"]   = obter_link_maps(page)

    return dados


def scroll_lista(page, n_scrolls: int = 10) -> None:
    try:
        feed = page.wait_for_selector(SEL_LISTA_RESULTADOS, timeout=TIMEOUT_PADRAO)
    except PlaywrightTimeoutError:
        return

    for i in range(n_scrolls):
        page.evaluate("(el) => el.scrollBy(0, el.scrollHeight)", feed)
        time.sleep(PAUSA_SCROLL)


def coletar_links_visiveis(page) -> list[str]:
    links = page.query_selector_all(f'{SEL_ITEM_LISTA} {SEL_LINK_ITEM}')
    urls  = []
    for link in links:
        href = link.get_attribute("href")
        if href and "/maps/place/" in href:
            url_limpa = href.split("?")[0]
            if url_limpa not in urls:
                urls.append(url_limpa)
    return urls


def scrape_google_maps(nicho: str, cidade: str, headless: bool = True) -> pd.DataFrame:
    query     = f"{nicho} em {cidade}"
    url_busca = f"https://www.google.com/maps/search/{quote(query)}"
    resultados = []

    print(f"\n{'=' * 55}")
    print(f"  🗺️  INICIANDO SCRAPING")
    print(f"{'=' * 55}")
    print(f"  🔍  Busca:    {query}")
    print(f"  🖥️  Headless: {'Sim' if headless else 'Não'}")
    print(f"{'=' * 55}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=50 if not headless else 0,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
        )
        page = context.new_page()

        page.goto(url_busca, wait_until="domcontentloaded", timeout=30_000)
        time.sleep(3)

        try:
            botao_aceitar = page.query_selector('button[aria-label*="Aceitar"]')
            if botao_aceitar:
                botao_aceitar.click()
                time.sleep(1)
        except Exception:
            pass

        todos_links       = set()
        rodadas_sem_novos = 0
        MAX_RODADAS_SEM_NOVOS = 3

        while True:
            scroll_lista(page, n_scrolls=5)
            links_atuais = coletar_links_visiveis(page)
            novos        = set(links_atuais) - todos_links

            if not novos:
                rodadas_sem_novos += 1
                if rodadas_sem_novos >= MAX_RODADAS_SEM_NOVOS:
                    break
            else:
                rodadas_sem_novos = 0
                todos_links.update(novos)

            if MAX_RESULTADOS and len(todos_links) >= MAX_RESULTADOS:
                break

        lista_links = list(todos_links)[:MAX_RESULTADOS]
        print(f"  📋 {len(lista_links)} estabelecimentos encontrados. Extraindo dados...\n")

        for idx, link in enumerate(lista_links, start=1):
            print(f"  ⏳ Progresso: {idx}/{len(lista_links)}  ({int(idx/len(lista_links)*100)}%)", end="\r")
            try:
                page.goto(link, wait_until="domcontentloaded", timeout=20_000)
                time.sleep(PAUSA_DETALHE)
                page.wait_for_selector(SEL_NOME, timeout=TIMEOUT_PADRAO)
                time.sleep(PAUSA_CLIQUE)

                dados = extrair_detalhes(page)
                if dados["Nome"]:
                    resultados.append(dados)

            except PlaywrightTimeoutError:
                pass
            except Exception:
                pass

            time.sleep(0.2)

        print(f"  ✅ Extração concluída: {len(resultados)} leads coletados.          \n")
        browser.close()

    if not resultados:
        print("\n⚠️  Nenhum resultado foi coletado.")
        return pd.DataFrame(columns=["Nome", "Status do Site", "Telefone", "Endereço", "Website", "Link do Maps"])

    df = pd.DataFrame(resultados)
    df = df[["Nome", "Status do Site", "Telefone", "Endereço", "Website", "Link do Maps"]]
    df = df.sort_values(
        by="Status do Site",
        key=lambda x: x.map({"Não Tem": 0, "Tem": 1}),
        ascending=True
    ).reset_index(drop=True)

    return df


def exibir_resumo(df: pd.DataFrame, nicho: str, cidade: str) -> None:
    total        = len(df)
    sem_site     = len(df[df["Status do Site"] == "Não Tem"])
    com_site     = len(df[df["Status do Site"] == "Tem"])
    com_telefone = len(df[df["Telefone"] != ""])

    print("\n" + "=" * 55)
    print("  📊  RESUMO DA PROSPECÇÃO")
    print("=" * 55)
    print(f"  🔍  Busca:              {nicho} em {cidade}")
    print(f"  📋  Total de leads:     {total}")
    print(f"  🔴  Sem website:        {sem_site}  ← LEADS PRIORITÁRIOS")
    print(f"  🟢  Com website:        {com_site}")
    print(f"  📞  Com telefone:       {com_telefone}")
    print("=" * 55)

    if sem_site > 0:
        print(f"\n  💡  TOP 5 LEADS QUENTES (sem site):\n")
        top = df[df["Status do Site"] == "Não Tem"].head(5)
        for _, row in top.iterrows():
            print(f"     • {row['Nome']}")
            print(f"       📞 {row['Telefone'] or 'Telefone não disponível'}")
            print(f"       📍 {row['Endereço'] or 'Endereço não disponível'}\n")


# ============================================================================
#  GERADOR DE FORMULÁRIOS
#  Para cada lead sem website, gera um formulário preenchido com os dados
#  disponíveis, pronto para colar no Claude.ai e criar a landing page.
# ============================================================================

# Mapeamento de nichos para paletas e serviços padrão
_CONFIGS_NICHO = {
    "dedetiz": {
        "cor_primaria": "#E21F26", "cor_secundaria": "#1a1a1a",
        "servicos": ["Dedetização", "Desratização", "Descupinização", "Sanitização", "Controle de pombos", "Desinsetização"],
        "cnae": "8122-2/00 – Imunização, higienização, desinfecção e dedetização",
        "certificacoes": "Produtos certificados ANVISA, Garantia de 90 dias, Equipe treinada",
    },
    "eletric": {
        "cor_primaria": "#F5A623", "cor_secundaria": "#b37a00",
        "servicos": ["Instalação elétrica", "Quadro de distribuição", "Iluminação LED", "Tomadas e interruptores", "Laudo elétrico NR-10"],
        "cnae": "4321-5/00 – Instalação e manutenção elétrica",
        "certificacoes": "Registro CREA, NR-10, Garantia técnica em contrato",
    },
    "encanament|desentupid|hidraul": {
        "cor_primaria": "#1E90FF", "cor_secundaria": "#0a5fad",
        "servicos": ["Desentupimento", "Vazamentos", "Instalação hidráulica", "Limpeza de caixas d'água", "Conserto de torneiras"],
        "cnae": "4322-3/01 – Instalações hidráulicas, sanitárias e de gás",
        "certificacoes": "Atendimento emergencial, Garantia nos serviços, Orçamento grátis",
    },
    "limpez|higieniz": {
        "cor_primaria": "#1a4fa0", "cor_secundaria": "#4a90e2",
        "servicos": ["Limpeza residencial", "Limpeza comercial", "Limpeza pós-obra", "Higienização de sofás", "Limpeza de vidros"],
        "cnae": "8121-4/00 – Limpeza em prédios e domicílios",
        "certificacoes": "Produtos certificados ANVISA, Equipe uniformizada, Satisfação garantida",
    },
    "pintur": {
        "cor_primaria": "#FF6B35", "cor_secundaria": "#c44a1a",
        "servicos": ["Pintura residencial", "Pintura comercial", "Textura", "Grafiato", "Pintura externa e interna"],
        "cnae": "4330-4/04 – Serviços de pintura de edifícios em geral",
        "certificacoes": "Acabamento impecável, Prazo garantido, Orçamento grátis",
    },
    "ar.condicion|refriger|climat": {
        "cor_primaria": "#0ea5e9", "cor_secundaria": "#0369a1",
        "servicos": ["Instalação de ar-condicionado", "Manutenção preventiva", "Limpeza de filtros", "Recarga de gás", "Desinstalação e reinstalação"],
        "cnae": "4322-3/02 – Instalação de sistemas de ar-condicionado",
        "certificacoes": "Técnico certificado, Todas as marcas, Garantia no serviço",
    },
    "dentist|odont": {
        "cor_primaria": "#2E86AB", "cor_secundaria": "#1a5f7a",
        "servicos": ["Clareamento dental", "Ortodontia", "Implantes", "Limpeza", "Restaurações"],
        "cnae": "8630-5/01 – Atividade médica ambulatorial com recursos para realização de procedimentos cirúrgicos",
        "certificacoes": "CRO ativo, Ambiente esterilizado, Parcelamento facilitado",
    },
    "academi|fitness|muscula": {
        "cor_primaria": "#FF3D00", "cor_secundaria": "#c42d00",
        "servicos": ["Musculação", "Funcional", "Spinning", "Yoga", "Personal trainer"],
        "cnae": "9313-1/00 – Atividades de condicionamento físico",
        "certificacoes": "Professores qualificados, Ambiente climatizado, Avaliação física gratuita",
    },
}

def _inferir_config(nicho: str) -> dict:
    """Retorna config de design/serviços baseada no nicho detectado."""
    nicho_lower = nicho.lower()
    for padrao, config in _CONFIGS_NICHO.items():
        if re.search(padrao, nicho_lower):
            return config
    # Fallback genérico
    return {
        "cor_primaria": "#2563EB", "cor_secundaria": "#1e40af",
        "servicos": [f"Serviços de {nicho}", "Atendimento especializado", "Orçamento grátis"],
        "cnae": "Consultar contador",
        "certificacoes": "Equipe qualificada, Preço justo, Garantia nos serviços",
    }


def _extrair_cidade_curta(endereco: str, cidade_busca: str) -> str:
    """Tenta extrair cidade - UF do endereço; fallback para cidade da busca."""
    if endereco:
        match = re.search(r'([A-ZÀ-Ú][a-zà-ú\s]+)\s*[-,]\s*([A-Z]{2})', endereco)
        if match:
            return f"{match.group(1).strip()} - {match.group(2)}"
    return cidade_busca


def gerar_formulario(lead: dict, nicho: str, cidade: str) -> str:
    """
    Gera o formulário preenchido para um lead sem site.
    Os campos que não temos são marcados como [PREENCHER].
    """
    config = _inferir_config(nicho)

    # Número formatado para exibição
    tel = lead.get("Telefone", "").strip()
    # Remove DDI se já tiver, mantém formato limpo
    tel_display = tel if tel else "[PREENCHER]"

    endereco = lead.get("Endereço", "").strip()
    cidade_display = _extrair_cidade_curta(endereco, cidade)
    if endereco and cidade_display not in endereco:
        cidade_display = f"{cidade_display} · {endereco}"

    servicos_fmt = "\n".join(f"* {s}" for s in config["servicos"])

    formulario = f"""FORMULÁRIO — Novo Site de Serviços
Preencha e envie no projeto do Claude.ai
──────────────────────────────────────────
NOVA EMPRESA:
Nome:        {lead['Nome']}
Segmento:    {nicho}
WhatsApp:    {tel_display}
Endereço:    {cidade_display or '[PREENCHER]'}
Cores:       {config['cor_primaria']}, {config['cor_secundaria']}
Serviços:
{servicos_fmt}

Razão Social:   [PREENCHER]
CNPJ:           [PREENCHER]
Abertura:       [PREENCHER]
CNAE:           {config['cnae']}
Certificações:  {config['certificacoes']}
Logo:           SEM LOGO

Link Maps: {lead.get('Link do Maps', '')}
──────────────────────────────────────────"""

    return formulario


def salvar_formularios(df: pd.DataFrame, nicho: str, cidade: str) -> str | None:
    """
    Gera um arquivo .txt com os formulários de todos os leads sem site.
    Retorna o caminho do arquivo gerado.
    """
    sem_site = df[df["Status do Site"] == "Não Tem"]

    if sem_site.empty:
        return None

    pasta = "Formularios"
    os.makedirs(pasta, exist_ok=True)

    timestamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"formularios_{nicho.lower().replace(' ', '_')}_{cidade.lower().replace(' ', '_')}_{timestamp}.txt"
    caminho      = os.path.join(pasta, nome_arquivo)

    linhas = []
    linhas.append("=" * 55)
    linhas.append(f"  FORMULÁRIOS PARA CRIAÇÃO DE SITES")
    linhas.append(f"  Nicho: {nicho.upper()} | Cidade: {cidade.upper()}")
    linhas.append(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    linhas.append(f"  Total: {len(sem_site)} lead(s) sem site")
    linhas.append("=" * 55)
    linhas.append("")
    linhas.append("  COMO USAR:")
    linhas.append("  1. Copie um bloco de formulário abaixo")
    linhas.append("  2. Preencha os campos marcados com [PREENCHER]")
    linhas.append("  3. Cole no projeto do Claude.ai para gerar o site")
    linhas.append("")

    for idx, (_, row) in enumerate(sem_site.iterrows(), 1):
        lead = row.to_dict()
        linhas.append(f"{'─' * 55}")
        linhas.append(f"  LEAD #{idx:02} — {lead['Nome']}")
        linhas.append(f"{'─' * 55}")
        linhas.append("")
        linhas.append(gerar_formulario(lead, nicho, cidade))
        linhas.append("")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    return caminho


# ============================================================================
#  PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  🗺️   GOOGLE MAPS B2B LEAD SCRAPER  +  NOTION")
    print("=" * 55)

    nicho  = input("\n  📌 Digite o nicho de mercado (ex: Dentistas): ").strip()
    cidade = input("  🏙️  Digite a cidade/região (ex: Brasília DF): ").strip()

    if not nicho or not cidade:
        print("❌ Nicho e cidade são obrigatórios!")
        sys.exit(1)

    resposta_headless = input("\n  🖥️  Rodar em modo invisível/headless? (S/N) [padrão: S]: ").strip().upper()
    headless = resposta_headless != "N"

    # ── Pergunta sobre o Notion ──────────────────────────────────────────────
    usar_notion = False
    rodada_nome = ""

    if NOTION_DISPONIVEL:
        resp_notion = input("\n  📋 Enviar leads sem site direto para o Notion? (S/N) [padrão: S]: ").strip().upper()
        usar_notion = resp_notion != "N"

        if usar_notion:
            rodada_nome = input("  📦 Nome da rodada/lote (ex: Lote 01 - Março) [Enter para deixar em branco]: ").strip()
            print()

    try:
        df_leads = scrape_google_maps(nicho, cidade, headless=headless)

        if not df_leads.empty:
            exibir_resumo(df_leads, nicho, cidade)

            # ── ENVIO PARA O NOTION ──────────────────────────────────────────
            if usar_notion and NOTION_DISPONIVEL:
                enviar_lote_para_notion(
                    df     = df_leads,
                    nicho  = nicho,
                    rodada = rodada_nome,
                )

            # ── GERAÇÃO DE FORMULÁRIOS ───────────────────────────────────────
            sem_site = len(df_leads[df_leads["Status do Site"] == "Não Tem"])
            if sem_site > 0:
                print(f"\n  📝 Gerando formulários para {sem_site} lead(s) sem website...")
                arquivo_forms = salvar_formularios(df_leads, nicho, cidade)
                if arquivo_forms:
                    print(f"  ✅ Formulários salvos em: {arquivo_forms}")
                    print(f"  💡 Abra o arquivo, complete os campos [PREENCHER] e cole no Claude.ai!")
            else:
                print("\n  ℹ️  Nenhum lead sem site — formulários não gerados.")

        else:
            print("\n❌ Nenhum dado coletado. Verifique a busca e tente novamente.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)