# financeiro.py
import json
import os
from datetime import datetime
from typing import Dict, Any, List

ARQUIVO_DADOS = "dados.json"
PASTA_RELATORIOS = "relatorios"

# -------------------------
# Utilitários
# -------------------------
def carregar_dados():
    # Se o arquivo não existir, cria vazio
    if not os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            f.write("{}")
        return {}

    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Se o arquivo estiver vazio ou corrompido, reinicia
            with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f2:
                f2.write("{}")
            return {}


def salvar_dados(dados: Dict[str, Any]) -> None:
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def obter_nome_mes(ano: int, mes: int) -> str:
    meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    return f"{meses[mes-1]}-{ano}"

def ordenar_meses_chaves(chaves: List[str]) -> List[str]:
    mapa_mes = {
        "Janeiro":1, "Fevereiro":2, "Março":3, "Abril":4, "Maio":5, "Junho":6,
        "Julho":7, "Agosto":8, "Setembro":9, "Outubro":10, "Novembro":11, "Dezembro":12
    }
    def chave_sort(k: str):
        nome, ano = k.split("-")
        return (int(ano), mapa_mes[nome])
    return sorted(chaves, key=chave_sort)

def obter_mes_anterior(ano: int, mes: int):
    """Retorna (ano_anterior, mes_anterior)."""
    if mes == 1:
        return ano - 1, 12
    return ano, mes - 1

# -------------------------
# Core
# -------------------------
def garantir_mes(dados: Dict[str, Any], ano: int, mes: int) -> None:
    """Garante o registro do mês com saldo_inicial herdado do mês anterior."""
    mes_ref = obter_nome_mes(ano, mes)
    if mes_ref in dados:
        return
    ano_ant, mes_ant = obter_mes_anterior(ano, mes)
    mes_ant_ref = obter_nome_mes(ano_ant, mes_ant)
    saldo_inicial = float(dados.get(mes_ant_ref, {}).get("saldo_final", 0.0))
    dados[mes_ref] = {
        "movimentacoes": [],
        "saldo_inicial": saldo_inicial,
        "entradas": 0.0,
        "saidas": 0.0,
        "saldo_final": saldo_inicial
    }

def cadastrar_movimentacao(dados: Dict[str, Any]) -> None:
    try:
        valor = float(input("Valor da movimentação: R$ ").replace(",", "."))
        tipo = input("Tipo (entrada/saida): ").strip().lower()
        if tipo not in {"entrada", "saida"}:
            print("⚠ Tipo inválido! Use 'entrada' ou 'saida'.")
            return
        descricao = input("Descrição: ").strip()
        data_str = input("Data (dd/mm/aaaa) [Enter para hoje]: ").strip()

        if data_str == "":
            data = datetime.now()
        else:
            data = datetime.strptime(data_str, "%d/%m/%Y")

        ano, mes = data.year, data.month
        mes_ref = obter_nome_mes(ano, mes)

        garantir_mes(dados, ano, mes)

        mov = {
            "tipo": tipo,
            "valor": float(valor),
            "data": data.strftime("%Y-%m-%d"),
            "descricao": descricao
        }
        dados[mes_ref]["movimentacoes"].append(mov)

        if tipo == "entrada":
            dados[mes_ref]["entradas"] += valor
            dados[mes_ref]["saldo_final"] += valor
        else:
            dados[mes_ref]["saidas"] += valor
            dados[mes_ref]["saldo_final"] -= valor

        salvar_dados(dados)
        print("✅ Movimentação cadastrada com sucesso!")
    except ValueError:
        print("⚠ Valor inválido!")

def exibir_resumo(dados: Dict[str, Any]) -> None:
    if not dados:
        print("⚠ Nenhum dado cadastrado ainda.")
        return
    for mes in ordenar_meses_chaves(list(dados.keys())):
        info = dados[mes]
        print("\n📅", mes)
        print(f"  Saldo inicial: R$ {info['saldo_inicial']:.2f}")
        print(f"  Entradas:      R$ {info['entradas']:.2f}")
        print(f"  Saídas:        R$ {info['saidas']:.2f}")
        print(f"  Saldo final:   R$ {info['saldo_final']:.2f}")
        print("  Movimentações:")
        for mov in sorted(info["movimentacoes"], key=lambda m: m["data"]):
            print(f"    - {datetime.strptime(mov['data'], '%Y-%m-%d').strftime('%d/%m/%Y')} | "
                  f"{mov['tipo']} R$ {mov['valor']:.2f} | {mov.get('descricao','')}")

