# 🗺️ Google Maps B2B Lead Scraper

Ferramenta de prospecção automatizada que coleta dados de empresas diretamente do Google Maps, classifica os leads por prioridade e sincroniza tudo com o Notion — pronta para uso em operações de vendas B2B.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=flat-square&logo=pandas&logoColor=white)
![Notion API](https://img.shields.io/badge/Notion-API-000000?style=flat-square&logo=notion&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 O que esse projeto faz?

Imagine que você quer encontrar **todos os dentistas de São Paulo** ou **todas as dedetizadoras de Brasília** e saber quais deles **não têm site** — esses são os clientes ideais para quem vende criação de sites, marketing digital ou qualquer serviço B2B.

Esse script faz exatamente isso de forma automática:

1. **Abre o Google Maps** com a busca que você digitar (ex: "Salões de beleza em Brasília DF")
2. **Rola a página** para carregar todos os resultados (o Maps usa lazy-loading, ou seja, carrega aos poucos conforme você desce)
3. **Entra no perfil de cada empresa** e extrai: nome, telefone, endereço, website e link direto no Maps
4. **Classifica os leads**: quem **não tem site** vai para o topo da lista — esses são os leads prioritários
5. **Envia os leads automaticamente para o Notion** (opcional), criando cards organizados em um CRM pessoal
6. **Gera formulários prontos** para criação de sites, com dados pré-preenchidos para colar no Claude.ai

---

## 🧠 Por que isso é útil?

Se você trabalha com vendas, prospecção comercial ou oferece serviços digitais (sites, landing pages, marketing), precisa de **leads qualificados** — e encontrar empresas que nem site têm é praticamente achar ouro: elas precisam do seu serviço e provavelmente ninguém ainda ofereceu.

O processo manual seria: abrir o Google Maps, clicar em cada empresa, anotar os dados, verificar se tem site... Isso levaria **horas**. Com esse script, você coleta **100 leads em minutos**.

---

## ⚙️ Como funciona por baixo dos panos

```
Você digita: nicho + cidade
       │
       ▼
┌─────────────────────────────────────────────┐
│  1. Monta a URL de busca do Google Maps     │
│     "Dentistas em São Paulo SP"             │
│                                             │
│  2. Abre um navegador Chromium automatizado │
│     (invisível ou visível, você escolhe)    │
│                                             │
│  3. Faz scroll automático no feed lateral   │
│     para carregar todos os resultados       │
│                                             │
│  4. Coleta os links de cada empresa         │
│                                             │
│  5. Entra em cada perfil e extrai:          │
│     • Nome                                  │
│     • Telefone                              │
│     • Endereço                              │
│     • Website (tem ou não tem)              │
│     • Link direto do Maps                   │
│                                             │
│  6. Ordena: sem site primeiro (prioridade)  │
│                                             │
│  7. (Opcional) Envia para o Notion          │
│                                             │
│  8. Gera formulários para criação de sites  │
└─────────────────────────────────────────────┘
       │
       ▼
Resultado: lista de leads + formulários prontos
```

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Para que serve |
|---|---|
| **Python 3.9+** | Linguagem principal do projeto |
| **Playwright** | Controla um navegador Chromium real de forma automatizada (é o que "clica" e "rola" o Google Maps) |
| **Pandas** | Organiza os dados em tabelas e permite filtrar/ordenar os leads |
| **Requests** | Faz as chamadas HTTP para a API do Notion |
| **python-dotenv** | Lê as credenciais do Notion a partir de um arquivo `.env` seguro |

---

## 📂 Estrutura do projeto

```
gmaps-b2b-scraper/
├── Scraping/
│   ├── scraper_com_notion.py   ← Script principal (roda esse aqui)
│   └── notion_sync.py          ← Módulo de integração com o Notion
├── Formularios/                ← Formulários gerados (criada automaticamente)
├── requirements.txt            ← Dependências do Python
├── .env                        ← Suas credenciais do Notion (não vai pro GitHub)
├── .gitignore                  ← Arquivos ignorados pelo Git
├── LICENSE                     ← Licença MIT
└── README.md                   ← Você está aqui
```

---

## 🚀 Instalação

### Pré-requisitos
- Python 3.9 ou superior instalado
- Git instalado

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/Augustuuuuu/gmaps-b2b-scraper.git
cd gmaps-b2b-scraper

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv

# No Windows:
venv\Scripts\activate

# No Linux/Mac:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale o navegador Chromium para o Playwright
playwright install chromium
```

---

## ▶️ Como usar

```bash
cd Scraping
python scraper_com_notion.py
```

O script vai te fazer algumas perguntas:

```
📌 Digite o nicho de mercado (ex: Dentistas): Dedetizadora
🏙️  Digite a cidade/região (ex: Brasília DF): Brasília DF
🖥️  Rodar em modo invisível/headless? (S/N) [padrão: S]: S
📋 Enviar leads sem site direto para o Notion? (S/N) [padrão: S]: N
```

> **Modo headless** = o navegador roda "invisível", sem abrir janela. Se quiser ver o navegador funcionando em tempo real, digite `N`.

Ao final, você verá um resumo assim:

```
📊  RESUMO DA PROSPECÇÃO
═══════════════════════════════════════════════
  🔍  Busca:              Dedetizadora em Brasília DF
  📋  Total de leads:     67
  🔴  Sem website:        26  ← LEADS PRIORITÁRIOS
  🟢  Com website:        41
  📞  Com telefone:       62
═══════════════════════════════════════════════
```

---

## 📊 O que é extraído de cada empresa

| Campo | Descrição | Exemplo |
|---|---|---|
| **Nome** | Nome do estabelecimento no Maps | `Império Dedetização Brasília DF` |
| **Status do Site** | Se tem ou não tem website cadastrado | `Não Tem` / `Tem` |
| **Telefone** | Número de telefone do perfil | `(61) 99854-9918` |
| **Endereço** | Endereço completo | `Brasília - DF` |
| **Website** | URL do site (quando existe) | `https://exemplo.com.br` |
| **Link do Maps** | Link direto para o perfil da empresa no Maps | URL do Google Maps |

> Os leads com **"Não Tem"** no status do site são colocados **no topo da lista** — são os mais valiosos para prospecção.

---

## 📋 Integração com o Notion (opcional)

O script pode enviar os leads sem site automaticamente para uma base de dados no Notion, criando um CRM pessoal com etapas de funil de vendas.

### Como configurar

**1. Crie uma integração no Notion:**
- Acesse [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Clique em "New integration"
- Dê um nome (ex: "LeadScraper") e copie o **Internal Integration Token**

**2. Descubra o ID da sua base de dados:**
- Abra sua base de leads no navegador
- A URL será algo como: `https://www.notion.so/SEU-NOME/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...`
- Os 32 caracteres entre a última `/` e o `?` são o **DATABASE_ID**

**3. Conecte a integração à base:**
- Na sua base do Notion, clique em `...` → `Connections` → selecione sua integração

**4. Configure o `.env`:**

Crie um arquivo `.env` na raiz do projeto com:

```env
NOTION_TOKEN=secret_xxxxxxxxxxxx
DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Campos criados no Notion

Cada lead vira um card com:

| Campo | Tipo | Valor padrão |
|---|---|---|
| Empresa | Title | Nome do estabelecimento |
| Segmento | Select | Nicho buscado |
| Cidade | Text | Extraído do endereço |
| WhatsApp | Phone | Telefone do perfil |
| Etapa | Select | 🔍 Prospectado |
| Temperatura | Select | ❄️ Frio |
| Data 1° Contato | Date | Data da coleta |
| Link Maps | URL | Link direto do Maps |
| Rodada | Select | Identificador do lote |

> O sistema **verifica duplicatas** automaticamente — se você rodar o script duas vezes na mesma cidade, os leads que já existem no Notion não serão duplicados.

---

## 📝 Geração automática de formulários

Para cada lead **sem site**, o script gera um formulário pré-preenchido pronto para ser colado no [Claude.ai](https://claude.ai/) para criação automática de landing pages.

Exemplo de formulário gerado:

```
FORMULÁRIO — Novo Site de Serviços
──────────────────────────────────────────
NOVA EMPRESA:
Nome:        Império Dedetização Brasília DF
Segmento:    Dedetizadora
WhatsApp:    (61) 99854-9918
Endereço:    Brasília - DF
Cores:       #E21F26, #1a1a1a
Serviços:
* Dedetização
* Desratização
* Descupinização
...
```

O sistema reconhece automaticamente o nicho e preenche:
- **Paleta de cores** adequada ao segmento
- **Lista de serviços** típicos do ramo
- **CNAE** e **certificações** relevantes

### Nichos com preenchimento automático

O sistema já tem configurações prontas para: dedetizadoras, eletricistas, encanadores, empresas de limpeza, pintores, ar-condicionado, dentistas e academias. Para outros nichos, usa um template genérico.

Os formulários são salvos na pasta `Formularios/` com o padrão:
```
formularios_{nicho}_{cidade}_{data_hora}.txt
```

---

## ⚙️ Configurações avançadas

No topo do arquivo `scraper_com_notion.py`, você pode ajustar:

```python
TIMEOUT_PADRAO = 8_000    # Timeout em ms (aumente se a internet for lenta)
PAUSA_SCROLL   = 0.8      # Segundos entre cada scroll
PAUSA_CLIQUE   = 1.0      # Segundos de espera após clicar em um perfil
MAX_RESULTADOS = 100      # Limite de empresas a coletar (None = sem limite)
```

### Seletores CSS

O Google Maps muda seu layout periodicamente. Se o script parar de funcionar, provavelmente algum seletor CSS ficou desatualizado. Eles ficam no topo do script:

```python
SEL_NOME      = 'h1.DUwDvf'
SEL_ENDERECO  = 'button[data-item-id="address"]'
SEL_TELEFONE  = 'button[data-item-id^="phone:"]'
SEL_WEBSITE   = 'a[data-item-id="authority"]'
```

**Para atualizar:** abra o Google Maps no Chrome, aperte `F12`, inspecione o elemento e copie o seletor.

---

## 🤝 Contribuindo

Pull requests são bem-vindos! Para mudanças maiores, abra uma issue primeiro.

```bash
# 1. Fork + clone do seu fork
# 2. Crie uma branch descritiva
git checkout -b feat/exportar-google-sheets

# 3. Faça as alterações e commit
git commit -m "feat: adiciona exportação para Google Sheets"

# 4. Push e abra o PR
git push origin feat/exportar-google-sheets
```

### Convenção de commits

```
feat:     nova funcionalidade
fix:      correção de bug
refactor: refatoração sem mudança de comportamento
docs:     alteração em documentação
chore:    manutenção (deps, config, etc.)
```

---

## ⚠️ Aviso legal

Este projeto é destinado a **fins educacionais e prospecção comercial legítima**. Os dados extraídos são informações públicas disponíveis no Google Maps. Ao utilizar esta ferramenta, respeite os [Termos de Serviço do Google](https://policies.google.com/terms) e a [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

---

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE). Sinta-se livre para usar, modificar e distribuir.
