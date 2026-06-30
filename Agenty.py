#!/usr/bin/env python3
"""
Agente Pessoal - Organização de Estudos e Finanças
Armazenamento: Google Sheets
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# CONEXÃO COM GOOGLE SHEETS
# ============================================================
def conectar_sheets():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID)


def obter_aba(spreadsheet, nome_aba, cabecalho):
    try:
        aba = spreadsheet.worksheet(nome_aba)
    except gspread.exceptions.WorksheetNotFound:
        aba = spreadsheet.add_worksheet(title=nome_aba, rows=1000, cols=len(cabecalho))
        aba.append_row(cabecalho)
    return aba


# ============================================================
# MÓDULO FINANCEIRO
# ============================================================
def adicionar_transacao(spreadsheet):
    print("\n--- Nova Transação ---")
    print("Tipo: 1) Receita  2) Despesa")
    opcao = input("Escolha (1 ou 2): ").strip()
    tipo = "Receita" if opcao == "1" else "Despesa"

    categoria = input("Categoria (ex: Alimentação, Salário, Transporte): ").strip()
    valor = input("Valor (R$): ").strip().replace(",", ".")
    descricao = input("Descrição: ").strip()
    data = input(f"Data (DD/MM/AAAA) [Enter para hoje]: ").strip()
    if not data:
        data = datetime.now().strftime("%d/%m/%Y")

    aba = obter_aba(spreadsheet, "Financeiro", ["Data", "Tipo", "Categoria", "Valor", "Descrição"])
    aba.append_row([data, tipo, categoria, float(valor), descricao])

    print(f"\n✅ Registrado: {tipo} de R${float(valor):.2f} em '{categoria}'")


def ver_resumo_financeiro(spreadsheet):
    aba = obter_aba(spreadsheet, "Financeiro", ["Data", "Tipo", "Categoria", "Valor", "Descrição"])
    registros = aba.get_all_records()

    if not registros:
        print("\n📊 Nenhuma transação registrada ainda.")
        return

    receitas = sum(float(r["Valor"]) for r in registros if r["Tipo"] == "Receita")
    despesas = sum(float(r["Valor"]) for r in registros if r["Tipo"] == "Despesa")
    saldo = receitas - despesas

    categorias = {}
    for r in registros:
        cat = r["Categoria"]
        val = float(r["Valor"])
        if cat not in categorias:
            categorias[cat] = {"Receita": 0.0, "Despesa": 0.0}
        categorias[cat][r["Tipo"]] += val

    print("\n" + "=" * 40)
    print("       📊 RESUMO FINANCEIRO")
    print("=" * 40)
    print(f"  Receitas totais : R${receitas:>10.2f}")
    print(f"  Despesas totais : R${despesas:>10.2f}")
    print(f"  Saldo           : R${saldo:>10.2f}")
    print("-" * 40)
    print("  Por categoria:")
    for cat, vals in categorias.items():
        print(f"    {cat}:")
        if vals["Receita"]:
            print(f"      + R${vals['Receita']:.2f}")
        if vals["Despesa"]:
            print(f"      - R${vals['Despesa']:.2f}")
    print(f"\n  Total de registros: {len(registros)}")
    print("=" * 40)


def listar_transacoes(spreadsheet):
    aba = obter_aba(spreadsheet, "Financeiro", ["Data", "Tipo", "Categoria", "Valor", "Descrição"])
    registros = aba.get_all_records()

    if not registros:
        print("\n📋 Nenhuma transação registrada ainda.")
        return

    print("\n" + "=" * 65)
    print(f"  {'DATA':<12} {'TIPO':<10} {'CATEGORIA':<15} {'VALOR':>10}  DESCRIÇÃO")
    print("=" * 65)
    for r in registros[-20:]:  # últimas 20
        tipo_label = "📈" if r["Tipo"] == "Receita" else "📉"
        print(f"  {r['Data']:<12} {tipo_label} {r['Tipo']:<8} {r['Categoria']:<15} R${float(r['Valor']):>8.2f}  {r['Descrição']}")
    print("=" * 65)
    if len(registros) > 20:
        print(f"  (mostrando últimas 20 de {len(registros)} transações)")


# ============================================================
# MÓDULO DE ESTUDOS
# ============================================================
def registrar_estudo(spreadsheet):
    print("\n--- Nova Sessão de Estudo ---")
    materia = input("Matéria / Assunto: ").strip()
    horas = input("Horas estudadas (ex: 1.5 para 1h30): ").strip().replace(",", ".")
    notas = input("Anotações (opcional): ").strip()
    data = input(f"Data (DD/MM/AAAA) [Enter para hoje]: ").strip()
    if not data:
        data = datetime.now().strftime("%d/%m/%Y")

    aba = obter_aba(spreadsheet, "Estudos", ["Data", "Matéria", "Horas", "Anotações"])
    aba.append_row([data, materia, float(horas), notas])

    print(f"\n✅ Registrado: {horas}h de {materia} em {data}")


def ver_progresso_estudos(spreadsheet):
    aba = obter_aba(spreadsheet, "Estudos", ["Data", "Matéria", "Horas", "Anotações"])
    registros = aba.get_all_records()

    if not registros:
        print("\n📚 Nenhuma sessão de estudo registrada ainda.")
        return

    total_horas = sum(float(r["Horas"]) for r in registros)

    materias = {}
    for r in registros:
        mat = r["Matéria"]
        materias[mat] = materias.get(mat, 0.0) + float(r["Horas"])

    print("\n" + "=" * 40)
    print("       📚 PROGRESSO DE ESTUDOS")
    print("=" * 40)
    print(f"  Total de horas  : {total_horas:.1f}h")
    print(f"  Total de sessões: {len(registros)}")
    print("-" * 40)
    print("  Por matéria (mais estudadas):")
    for mat, horas in sorted(materias.items(), key=lambda x: x[1], reverse=True):
        barra = "█" * int(horas)
        print(f"    {mat:<20} {horas:>5.1f}h  {barra}")
    print("=" * 40)


def listar_estudos(spreadsheet):
    aba = obter_aba(spreadsheet, "Estudos", ["Data", "Matéria", "Horas", "Anotações"])
    registros = aba.get_all_records()

    if not registros:
        print("\n📋 Nenhuma sessão de estudo registrada ainda.")
        return

    print("\n" + "=" * 65)
    print(f"  {'DATA':<12} {'MATÉRIA':<22} {'HORAS':>6}  ANOTAÇÕES")
    print("=" * 65)
    for r in registros[-20:]:
        print(f"  {r['Data']:<12} {r['Matéria']:<22} {float(r['Horas']):>5.1f}h  {r['Anotações']}")
    print("=" * 65)
    if len(registros) > 20:
        print(f"  (mostrando últimas 20 de {len(registros)} sessões)")


# ============================================================
# MENUS
# ============================================================
def menu_financeiro(spreadsheet):
    while True:
        print("\n--- 💰 Financeiro ---")
        print("1) Adicionar transação")
        print("2) Ver resumo")
        print("3) Listar transações")
        print("0) Voltar")
        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            adicionar_transacao(spreadsheet)
        elif opcao == "2":
            ver_resumo_financeiro(spreadsheet)
        elif opcao == "3":
            listar_transacoes(spreadsheet)
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


def menu_estudos(spreadsheet):
    while True:
        print("\n--- 📚 Estudos ---")
        print("1) Registrar sessão de estudo")
        print("2) Ver progresso")
        print("3) Listar sessões")
        print("0) Voltar")
        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            registrar_estudo(spreadsheet)
        elif opcao == "2":
            ver_progresso_estudos(spreadsheet)
        elif opcao == "3":
            listar_estudos(spreadsheet)
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


# ============================================================
# VERIFICAÇÃO DE CONFIGURAÇÃO
# ============================================================
def verificar_config():
    erros = []
    if not SPREADSHEET_ID:
        erros.append("SPREADSHEET_ID não configurado no arquivo .env")
    if not os.path.exists(CREDENTIALS_FILE):
        erros.append(f"Arquivo '{CREDENTIALS_FILE}' não encontrado")

    if erros:
        print("\n❌ Configuração incompleta:")
        for erro in erros:
            print(f"   • {erro}")
        print("\nConsulte o guia de configuração do Google Sheets.")
        return False
    return True


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 40)
    print("   🤖 Agente Pessoal")
    print("   Estudos & Finanças")
    print("=" * 40)

    if not verificar_config():
        return

    try:
        spreadsheet = conectar_sheets()
        print(f"\n✅ Conectado à planilha com sucesso!\n")
    except Exception as e:
        print(f"\n❌ Erro ao conectar ao Google Sheets: {e}")
        return

    while True:
        print("\n=== MENU PRINCIPAL ===")
        print("1) 💰 Financeiro")
        print("2) 📚 Estudos")
        print("0) Sair")
        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            menu_financeiro(spreadsheet)
        elif opcao == "2":
            menu_estudos(spreadsheet)
        elif opcao == "0":
            print("\nAté logo! 👋")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
