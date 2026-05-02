## Endpoints Existentes (Funcionais Internos)

O sistema atual opera em arquitetura desktop (PyQt6), utilizando handlers internos que futuramente poderão ser migrados para API REST.

### Produtos

- acao_salvar_produto()
  - Responsável por cadastrar ou atualizar produtos.
  - Dados: SKU, nome, preço base, alíquota.

### Estoque

- acao_estoque("entrada")
  - Registra entrada de estoque.

- acao_estoque("saida")
  - Registra saída de estoque com validação de saldo.

- acao_consultar_estoque()
  - Consulta saldo atual por SKU.

### Fiscal

- acao_calcular_impostos()
  - Calcula impostos de item/produto via integração PHP.

### Caixa

- acao_atualizar_caixa()
  - Consulta resumo financeiro:
    - total entradas
    - total despesas
    - saldo líquido

### Nota Fiscal

- acao_criar_nota_fiscal()
  - Cria intenção de nota fiscal.

- acao_validar_sku_nota()
  - Valida SKU antes de inserir item.

- acao_adicionar_item_nota()
  - Adiciona item à nota.

- acao_exibir_itens_nota()
  - Lista itens vinculados.

- acao_calcular_totais_nota()
  - Consolida totais financeiros da nota.

- acao_emitir_nota_fiscal()
  - Emite nota e processa estoque.
