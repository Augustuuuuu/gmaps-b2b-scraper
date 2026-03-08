# gmaps-b2b-scraper

Ferramenta de web scraping para prospecção B2B via Google Maps. Extrai dados estruturados de estabelecimentos comerciais e classifica leads por prioridade com base na presença (ou ausência) de website cadastrado.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.40%2B-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=flat-square&logo=pandas&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Stars](https://img.shields.io/github/stars/seu-usuario/gmaps-b2b-scraper?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/seu-usuario/gmaps-b2b-scraper?style=flat-square)

---

## Como funciona

O script abre o Google Maps via URL com a query `{nicho} em {cidade}`, realiza scroll automático no feed lateral para carregar todos os resultados via lazy-loading e, para cada estabelecimento, navega até o perfil individual para extrair os dados. O output é uma planilha `.xlsx` com os leads ordenados por ausência de website.

```
input: nicho + cidade
    → busca via URL do Maps
    → scroll automático do feed (lazy-load)
    → extração por perfil: nome · telefone · endereço · website
    → output: leads_*.xlsx (sem site no topo)
```

---

## Stack

| Lib            | Função                                     |
| -------------- | -------------------------------------------- |
| `playwright` | Automação do navegador (Chromium headless) |
| `pandas`     | Estruturação e exportação dos dados      |
| `openpyxl`   | Formatação da planilha `.xlsx`           |

---

## Instalação

```bash
git clone https://github.com/seu-usuario/gmaps-b2b-scraper.git
cd gmaps-b2b-scraper

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
playwright install chromium
```

---

## Uso

```bash
python gmaps_scraper.py
```

```
📌 Digite o nicho de mercado: Dentistas
🏙️  Digite a cidade/região: São Paulo SP
🖥️  Rodar em modo headless? (S/N): S
```

O arquivo gerado segue o padrão `leads_{nicho}_{cidade}_{timestamp}.xlsx`.

---

## Output

| Coluna             | Descrição                   |
| ------------------ | ----------------------------- |
| `Nome`           | Nome do estabelecimento       |
| `Status do Site` | `Não Tem` / `Tem`        |
| `Telefone`       | Número extraído do perfil   |
| `Endereço`      | Endereço completo            |
| `Website`        | URL do site (quando presente) |
| `Link do Maps`   | URL direta para o perfil      |

Leads com `Status do Site = Não Tem` são ordenados no topo e destacados em vermelho na planilha — são os contatos prioritários para oferta de serviços digitais.

---

## Configuração

Constantes no topo de `gmaps_scraper.py`:

```python
TIMEOUT_PADRAO = 10_000   # ms — aumente em conexões lentas
PAUSA_SCROLL   = 1.5      # segundos entre cada scroll do feed
MAX_RESULTADOS = 100      # None = sem limite
```

---

## Seletores CSS

Os seletores ficam documentados em bloco próprio no script. O Google Maps atualiza o layout com frequência — se a coleta parar de funcionar, esse é o primeiro lugar a revisar.

```python
SEL_NOME      = 'h1.DUwDvf'
SEL_ENDERECO  = 'button[data-item-id="address"]'
SEL_TELEFONE  = 'button[data-item-id^="phone:"]'
SEL_WEBSITE   = 'a[data-item-id="authority"]'
SEL_FEED      = 'div[role="feed"]'
```

**Para atualizar:** `F12` no Chrome → inspecionar o elemento → `Copy selector`.

---

## Roadmap

- [ ] Exportação direta para Google Sheets
- [ ] Modo batch (múltiplos nichos/cidades em sequência)
- [ ] Suporte a proxy rotativo
- [ ] Interface CLI com `argparse` (sem modo interativo)
- [ ] Integração com CRMs via API (HubSpot, RD Station)

---

## Contributing

Pull requests são bem-vindos. Para mudanças maiores, abra uma issue primeiro descrevendo o que você quer alterar.

### Setup de desenvolvimento

```bash
git clone https://github.com/augustuuuuu/gmaps-b2b-scraper.git
cd gmaps-b2b-scraper
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Fluxo de contribuição

```bash
# 1. Fork + clone do seu fork
# 2. Crie uma branch descritiva
git checkout -b feat/exportar-google-sheets

# 3. Faça as alterações e commit seguindo Conventional Commits
git commit -m "feat: adiciona exportação para Google Sheets via API"

# 4. Push e abra o PR apontando para main
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

### Reportando bugs

Abra uma [issue](https://github.com/seu-usuario/gmaps-b2b-scraper/issues) com:

- Versão do Python e SO
- Nicho e cidade usados na busca
- Trecho do traceback (se houver)

---

## Aviso legal

Uso destinado a fins educacionais e prospecção comercial legítima. Respeite os [Termos de Serviço do Google](https://policies.google.com/terms) e a [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm). Os dados coletados são de domínio público no Google Maps.

---

## Licença

[MIT](LICENSE)
