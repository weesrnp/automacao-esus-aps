# 🚀 PROJETO AUTOMAÇÕES SISTEMAS - GUIA DE CONTINUAÇÃO E DOCUMENTAÇÃO TÉCNICA

> **Repositório Guarda-Chuva**: `Automações Sistemas`  
> **Módulo Atual**: Automação e-SUS PEC (CDS/RAS) no IPM Saúde  
> **Objetivo deste Documento**: Registrar tudo o que foi desenvolvido, explicar as soluções técnicas criadas e fornecer o modelo padrão para criação de **novas automações** de outras rotinas no IPM Saúde e demais sistemas de gestão pública.

---

## 📁 1. ESTRUTURA RECOMENDADA PARA O REPOSITÓRIO

Ao organizar a pasta raiz `Automações Sistemas`, utilize a seguinte estrutura de diretórios:

```text
Automações Sistemas/
├── README.md                            <- Documentação principal do repositório
├── DOCUMENTO_CONTINUACAO_E_GUIA.md      <- Este guia de continuação e padrões
│
├── 01_ipm_esus_cds_ras/                 <- [CONCLUÍDO] Exportação de fichas e-SUS PEC
│   ├── automacao_ipm_esus.py            <- Script principal em produção
│   ├── main_automacao.py                <- Script limpo/genérico (versão GitHub)
│   ├── .env.example                     <- Modelo de credenciais
│   ├── EXECUTAR.bat                     <- Executar automação com 1 clique
│   ├── PARAR.bat                        <- Interromper automação com 1 clique
│   ├── ATUALIZAR.bat                    <- Puxar novidades do GitHub (git pull)
│   ├── test_notification_detection.py   <- Suíte de testes automatizados (16/16 OK)
│   └── MANUAL_SERVIDOR_AGENDADOR.txt    <- Guia de deploy no Agendador de Tarefas
│
└── 02_nova_rotina_ipm/                  <- [TEMPLATE PARA NOVAS ROTINAS]
    ├── .env.example
    ├── nova_automacao.py
    ├── EXECUTAR.bat
    └── PARAR.bat
```

---

## 🏛️ 2. O QUE JÁ FOI DESENVOLVEDO (MÓDULO e-SUS CDS/RAS)

Desenvolvemos e colocamos em produção uma automação completa em **Python + Playwright** para a rotina de exportação em lote de fichas do e-SUS PEC no **IPM Saúde**.

### 🌟 Principais Desafios Resolvidos e Soluções Aplicadas:

#### A. Manipulação de Dropdowns Customizados (Chosen.js)
- **Desafio**: O IPM Saúde utiliza a biblioteca `Chosen.js` no campo *"Tipo Exportação"*, que esconde o `<select id='tipo_exportacao'>` original e cria uma estrutura de `div` e `span` dinâmica.
- **Solução**: Em vez de simular cliques na interface (que falhavam com acentuação ou lentidão), executamos JavaScript nativo no iFrame (`frame.evaluate()`) alterando a propriedade `.value` do select oculto e disparando o evento jQuery `jQuery('#tipo_exportacao').trigger('chosen:updated')`.

#### B. Detecção Instantânea de Fichas "Sem Produção / Sem Registros"
- **Desafio**: Quando um tipo de ficha (ex: *Atendimento Domiciliar*) não tinha atendimentos gravados no dia, o IPM exibia uma notificação pop-up/toast no canto inferior direito e o script travava aguardando 60 segundos de timeout.
- **Solução**: Criamos a função `detectar_sem_producao()` que faz a varredura ativa de textos e seletores de alerta (`.toast`, `.noty_bar`, `.alert`, `#system_aviso_confirma`). Ao detectar o aviso, o robô fecha a notificação, clica em **Voltar** e avança para a próxima ficha em menos de **2 segundos**.

#### C. Prevenção de Duplicatas em Tempo Real
- **Desafio**: A automação roda 3x ao dia (12:05, 15:00, 17:05) e não pode gerar exportações repetidas no mesmo intervalo.
- **Solução**: Antes de incluir uma nova ficha, o script lê as colunas `Data`, `Hora` e `Tipo de Exportação` da própria tabela/grade exibida na tela do IPM. Se a ficha já foi gerada nos últimos 5 minutos, ela é marcada como `[PULADA]`.

