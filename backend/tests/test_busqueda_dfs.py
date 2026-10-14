"""Pruebas unitarias del algoritmo DFS académico, sin base de datos ni red."""

from app.ia.busqueda_dfs import busqueda_dfs_transporte, planificar_rutas_dfs


def test_dfs_controla_ciclos_y_encuentra_todas_las_rutas():
    grafo = {
        "A": [{"destino": "B"}, {"destino": "C"}],
        "B": [{"destino": "A"}, {"destino": "D"}],
        "C": [{"destino": "D"}],
        "D": [],
    }

    rutas, exploracion, traza = busqueda_dfs_transporte(grafo, "A", "D", limite_profundidad=2)

    assert rutas == [["A", "B", "D"], ["A", "C", "D"]]
    assert exploracion == ["A", "B", "D", "C", "D"]
    assert any(paso["tipo"] == "ciclo_evitado" for paso in traza)
    assert [paso["tipo"] for paso in traza].count("objetivo") == 2


def test_dfs_respeta_el_limite_de_profundidad_en_aristas():
    grafo = {"A": [{"destino": "B"}], "B": [{"destino": "C"}], "C": []}

    rutas, _, traza = busqueda_dfs_transporte(grafo, "A", "C", limite_profundidad=1)

    assert rutas == []
    assert any(paso["tipo"] == "limite" for paso in traza)


def test_servicio_identifica_la_red_como_no_verificada():
    resultado = planificar_rutas_dfs("TerminalToluca", "CentroToluca")

    assert resultado["exito"] is True
    assert resultado["datos_verificados"] is False
    assert "demostración académica" in resultado["aviso"]
