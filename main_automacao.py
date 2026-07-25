"""
Automação de Exportação em Lote - Sistemas de Atenção Primária à Saúde (APS / e-SUS PEC)
---------------------------------------------------------------------------------------
Projeto de automação web em Python/Playwright para sistemas municipais de gestão em saúde.
"""

import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SISTEMA_URL = os.getenv("SISTEMA_SAUDE_URL", "https://sua-prefeitura.atende.net/saude/")
SISTEMA_USER = os.getenv("SISTEMA_SAUDE_USUARIO", "")
SISTEMA_PASS = os.getenv("SISTEMA_SAUDE_SENHA", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

SCRIPT_DIR = Path(__file__).parent.resolve()

DATA_HOJE_PASTA = datetime.now().strftime("%Y-%m-%d")
EXPORT_BASE_DIR = Path(os.getenv("EXPORT_DIR", str(SCRIPT_DIR / "exports"))).resolve()
PASTA_HOJE = EXPORT_BASE_DIR / DATA_HOJE_PASTA
PASTA_HOJE.mkdir(parents=True, exist_ok=True)

LOG_FILE = SCRIPT_DIR / "log_exportacao.txt"
LOG_PASTA_HOJE = PASTA_HOJE / f"log_{datetime.now().strftime('%H%M%S')}.txt"
PARAR_FILE = SCRIPT_DIR / "PARAR.txt"

INTERVALO_DUPLICATA_MIN = 5

FICHAS_EXPORTAR = [
    "Ficha de Atendimento Domiciliar",
    "Ficha de Atendimento Individual",
    "Ficha de Atendimento Odontol\u00f3gico",
    "Ficha de Atividade Coletiva",
    "Ficha de Cadastro Domiciliar e Territorial",
    "Ficha de Cadastro Individual",
    "Ficha de Procedimentos",
    "Ficha de Visita Domiciliar e Territorial",
    "Marcadores de Consumo Alimentar",
]

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Mar\u00e7o", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

UNIDADES = [
    "Unidade de Saude Gigante",
    "Unidade de Saude Pinho Fleck",
    "Unidade de Atencao Primaria Saude da Familia Uapsf"
]

def log(mensagem):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {mensagem}"
    print(linha)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
        with open(LOG_PASTA_HOJE, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except:
        pass

def enviar_notificacao_telegram(mensagem):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"  ! Aviso ao enviar Telegram: {e}")
        return False

def verificar_parada():
    if PARAR_FILE.exists():
        log(">> ARQUIVO PARAR.txt DETECTADO! Encerrando automacao...")
        return True
    return False

def obter_competencia_atual():
    now = datetime.now()
    nome_mes = MESES_PT.get(now.month, "Julho")
    return f"{nome_mes}, {now.year}"

def obter_data_hoje():
    return datetime.now().strftime("%d/%m/%Y")

def encontrar_frame_exportacao(page):
    for frame in page.frames:
        try:
            el = frame.query_selector("#tipo_exportacao")
            if el:
                return frame
        except:
            pass
    return None

def clicar_em_frames(page, seletor=None, texto=None, timeout_sec=5):
    start = time.time()
    while time.time() - start < timeout_sec:
        for frame in page.frames:
            try:
                elem = None
                if seletor:
                    elem = frame.query_selector(seletor)
                if not elem and texto:
                    elem = frame.query_selector(f"text='{texto}'")
                if elem and elem.is_visible():
                    elem.click()
                    return True
            except:
                pass
        time.sleep(0.3)
    return False

def clicar_incluir(page):
    seletores = [
        "[title*='Incluir']", "[id*='incluir']", "input[value='Incluir']",
        "input[value='+']", "button:has-text('Incluir')", "a:has-text('Incluir')",
        "i.fa-plus", "i.fa-plus-circle"
    ]
    for sel in seletores:
        if clicar_em_frames(page, seletor=sel, timeout_sec=2):
            log("  + Botao Incluir (+) clicado.")
            return True
    if clicar_em_frames(page, texto="Incluir", timeout_sec=2):
        log("  + Botao Incluir clicado via texto.")
        return True
    return False

def ler_tabela_exportacoes(page):
    registros = []
    for frame in page.frames:
        try:
            dados = frame.evaluate("""
                () => {
                    const rows = document.querySelectorAll('tr');
                    const registros = [];
                    for (const row of rows) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 9) {
                            const data = cells[0]?.innerText?.trim() || '';
                            const hora = cells[1]?.innerText?.trim() || '';
                            const tipo = cells[8]?.innerText?.trim() || '';
                            if (data.length === 10 && data[2] === '/' && data[5] === '/') {
                                registros.push({ data: data, hora: hora, tipo_exportacao: tipo });
                            }
                        }
                    }
                    return registros;
                }
            """)
            if dados and len(dados) > 0:
                registros = dados
                break
        except:
            pass
    return registros

def ficha_exportada_recentemente_na_tela(registros_tabela, ficha, data_hoje):
    agora = datetime.now()
    for reg in registros_tabela:
        if reg.get("data") != data_hoje:
            continue
        tipo_na_tabela = reg.get("tipo_exportacao", "")
        if ficha.lower() not in tipo_na_tabela.lower() and tipo_na_tabela.lower() not in ficha.lower():
            continue
        hora_str = reg.get("hora", "")
        try:
            hora_export = datetime.strptime(f"{reg['data']} {hora_str}", "%d/%m/%Y %H:%M:%S")
            diferenca = agora - hora_export
            if diferenca < timedelta(minutes=INTERVALO_DUPLICATA_MIN):
                min_atras = round(diferenca.total_seconds() / 60, 1)
                return True, min_atras
        except:
            pass
    return False, 0

def selecionar_tipo_ficha_chosen(frame, nome_ficha, max_tentativas=3):
    for tentativa in range(1, max_tentativas + 1):
        log(f"  [Tentativa {tentativa}/{max_tentativas}] Selecionando tipo: {nome_ficha}")
        try:
            resultado = frame.evaluate("""
                (nomeFicha) => {
                    const select = document.getElementById('tipo_exportacao');
                    if (!select) return { ok: false, erro: 'select nao encontrado' };
                    let found = false;
                    for (let opt of select.options) {
                        if (opt.text.trim() === nomeFicha) {
                            select.value = opt.value;
                            found = true;
                            break;
                        }
                    }
                    if (!found) return { ok: false, erro: 'option nao encontrada: ' + nomeFicha };
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    if (typeof jQuery !== 'undefined') {
                        jQuery('#tipo_exportacao').trigger('chosen:updated');
                    }
                    const selecionado = select.options[select.selectedIndex]?.text?.trim();
                    return { ok: selecionado === nomeFicha, selecionado: selecionado };
                }
            """, nome_ficha)
            if resultado.get("ok"):
                log(f"  [OK] Tipo de Ficha selecionado: {nome_ficha}")
                return True
            else:
                log(f"  ! Falha na tentativa {tentativa}: {resultado}")
        except Exception as e:
            log(f"  ! Erro JS na tentativa {tentativa}: {e}")
        time.sleep(1)
    log(f"  [FALHA] Nao foi possivel selecionar '{nome_ficha}' apos {max_tentativas} tentativas.")
    return False

def selecionar_competencia(frame, competencia_texto):
    try:
        resultado = frame.evaluate("""
            (comp) => {
                const select = document.getElementById('competencia');
                if (!select) return { ok: false, erro: 'select competencia nao encontrado' };
                for (let opt of select.options) {
                    if (opt.text.trim() === comp) {
                        select.value = opt.value;
                        select.dispatchEvent(new Event('change', { bubbles: true }));
                        return { ok: true, selecionado: opt.text.trim() };
                    }
                }
                if (select.options.length > 1) {
                    select.value = select.options[1].value;
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    return { ok: true, selecionado: select.options[1].text.trim() };
                }
                return { ok: false, erro: 'nenhuma opcao disponivel' };
            }
        """, competencia_texto)
        if resultado.get("ok"):
            log(f"  + Competencia selecionada: {resultado.get('selecionado')}")
            return True
        else:
            log(f"  ! Competencia: {resultado}")
            return False
    except Exception as e:
        log(f"  ! Erro ao selecionar competencia: {e}")
        return False

def preencher_datas(frame, data_hoje):
    try:
        resultado = frame.evaluate("""
            (dataHoje) => {
                const dtInicial = document.getElementById('eedatainicial');
                const dtFinal = document.getElementById('eedatafinal');
                if (!dtInicial || !dtFinal) return { ok: false, erro: 'campos de data nao encontrados' };
                dtInicial.value = dataHoje;
                dtFinal.value = dataHoje;
                dtInicial.dispatchEvent(new Event('change', { bubbles: true }));
                dtFinal.dispatchEvent(new Event('change', { bubbles: true }));
                dtInicial.dispatchEvent(new Event('blur', { bubbles: true }));
                dtFinal.dispatchEvent(new Event('blur', { bubbles: true }));
                return { ok: true, inicial: dtInicial.value, final: dtFinal.value };
            }
        """, data_hoje)
        if resultado.get("ok"):
            log(f"  + Datas preenchidas: {resultado.get('inicial')} a {resultado.get('final')}")
            return True
        else:
            log(f"  ! Datas: {resultado}")
            return False
    except Exception as e:
        log(f"  ! Erro ao preencher datas: {e}")
        return False

def executar_automacao_lote():
    from playwright.sync_api import sync_playwright

    competencia = obter_competencia_atual()
    data_hoje = obter_data_hoje()
    hora_inicio = datetime.now().strftime("%H:%M")

    if PARAR_FILE.exists():
        PARAR_FILE.unlink()

    log("=" * 70)
    log("  AUTOMACAO DE EXPORTACAO EM LOTE - SISTEMAS DE SAUDE APS")
    log(f"  URL: {SISTEMA_URL}")
    log(f"  COMPETENCIA: {competencia}")
    log(f"  DATA HOJE: {data_hoje}")
    log(f"  PASTA DO DIA: {PASTA_HOJE}")
    log("=" * 70)

    with sync_playwright() as p:
        is_headless = os.getenv("HEADLESS", "false").lower() == "true"
        browser = p.chromium.launch(headless=is_headless, slow_mo=300 if not is_headless else 0)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        def on_download(download):
            try:
                caminho_dest = PASTA_HOJE / download.suggested_filename
                download.save_as(caminho_dest)
                log(f"  [DOWNLOAD OK] Arquivo salvo em: {caminho_dest}")
            except Exception as ex_dl:
                log(f"  ! Aviso ao salvar download: {ex_dl}")

        page.on("download", on_download)

        log("\n[1/4] Login...")
        page.goto(SISTEMA_URL)
        page.wait_for_load_state("networkidle")

        user_input = page.query_selector("input[name*='usuario'], input[name*='cpf'], input[id*='usuario'], input[type='text']")
        pass_input = page.query_selector("input[type='password']")

        if user_input and pass_input:
            user_input.fill(SISTEMA_USER)
            pass_input.fill(SISTEMA_PASS)
            btn = page.query_selector("#btn_enter, button[type='submit'], input[type='submit']")
            if btn:
                btn.click()
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            log(" -> Login OK!")

        log("[2/4] Navegando: Exportacoes -> E-SUS -> CDS/RAS...")
        clicar_em_frames(page, texto="Exporta\u00e7\u00f5es", timeout_sec=15)
        time.sleep(1.5)
        clicar_em_frames(page, texto="E-SUS", timeout_sec=10)
        time.sleep(1.5)
        clicar_em_frames(page, texto="CDS/RAS", timeout_sec=10)
        time.sleep(3)
        log(" -> OK!")

        log("[3/4] Lendo tabela de exportacoes existentes...")
        registros_tabela = ler_tabela_exportacoes(page)
        registros_hoje = [r for r in registros_tabela if r.get("data") == data_hoje]
        log(f"  -> {len(registros_tabela)} registros na tabela, {len(registros_hoje)} de hoje ({data_hoje}).")

        log(f"\n[4/4] Iniciando exportacao em lote ({len(FICHAS_EXPORTAR)} fichas)...\n")
        total_ok = 0
        total_falha = 0
        total_puladas = 0

        for i, ficha in enumerate(FICHAS_EXPORTAR, 1):
            if verificar_parada():
                break

            log(f"{'='*60}")
            log(f" [{i}/{len(FICHAS_EXPORTAR)}] {ficha}")
            log(f"{'='*60}")

            duplicada, min_atras = ficha_exportada_recentemente_na_tela(registros_tabela, ficha, data_hoje)
            if duplicada:
                log(f"  [PULADA] Ja gerada ha {min_atras} min (limite: {INTERVALO_DUPLICATA_MIN} min).")
                total_puladas += 1
                continue

            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            time.sleep(1)

            incluir_ok = False
            for tentativa_incluir in range(5):
                if clicar_incluir(page):
                    incluir_ok = True
                    break
                log(f"  -> Aguardando tela (tentativa {tentativa_incluir + 1}/5)...")
                time.sleep(3)
                clicar_em_frames(page, texto="Voltar", timeout_sec=2)
                time.sleep(2)
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except:
                    pass

            if not incluir_ok:
                log("  [FALHA] Botao Incluir nao encontrado. Pulando...")
                total_falha += 1
                continue

            time.sleep(2)

            for u in UNIDADES:
                clicar_em_frames(page, texto=u, timeout_sec=3)
            time.sleep(1)

            frame_exp = encontrar_frame_exportacao(page)
            if not frame_exp:
                log("  [FALHA] Frame do formulario nao encontrado! Pulando...")
                total_falha += 1
                clicar_em_frames(page, texto="Voltar", timeout_sec=3)
                time.sleep(2)
                continue

            ficha_ok = selecionar_tipo_ficha_chosen(frame_exp, ficha)
            if not ficha_ok:
                log(f"  [FALHA] Nao selecionou {ficha}. Pulando...")
                total_falha += 1
                clicar_em_frames(page, texto="Voltar", timeout_sec=3)
                time.sleep(1)
                continue

            time.sleep(0.5)

            selecionar_competencia(frame_exp, competencia)
            time.sleep(0.5)

            preencher_datas(frame_exp, data_hoje)
            time.sleep(0.5)

            log(" -> Confirmando exportacao...")
            clicar_em_frames(page, seletor="#confirmar", timeout_sec=5)
            time.sleep(1.5)

            clicar_em_frames(page, seletor="#system_aviso_confirma", timeout_sec=4)
            time.sleep(1.5)

            clicar_em_frames(page, seletor="#sobreposta-confirmacao-padrao-confirmar", timeout_sec=4)

            log(" -> Aguardando processamento...")
            processamento_ok = False
            for _ in range(30):
                time.sleep(2)
                for frame in page.frames:
                    try:
                        for sel in ["[title*='Incluir']", "[id*='incluir']", "input[value='Incluir']",
                                    "input[value='+']", "i.fa-plus", "i.fa-plus-circle"]:
                            el = frame.query_selector(sel)
                            if el and el.is_visible():
                                processamento_ok = True
                                break
                    except:
                        pass
                    if processamento_ok:
                        break
                if processamento_ok:
                    break

            if not processamento_ok:
                log(" -> Tempo de processamento excedido, continuando...")

            total_ok += 1
            log(f" [OK] {ficha} exportada com sucesso!\n")

        hora_fim = datetime.now().strftime("%H:%M")
        log("\n" + "=" * 70)
        log("  PROCESSO EM LOTE CONCLUIDO!")
        log(f"  Data: {data_hoje} ({hora_inicio} as {hora_fim})")
        log(f"  Exportadas com Sucesso: {total_ok}")
        log(f"  Puladas (duplicata):    {total_puladas}")
        log(f"  Falhas:                 {total_falha}")
        log("=" * 70)

        msg_telegram = (
            f"🏥 *Relatório de Exportação e-SUS APS*\n\n"
            f"📅 *Data:* {data_hoje} ({hora_inicio} às {hora_fim})\n"
            f"✅ *Sucesso:* {total_ok} fichas\n"
            f"⏩ *Puladas (duplicatas):* {total_puladas} fichas\n"
            f"❌ *Falhas:* {total_falha} fichas\n\n"
            f"📁 *Pasta:* `{PASTA_HOJE.name}`"
        )
        enviado = enviar_notificacao_telegram(msg_telegram)
        if enviado:
            log(" -> Notificacao enviada para o Telegram com sucesso!")

        browser.close()

if __name__ == "__main__":
    executar_automacao_lote()
