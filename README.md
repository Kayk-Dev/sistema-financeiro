# Sistema Financeiro

Um sistema simples de controle financeiro desenvolvido em **Python**, que permite cadastrar **entradas e saídas**, salvar o **histórico mensal** e gerar relatórios em PDF.

---

## Funcionalidades

- Cadastro de **entradas** (receitas) e **saídas** (despesas)
- Armazenamento local em **JSON**
- Cálculo automático do **saldo mensal**
- Histórico mensal completo, com somatória de entradas e subtração de saídas
- Geração de **relatórios em PDF**
- Sistema preparado para rodar em **Windows** como **executável `.exe`** usando PyInstaller
- Criação automática de pastas e arquivos necessários (`relatorios`, `financeiro.json`)

---

## Pré-requisitos

- Python 3.10+  
- Bibliotecas Python:

```bash
pip install reportlab
