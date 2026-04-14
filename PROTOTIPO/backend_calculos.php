<?php
// backend_calculos.php
// Recebe os dados em formato JSON do primeiro argumento passado pelo terminal.
// Exemplo: php backend_calculos.php '{"action": "calcular_nota", "items": [{"preco_base": 10.5, "aliquota": 0.1, "quantidade": 2}]}'

if ($argc < 2) {
    echo json_encode(["status" => "error", "message" => "Nenhum dado JSON fornecido."]);
    exit(1);
}

$jsonData = $argv[1];
$data = json_decode($jsonData, true);

if (!$data) {
    echo json_encode(["status" => "error", "message" => "O formato JSON passado está inválido ou malformado."]);
    exit(1);
}

$action = $data['action'] ?? '';

if ($action === 'calcular_nota') {
    $items = $data['items'] ?? [];
    
    $total_bruto = 0;
    $total_imposto = 0;
    $total_final = 0;
    
    foreach ($items as $item) {
        $preco_base = (float)($item['preco_base'] ?? 0);
        $aliquota = (float)($item['aliquota'] ?? 0);
        $quantidade = (int)($item['quantidade'] ?? 0);
        
        $imposto_item = $preco_base * $aliquota * $quantidade;
        $total_item = ($preco_base * $quantidade) + $imposto_item;
        
        $total_bruto += ($preco_base * $quantidade);
        $total_imposto += $imposto_item;
        $total_final += $total_item;
    }
    
    // Retorna o cálculo completo para o Python
    echo json_encode([
        "status" => "success",
        "data" => [
            "total_bruto" => round($total_bruto, 2),
            "total_imposto" => round($total_imposto, 2),
            "total_final" => round($total_final, 2)
        ]
    ]);
    exit(0);

} elseif ($action === 'verificar_estoque') {
    // Uma simulação de uma ação mais complexa: checar saldo x quantidade exigida.
    // O backend PHP no futuro pode validar diretamente no banco ou receber pelo Python para fazer a lógica.
    echo json_encode(["status" => "success", "message" => "Checagem fictícia realizada."]);
    exit(0);
} else {
    echo json_encode(["status" => "error", "message" => "Ação não reconhecida."]);
    exit(1);
}
