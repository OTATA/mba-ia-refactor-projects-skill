"""Smoke test dos endpoints originais.

Roda contra um banco temporário e confere status code e formato de resposta de
cada rota que existia antes da refatoração. Não é uma suíte de testes: é a
validação da Fase 3 do desafio.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

from src.app import create_app
from src.config.settings import load_settings

falhas = []
total = 0


def checar(descricao, condicao, detalhe=""):
    global total
    total += 1
    if condicao:
        print(f"  ✓ {descricao}")
    else:
        print(f"  ✗ {descricao} :: {detalhe}")
        falhas.append(descricao)


def main():
    banco = os.path.join(tempfile.mkdtemp(), "validacao.db")
    settings = load_settings(
        {
            "APP_ENV": "development",
            "APP_DEBUG": "false",
            "SECRET_KEY": "chave-de-teste",
            "DATABASE_PATH": banco,
            "SEED_DATABASE": "true",
            "BOOTSTRAP_DATABASE": "true",
        }
    )
    app = create_app(settings)
    cliente = app.test_client()

    print("\n[boot]")
    checar("aplicação inicia sem erros", app is not None)

    print("\n[GET /]")
    r = cliente.get("/")
    checar("200", r.status_code == 200, r.status_code)
    checar("payload de índice", r.json["mensagem"] == "Bem-vindo à API da Loja")

    print("\n[GET /health]")
    r = cliente.get("/health")
    checar("200", r.status_code == 200, r.status_code)
    checar("status ok", r.json["status"] == "ok")
    checar("counts presentes", set(r.json["counts"]) == {"produtos", "usuarios", "pedidos"})
    checar("seed com 10 produtos", r.json["counts"]["produtos"] == 10, r.json["counts"])
    checar("secret_key NÃO exposta", "secret_key" not in r.json, list(r.json))
    checar("db_path NÃO exposto", "db_path" not in r.json, list(r.json))

    print("\n[GET /produtos]")
    r = cliente.get("/produtos")
    checar("200", r.status_code == 200, r.status_code)
    checar("envelope dados/sucesso", r.json["sucesso"] is True and len(r.json["dados"]) == 10)
    checar(
        "campos do produto",
        set(r.json["dados"][0])
        == {"id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em"},
        set(r.json["dados"][0]),
    )
    checar(
        "apóstrofo no seed preservado (SQL parametrizado)",
        any(p["nome"] == "Monitor 27''" for p in r.json["dados"]),
    )

    print("\n[GET /produtos/<id>]")
    r = cliente.get("/produtos/1")
    checar("200", r.status_code == 200, r.status_code)
    checar("produto retornado", r.json["dados"]["id"] == 1)
    r = cliente.get("/produtos/9999")
    checar("404 inexistente", r.status_code == 404, r.status_code)
    checar("mensagem original", r.json["erro"] == "Produto não encontrado", r.json)

    print("\n[GET /produtos/busca]")
    r = cliente.get("/produtos/busca?q=Notebook")
    checar("200", r.status_code == 200, r.status_code)
    checar("total presente", r.json["total"] == 1, r.json)
    r = cliente.get("/produtos/busca?categoria=moveis")
    checar("filtro por categoria", r.json["total"] == 1, r.json)
    r = cliente.get("/produtos/busca?preco_min=1000&preco_max=2000")
    checar("filtro por faixa de preço", r.json["total"] == 2, r.json)
    r = cliente.get("/produtos/busca?q=O'Brien")
    checar("apóstrofo no termo não quebra", r.status_code == 200, r.status_code)
    r = cliente.get("/produtos/busca?q=x' OR '1'='1")
    checar("injeção no termo não retorna tudo", r.json["total"] == 0, r.json["total"])

    print("\n[POST /produtos]")
    r = cliente.post(
        "/produtos",
        json={"nome": "Produto Teste", "preco": 10.5, "estoque": 3, "categoria": "livros"},
    )
    checar("201", r.status_code == 201, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Produto criado", r.json)
    novo_id = r.json["dados"]["id"]
    checar("id retornado", isinstance(novo_id, int))

    r = cliente.post("/produtos", json={"preco": 1, "estoque": 1})
    checar("400 sem nome", r.status_code == 400 and r.json["erro"] == "Nome é obrigatório", r.json)
    r = cliente.post("/produtos", json={"nome": "abc", "estoque": 1})
    checar("400 sem preço", r.json["erro"] == "Preço é obrigatório", r.json)
    r = cliente.post("/produtos", json={"nome": "abc", "preco": 1})
    checar("400 sem estoque", r.json["erro"] == "Estoque é obrigatório", r.json)
    r = cliente.post("/produtos", json={"nome": "abc", "preco": -1, "estoque": 1})
    checar("400 preço negativo", r.json["erro"] == "Preço não pode ser negativo", r.json)
    r = cliente.post("/produtos", json={"nome": "abc", "preco": 1, "estoque": -1})
    checar("400 estoque negativo", r.json["erro"] == "Estoque não pode ser negativo", r.json)
    r = cliente.post("/produtos", json={"nome": "a", "preco": 1, "estoque": 1})
    checar("400 nome curto", r.json["erro"] == "Nome muito curto", r.json)
    r = cliente.post("/produtos", json={"nome": "a" * 201, "preco": 1, "estoque": 1})
    checar("400 nome longo", r.json["erro"] == "Nome muito longo", r.json)
    r = cliente.post(
        "/produtos", json={"nome": "abc", "preco": 1, "estoque": 1, "categoria": "xpto"}
    )
    checar("400 categoria inválida", r.json["erro"].startswith("Categoria inválida."), r.json)
    r = cliente.post("/produtos", json={"nome": "abc", "preco": "muito", "estoque": 1})
    checar("400 (não 500) para preço não numérico", r.status_code == 400, r.status_code)
    r = cliente.post("/produtos", data="nao-json", content_type="text/plain")
    checar("400 (não 500) para corpo inválido", r.status_code == 400, r.status_code)
    checar("mensagem original", r.json["erro"] == "Dados inválidos", r.json)

    print("\n[PUT /produtos/<id>]")
    r = cliente.put(
        f"/produtos/{novo_id}",
        json={"nome": "Produto Teste Editado", "preco": 20.0, "estoque": 7, "categoria": "geral"},
    )
    checar("200", r.status_code == 200, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Produto atualizado", r.json)
    r = cliente.get(f"/produtos/{novo_id}")
    checar("alteração persistida", r.json["dados"]["nome"] == "Produto Teste Editado", r.json)
    r = cliente.put(
        "/produtos/9999", json={"nome": "abc", "preco": 1, "estoque": 1}
    )
    checar("404 inexistente", r.status_code == 404, r.status_code)
    r = cliente.put(
        f"/produtos/{novo_id}", json={"nome": "a", "preco": 1, "estoque": 1}
    )
    checar(
        "validação de nome agora aplicada no PUT (era divergente)",
        r.status_code == 400 and r.json["erro"] == "Nome muito curto",
        r.json,
    )

    print("\n[DELETE /produtos/<id>]")
    r = cliente.delete(f"/produtos/{novo_id}")
    checar("200", r.status_code == 200, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Produto deletado", r.json)
    r = cliente.delete(f"/produtos/{novo_id}")
    checar("404 já deletado", r.status_code == 404, r.status_code)

    print("\n[GET /usuarios]")
    r = cliente.get("/usuarios")
    checar("200", r.status_code == 200, r.status_code)
    checar("3 usuários do seed", len(r.json["dados"]) == 3, len(r.json["dados"]))
    checar(
        "senha NÃO exposta",
        all("senha" not in u for u in r.json["dados"]),
        r.json["dados"][0],
    )
    checar(
        "campos públicos",
        set(r.json["dados"][0]) == {"id", "nome", "email", "tipo", "criado_em"},
        set(r.json["dados"][0]),
    )

    print("\n[GET /usuarios/<id>]")
    r = cliente.get("/usuarios/1")
    checar("200", r.status_code == 200, r.status_code)
    checar("senha NÃO exposta", "senha" not in r.json["dados"], r.json)
    r = cliente.get("/usuarios/9999")
    checar("404 inexistente", r.status_code == 404, r.status_code)
    checar("mensagem original", r.json["erro"] == "Usuário não encontrado", r.json)

    print("\n[POST /usuarios]")
    r = cliente.post(
        "/usuarios", json={"nome": "Teste", "email": "teste@x.com", "senha": "segredo"}
    )
    checar("201", r.status_code == 201, r.status_code)
    checar("id retornado", isinstance(r.json["dados"]["id"], int), r.json)
    r = cliente.post("/usuarios", json={"nome": "Teste"})
    checar(
        "400 campos faltando",
        r.json["erro"] == "Nome, email e senha são obrigatórios",
        r.json,
    )

    print("\n[POST /login]")
    r = cliente.post("/login", json={"email": "teste@x.com", "senha": "segredo"})
    checar("200 credenciais válidas", r.status_code == 200, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Login OK", r.json)
    checar(
        "campos do usuário autenticado",
        set(r.json["dados"]) == {"id", "nome", "email", "tipo"},
        set(r.json["dados"]),
    )
    r = cliente.post("/login", json={"email": "admin@loja.com", "senha": "admin123"})
    checar("200 usuário do seed (senha em hash)", r.status_code == 200, r.status_code)
    r = cliente.post("/login", json={"email": "teste@x.com", "senha": "errada"})
    checar("401 senha errada", r.status_code == 401, r.status_code)
    checar("mensagem original", r.json["erro"] == "Email ou senha inválidos", r.json)
    r = cliente.post("/login", json={"email": "x", "senha": ""})
    checar("400 campos vazios", r.json["erro"] == "Email e senha são obrigatórios", r.json)
    r = cliente.post("/login", json={"email": "' OR '1'='1", "senha": "' OR '1'='1"})
    checar("injeção no login recusada", r.status_code == 401, r.status_code)

    print("\n[POST /pedidos]")
    estoque_antes = cliente.get("/produtos/2").json["dados"]["estoque"]
    r = cliente.post(
        "/pedidos",
        json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 1}, {"produto_id": 2, "quantidade": 2}]},
    )
    checar("201", r.status_code == 201, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Pedido criado com sucesso", r.json)
    esperado = 5999.99 * 1 + 89.90 * 2
    checar(
        "total calculado igual ao original",
        abs(r.json["dados"]["total"] - esperado) < 1e-9,
        (r.json["dados"]["total"], esperado),
    )
    pedido_id = r.json["dados"]["pedido_id"]
    estoque_depois = cliente.get("/produtos/2").json["dados"]["estoque"]
    checar("estoque debitado", estoque_depois == estoque_antes - 2, (estoque_antes, estoque_depois))

    r = cliente.post("/pedidos", json={"itens": [{"produto_id": 1, "quantidade": 1}]})
    checar("400 sem usuario_id", r.json["erro"] == "Usuario ID é obrigatório", r.json)
    r = cliente.post("/pedidos", json={"usuario_id": 2, "itens": []})
    checar(
        "400 sem itens", r.json["erro"] == "Pedido deve ter pelo menos 1 item", r.json
    )
    r = cliente.post(
        "/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 9999, "quantidade": 1}]}
    )
    checar("400 produto inexistente", r.json["erro"] == "Produto 9999 não encontrado", r.json)
    r = cliente.post(
        "/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": 999999}]}
    )
    checar(
        "400 estoque insuficiente",
        r.json["erro"] == "Estoque insuficiente para Notebook Gamer",
        r.json,
    )
    estoque_pre_rollback = cliente.get("/produtos/1").json["dados"]["estoque"]
    r = cliente.post(
        "/pedidos",
        json={
            "usuario_id": 2,
            "itens": [{"produto_id": 1, "quantidade": 1}, {"produto_id": 9999, "quantidade": 1}],
        },
    )
    checar("400 item inválido no meio do pedido", r.status_code == 400, r.status_code)
    checar(
        "rollback: estoque do item válido intacto",
        cliente.get("/produtos/1").json["dados"]["estoque"] == estoque_pre_rollback,
        estoque_pre_rollback,
    )
    r = cliente.post(
        "/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 1, "quantidade": -5}]}
    )
    checar(
        "400 (não crédito de estoque) para quantidade negativa",
        r.status_code == 400,
        r.status_code,
    )
    r = cliente.post("/pedidos", json={"usuario_id": 2, "itens": [{"produto_id": 1}]})
    checar("400 (não 500) para item sem quantidade", r.status_code == 400, r.status_code)

    print("\n[GET /pedidos]")
    r = cliente.get("/pedidos")
    checar("200", r.status_code == 200, r.status_code)
    checar("1 pedido criado", len(r.json["dados"]) == 1, len(r.json["dados"]))
    pedido = r.json["dados"][0]
    checar(
        "campos do pedido",
        set(pedido) == {"id", "usuario_id", "status", "total", "criado_em", "itens"},
        set(pedido),
    )
    checar("2 itens agrupados", len(pedido["itens"]) == 2, pedido["itens"])
    checar(
        "campos do item",
        set(pedido["itens"][0])
        == {"produto_id", "produto_nome", "quantidade", "preco_unitario"},
        set(pedido["itens"][0]),
    )
    checar(
        "nome do produto resolvido no JOIN",
        pedido["itens"][0]["produto_nome"] == "Notebook Gamer",
        pedido["itens"][0],
    )
    checar("status inicial pendente", pedido["status"] == "pendente", pedido["status"])

    print("\n[GET /pedidos/usuario/<id>]")
    r = cliente.get("/pedidos/usuario/2")
    checar("200", r.status_code == 200, r.status_code)
    checar("1 pedido do usuário 2", len(r.json["dados"]) == 1, len(r.json["dados"]))
    r = cliente.get("/pedidos/usuario/999")
    checar("lista vazia para usuário sem pedidos", r.json["dados"] == [], r.json)

    print("\n[PUT /pedidos/<id>/status]")
    r = cliente.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"})
    checar("200", r.status_code == 200, r.status_code)
    checar("mensagem original", r.json["mensagem"] == "Status atualizado", r.json)
    checar(
        "status persistido",
        cliente.get("/pedidos").json["dados"][0]["status"] == "aprovado",
    )
    r = cliente.put(f"/pedidos/{pedido_id}/status", json={"status": "xpto"})
    checar("400 status inválido", r.json["erro"] == "Status inválido", r.json)
    r = cliente.put("/pedidos/9999/status", json={"status": "aprovado"})
    checar(
        "404 pedido inexistente (antes respondia 200)", r.status_code == 404, r.status_code
    )

    print("\n[GET /relatorios/vendas]")
    r = cliente.get("/relatorios/vendas")
    checar("200", r.status_code == 200, r.status_code)
    relatorio = r.json["dados"]
    checar(
        "campos do relatório",
        set(relatorio)
        == {
            "total_pedidos",
            "faturamento_bruto",
            "desconto_aplicavel",
            "faturamento_liquido",
            "pedidos_pendentes",
            "pedidos_aprovados",
            "pedidos_cancelados",
            "ticket_medio",
        },
        set(relatorio),
    )
    checar("1 pedido", relatorio["total_pedidos"] == 1, relatorio)
    checar(
        "faturamento bruto", relatorio["faturamento_bruto"] == round(esperado, 2), relatorio
    )
    # 5000 < 6179.79 <= 10000 -> faixa de 5%, idêntica à cadeia de elif original.
    checar(
        "faixa de desconto de 5% (5000 < faturamento <= 10000)",
        relatorio["desconto_aplicavel"] == round(esperado * 0.05, 2),
        relatorio,
    )
    checar(
        "faturamento líquido",
        relatorio["faturamento_liquido"] == round(esperado - esperado * 0.05, 2),
        relatorio,
    )
    checar("ticket médio", relatorio["ticket_medio"] == round(esperado, 2), relatorio)
    checar("contagem por status", relatorio["pedidos_aprovados"] == 1, relatorio)

    print("\n[rotas administrativas removidas]")
    r = cliente.post("/admin/query", json={"sql": "SELECT * FROM usuarios"})
    checar("POST /admin/query -> 404", r.status_code == 404, r.status_code)
    r = cliente.post("/admin/reset-db")
    checar("POST /admin/reset-db -> 404", r.status_code == 404, r.status_code)

    print("\n[error handling]")
    r = cliente.get("/rota-que-nao-existe")
    checar("404 em JSON", r.status_code == 404 and r.json["sucesso"] is False, r.data[:80])
    r = cliente.delete("/produtos")
    checar("405 método não permitido", r.status_code == 405, r.status_code)

    print("\n[relatório vazio]")
    banco_vazio = os.path.join(tempfile.mkdtemp(), "vazio.db")
    app_vazio = create_app(
        load_settings(
            {
                "APP_ENV": "development",
                "SECRET_KEY": "x",
                "DATABASE_PATH": banco_vazio,
                "SEED_DATABASE": "false",
            }
        )
    )
    r = app_vazio.test_client().get("/relatorios/vendas")
    checar("200 sem pedidos", r.status_code == 200, r.status_code)
    checar(
        "zeros em vez de divisão por zero",
        r.json["dados"]["ticket_medio"] == 0 and r.json["dados"]["faturamento_bruto"] == 0,
        r.json,
    )

    print("\n" + "=" * 50)
    if falhas:
        print(f"FALHAS: {len(falhas)} de {total}")
        for falha in falhas:
            print(f"  - {falha}")
        print("=" * 50)
        return 1
    print(f"OK: {total}/{total} verificações passaram")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