# -------------------------
# PDFs - reportlab
# -------------------------
def gerar_pdf_mes(dados: Dict[str, Any], mes_ref: str) -> str:
    """
    Gera um PDF do mês informado (ex.: 'Janeiro-2025').
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        raise RuntimeError("A biblioteca 'reportlab' é necessária. Instale com: pip install reportlab")

    if mes_ref not in dados:
        raise ValueError(f"Mês '{mes_ref}' não encontrado.")

    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    nome_arquivo = os.path.join(PASTA_RELATORIOS, f"relatorio-{mes_ref}.pdf")

    info = dados[mes_ref]
    movs = sorted(info.get("movimentacoes", []), key=lambda m: m["data"])

    styles = getSampleStyleSheet()
    estilo_titulo = styles["Heading1"]
    estilo_sub = styles["Heading3"]
    estilo_normal = styles["BodyText"]

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    elementos = []

    # Cabeçalho
    elementos.append(Paragraph(f"Relatório Financeiro – {mes_ref}", estilo_titulo))
    elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_normal))
    elementos.append(Spacer(1, 6*mm))

    # Resumo
    elementos.append(Paragraph("Resumo do Mês", estilo_sub))
    resumo_txt = (
        f"<b>Saldo inicial:</b> R$ {info['saldo_inicial']:.2f}<br/>"
        f"<b>Total de entradas:</b> R$ {info['entradas']:.2f}<br/>"
        f"<b>Total de saídas:</b> R$ {info['saidas']:.2f}<br/>"
        f"<b>Saldo final:</b> R$ {info['saldo_final']:.2f}"
    )
    elementos.append(Paragraph(resumo_txt, estilo_normal))
    elementos.append(Spacer(1, 6*mm))

    # Tabela
    cabecalho = ["Data", "Tipo", "Valor (R$)", "Descrição"]
    linhas = [cabecalho]
    for m in movs:
        linhas.append([
            datetime.strptime(m["data"], "%Y-%m-%d").strftime("%d/%m/%Y"),
            "Entrada" if m["tipo"] == "entrada" else "Saída",
            f"{m['valor']:.2f}",
            m.get("descricao", "")
        ])

    tabela = Table(linhas, colWidths=[25*mm, 25*mm, 30*mm, None])
    estilo = TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,0), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (2,1), (2,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
    ])
    tabela.setStyle(estilo)
    elementos.append(tabela)

    doc.build(elementos)
    return nome_arquivo

def gerar_pdfs_todos_os_meses(dados: Dict[str, Any]) -> List[str]:
    gerados = []
    for mes in ordenar_meses_chaves(list(dados.keys())):
        gerados.append(gerar_pdf_mes(dados, mes))
    return gerados

# -------------------------
# PDF por período (com gráfico)
# -------------------------
def gerar_pdf_periodo(dados: Dict[str, Any], ano: int, mes_ini: int, mes_fim: int) -> str:
    """
    Gera um relatório PDF consolidado para um intervalo de meses de um ano.
    Inclui gráfico Entradas (verde), Saídas (vermelho) e Saldo Final (azul).
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        raise RuntimeError("Instale reportlab: pip install reportlab")

    # Selecionar meses do intervalo
    meses_selecionados = []
    for m in range(mes_ini, mes_fim + 1):
        ms = obter_nome_mes(ano, m)
        if ms in dados:
            meses_selecionados.append(ms)

    if not meses_selecionados:
        raise ValueError("Nenhum mês encontrado nesse intervalo.")

    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    nome_arquivo = os.path.join(PASTA_RELATORIOS, f"relatorio-{ano}-{mes_ini:02d}_a_{mes_fim:02d}.pdf")

    styles = getSampleStyleSheet()
    estilo_titulo = styles["Heading1"]
    estilo_normal = styles["BodyText"]

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4,
                            rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    elementos = []

    # Cabeçalho
    elementos.append(Paragraph(f"Relatório Financeiro – {ano} ({mes_ini:02d} a {mes_fim:02d})", estilo_titulo))
    elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_normal))
    elementos.append(Spacer(1, 6*mm))

    # Consolidado
    total_entradas = total_saidas = 0.0
    saldo_inicial = dados[meses_selecionados[0]]["saldo_inicial"]
    saldo_final = dados[meses_selecionados[-1]]["saldo_final"]

    for ms in meses_selecionados:
        total_entradas += dados[ms]["entradas"]
        total_saidas += dados[ms]["saidas"]

    resumo = (
        f"<b>Saldo inicial:</b> R$ {saldo_inicial:.2f}<br/>"
        f"<b>Total de entradas:</b> R$ {total_entradas:.2f}<br/>"
        f"<b>Total de saídas:</b> R$ {total_saidas:.2f}<br/>"
        f"<b>Saldo final:</b> R$ {saldo_final:.2f}"
    )
    elementos.append(Paragraph(resumo, estilo_normal))
    elementos.append(Spacer(1, 6*mm))

    # ---------- Gráfico (matplotlib) ----------
    import matplotlib
    matplotlib.use("Agg")  # backend para salvar arquivo sem janela
    import matplotlib.pyplot as plt

    meses_labels = [ms for ms in meses_selecionados]
    entradas_vals = [dados[ms]["entradas"] for ms in meses_selecionados]
    saidas_vals = [dados[ms]["saidas"] for ms in meses_selecionados]
    saldos_finais = [dados[ms]["saldo_final"] for ms in meses_selecionados]

    plt.figure(figsize=(7, 3.5))
    # barras lado a lado
    x = list(range(len(meses_labels)))
    largura = 0.35
    plt.bar([i - largura/2 for i in x], entradas_vals, width=largura, label="Entradas", color="green")
    plt.bar([i + largura/2 for i in x], saidas_vals, width=largura, label="Saídas", color="red")
    # linha do saldo
    plt.plot(x, saldos_finais, marker="o", label="Saldo Final", color="blue")
    plt.xticks(x, meses_labels, rotation=45, ha="right")
    plt.ylabel("R$ ")
    plt.legend()
    plt.tight_layout()

    img_temp = os.path.join(PASTA_RELATORIOS, "grafico_temp.png")
    plt.savefig(img_temp, dpi=160)
    plt.close()

    elementos.append(Image(img_temp, width=170*mm, height=85*mm))
    elementos.append(Spacer(1, 6*mm))

    # Listagem de movimentações por mês
    for ms in meses_selecionados:
        elementos.append(Paragraph(f"<b>{ms}</b>", styles["Heading3"]))
        for mov in sorted(dados[ms]["movimentacoes"], key=lambda m: m["data"]):
            elementos.append(Paragraph(
                f"{datetime.strptime(mov['data'], '%Y-%m-%d').strftime('%d/%m/%Y')} | "
                f"{mov['tipo']} R$ {mov['valor']:.2f} | {mov.get('descricao','')}",
                estilo_normal
            ))
        elementos.append(Spacer(1, 3*mm))

    doc.build(elementos)

    if os.path.exists(img_temp):
        os.remove(img_temp)

    return nome_arquivo