#### D. Filtro de Período Diário Automatizado
- Preenchimento automático das caixas de texto `#eedatainicial` e `#eedatafinal` com a data do dia vigente no formato `DD/MM/YYYY`.

#### E. Seleção Multi-Unidades ESF
- Seleção automatizada via marcação de checkboxes na tabela de unidades (`Gigante`, `Pinho Fleck` e `UAPSF`).

#### F. Notificação em Tempo Real no Telegram
- Integração usando apenas a biblioteca nativa `urllib.request` do Python para enviar relatórios formatados em Markdown ao Telegram ao final de cada execução, sem precisar instalar pacotes externos pesados.

#### G. Controle Operacional Simplificado (`.bat`)
- `EXECUTAR.bat`: Apaga sinais de parada antigos e roda o script.
- `PARAR.bat`: Cria o sinal de parada `PARAR.txt` e mata os processos Python com segurança.
- `ATUALIZAR.bat`: Atualiza o repositório via `git pull origin master`.

---

## 📋 3. GUIA PASSO A PASSO PARA CRIAR NOVAS AUTOMAÇÕES NO IPM SAÚDE

Para criar uma automação para uma **nova rotina do IPM Saúde** (ex: Agendamento, Faturamento, Relatórios, Almoxarifado), siga o roteiro abaixo:

### Passo 1: Mapear os iFrames e Seletores (Fase de Diagnóstico)
O IPM Saúde funciona dentro de **iFrames encadeados**. Para descobrir os IDs e seletores dos campos da nova tela, crie um script rápido de diagnóstico usando Playwright:

```python
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://sua-prefeitura.exemplo.gov.br/saude/")
    
    # 1. Faça login e navegue até a tela desejada...
    
    # 2. Imprima os elementos de formulário de cada iFrame
    for idx, frame in enumerate(page.frames):
        print(f"\n--- FRAME {idx}: {frame.url} ---")
        selects = frame.query_selector_all("select, input, button")
        for s in selects:
            print(f"Tag: {s.evaluate('el => el.tagName')} | ID: {s.get_attribute('id')} | Name: {s.get_attribute('name')}")
```

### Passo 2: Utilizar o Template Padrão de Automação
Ao criar o arquivo Python da nova rotina (ex: `automacao_faturamento_ipm.py`), utilize a estrutura base com os seguintes auxiliares padronizados:

```python
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

def clicar_em_frames(page, seletor=None, texto=None, timeout_sec=5):
    """Procura e clica em um elemento em qualquer iFrame ativo da página."""
    start = time.time()
    while time.time() - start < timeout_sec:
        for frame in page.frames:
            try:
                elem = frame.query_selector(seletor) if seletor else frame.query_selector(f"text='{texto}'")
                if elem and elem.is_visible():
                    elem.click()
                    return True
            except:
                pass
        time.sleep(0.3)
    return False

def lidar_com_popups_e_notificacoes(page):
    """Fecha confirmações padrão do IPM Saúde."""
    clicar_em_frames(page, seletor="#system_aviso_confirma", timeout_sec=2)
    clicar_em_frames(page, seletor="#sobreposta-confirmacao-padrao-confirmar", timeout_sec=2)
    clicar_em_frames(page, texto="Sim", timeout_sec=2)
```

### Passo 3: Criar os Scripts `.bat` da Nova Rotina
Copie os modelos `EXECUTAR.bat` e `PARAR.bat` para a pasta da nova rotina, alterando apenas o nome do arquivo `.py` que será invocado.

---

## 🛠️ 4. BOAS PRÁTICAS E SEGURANÇA (MANUTENÇÃO)

1. **Credenciais**: NUNCA coloque senhas ou CPFs diretamente nos arquivos `.py`. Use sempre a leitura via `os.getenv()` do arquivo `.env`.
2. **Repositório Git Público**: Certifique-se de que o arquivo `.gitignore` ignore `.env`, pasta `exports/`, logs e imagens.
3. **Deploy no Servidor**: Para agendar no Windows Server, utilize o Agendador de Tarefas (`taskschd.msc`) apontando para o `python.exe` do ambiente `.venv` criado na máquina.

---

Este documento garante a continuidade do projeto e permite que qualquer membro da equipe desenvolva novas automações seguindo exatamente o mesmo padrão profissional!
