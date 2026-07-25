# 🏥 Automação de Exportação e-SUS PEC (Sistemas APS)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-Automation-green.svg)](https://playwright.dev/python/)

Robô de automação web em Python/Playwright desenvolvido para otimizar o fluxo diário de exportação das fichas do **e-SUS PEC / CDS / RAS** em sistemas de Atenção Primária à Saúde (APS) municipais.

---

## ✨ Recursos

- 🔄 **Exportação em Lote Automática**: Processa sequencialmente todas as fichas válidas do e-SUS PEC.
- 🏢 **Multi-Unidades ESF**: Marcação automatizada de múltiplas Unidades de Saúde (UBS/ESF).
- 📅 **Filtro Diário Dinâmico**: Preenchimento automático de `Data Inicial` e `Data Final` com o dia corrente.
- 🛑 **Prevenção de Duplicatas**: Consulta em tempo real na tela para evitar exportações duplicadas dentro de uma janela configurável (ex: 5 minutos).
- 📲 **Notificação via Telegram**: Envio de relatório formatado ao final da execução (sucesso, duplicatas e eventuais falhas).
- 📁 **Organização em Pastas**: Armazenamento dos relatórios e logs organizados por data (`./exports/YYYY-MM-DD/`).
- ⚡ **Modo Interruptível**: Atalho (`PARAR.bat`) para interromper o ciclo com 1 clique.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **Playwright** (Automação web headless e interação com iFrames/Dropdowns dinâmicos)
- **python-dotenv** (Gestão segura de credenciais)
- **Telegram Bot API** (Notificações em tempo real)

---

## 🚀 Como Usar

### 1. Clonar o Repositório
```bash
git clone https://github.com/weesrnp/automacao-esus-aps.git
cd automacao-esus-aps
```

### 2. Criar Ambiente Virtual e Instalar Dependências
```bash
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 3. Configurar Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e preencha suas credenciais:
```bash
cp .env.example .env
```
Edite o arquivo `.env`:
```env
SISTEMA_SAUDE_URL=https://sua-prefeitura.exemplo.gov.br/saude/
SISTEMA_SAUDE_USUARIO=seu_cpf_ou_usuario
SISTEMA_SAUDE_SENHA=sua_senha_aqui

# Opcional (Telegram)
TELEGRAM_BOT_TOKEN=seu_bot_token
TELEGRAM_CHAT_ID=seu_chat_id
```

### 4. Executar
- **Manual via Terminal**:
  ```bash
  python main_automacao.py
  ```
- **Windows (1 clique)**:
  Dê duplo clique no arquivo `EXECUTAR.bat`.

---

## 📄 Licença

Este projeto está sob a licença **MIT** - veja o arquivo [LICENSE](LICENSE) para mais detalhes. Livre para uso, modificação e distribuição na gestão pública de saúde.