# -------------------------
# Menu (CLI)
# -------------------------
def menu():
    dados = carregar_dados()
    while True:
        print("\n=== SISTEMA FINANCEIRO ===")
        print("1 - Cadastrar movimentação")
        print("2 - Exibir resumo")
        print("3 - Gerar PDF de um mês")
        print("4 - Gerar PDFs de todos os meses")
        print("5 - Gerar PDF por período (trimestre/semestre/ano)")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_movimentacao(dados)
            dados = carregar_dados()  # recarrega do disco
        elif opcao == "2":
            exibir_resumo(dados)
        elif opcao == "3":
            mes_ref = input("Informe o mês (ex: Janeiro-2025): ").strip()
            try:
                caminho = gerar_pdf_mes(dados, mes_ref)
                print(f"✅ PDF gerado em: {caminho}")
            except Exception as e:
                print(f"⚠ Erro ao gerar PDF: {e}")
        elif opcao == "4":
            try:
                gerados = gerar_pdfs_todos_os_meses(dados)
                if gerados:
                    print("✅ PDFs gerados:")
                    for c in gerados:
                        print(" -", c)
                else:
                    print("⚠ Não há meses para gerar.")
            except Exception as e:
                print(f"⚠ Erro ao gerar PDFs: {e}")
        elif opcao == "5":
            try:
                ano = int(input("Ano (ex: 2025): "))
                mes_ini = int(input("Mês inicial (1-12): "))
                mes_fim = int(input("Mês final (1-12): "))
                if not (1 <= mes_ini <= 12 and 1 <= mes_fim <= 12 and mes_ini <= mes_fim):
                    print("⚠ Intervalo de meses inválido.")
                    continue
                caminho = gerar_pdf_periodo(dados, ano, mes_ini, mes_fim)
                print(f"✅ PDF consolidado gerado em: {caminho}")
            except Exception as e:
                print(f"⚠ Erro: {e}")
        elif opcao == "0":
            print("Saindo... 👋")
            break
        else:
            print("⚠ Opção inválida!")

if __name__ == "__main__":
    menu()
