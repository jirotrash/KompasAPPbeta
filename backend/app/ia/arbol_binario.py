# ============================================================
# Árbol binario de búsqueda de las paradas de una ruta (implementación propia, sin librerías)
# ============================================================
# Clave de cada nodo: km acumulado desde el inicio de la ruta. Como las paradas ya vienen ordenadas
# por km, insertarlas una por una produciría un árbol degenerado (cada nodo solo tiene hijo derecho:
# una lista con altura n y búsquedas O(n)). construir_balanceado() usa la mediana como raíz y repite
# en cada mitad, así la altura es ⌈log₂(n + 1)⌉ y buscar / mas_cercano cuestan O(log n).
#
# Uso en "¿Cómo llego?": se proyecta el origen (o el destino) sobre el trazo, se obtiene su km y
# mas_cercano(km) da la parada donde subir (o bajar).
# ============================================================

from typing import Any


class NodoParada:
    __slots__ = ("clave", "parada", "izquierdo", "derecho")

    def __init__(self, clave: float, parada: dict[str, Any]):
        self.clave = clave
        self.parada = parada  # {id, nombre, lat, lng}
        self.izquierdo: NodoParada | None = None
        self.derecho: NodoParada | None = None

    def a_dict(self) -> dict[str, Any]:
        return {
            "clave": round(self.clave, 4),
            "parada": self.parada,
            "izquierdo": self.izquierdo.a_dict() if self.izquierdo else None,
            "derecho": self.derecho.a_dict() if self.derecho else None,
        }


class ArbolParadas:
    def __init__(self) -> None:
        self.raiz: NodoParada | None = None

    # ───────────── Construcción ─────────────

    @classmethod
    def construir_balanceado(cls, paradas_ordenadas: list[dict[str, Any]]) -> "ArbolParadas":
        """`paradas_ordenadas`: [{km, id, nombre, lat, lng}, ...] ordenadas por km. La mediana es la raíz."""

        def armar(inicio: int, fin: int) -> NodoParada | None:
            if inicio > fin:
                return None
            medio = (inicio + fin + 1) // 2
            p = paradas_ordenadas[medio]
            nodo = NodoParada(p["km"], {k: v for k, v in p.items() if k != "km"})
            nodo.izquierdo = armar(inicio, medio - 1)
            nodo.derecho = armar(medio + 1, fin)
            return nodo

        arbol = cls()
        arbol.raiz = armar(0, len(paradas_ordenadas) - 1)
        return arbol

    def insertar(self, clave: float, parada: dict[str, Any]) -> NodoParada:
        """Inserción clásica de un ABB (menores a la izquierda). Una clave repetida reemplaza la parada."""
        nuevo = NodoParada(clave, parada)
        if self.raiz is None:
            self.raiz = nuevo
            return nuevo
        actual = self.raiz
        while True:
            if clave == actual.clave:
                actual.parada = parada
                return actual
            lado = "izquierdo" if clave < actual.clave else "derecho"
            hijo = getattr(actual, lado)
            if hijo is None:
                setattr(actual, lado, nuevo)
                return nuevo
            actual = hijo

    # ───────────── Búsquedas ─────────────

    def buscar(self, km: float, tolerancia: float = 1e-9) -> NodoParada | None:
        """La parada con clave = km (± tolerancia), o None."""
        actual = self.raiz
        while actual is not None:
            if abs(km - actual.clave) <= tolerancia:
                return actual
            actual = actual.izquierdo if km < actual.clave else actual.derecho
        return None

    def mas_cercano(self, km: float) -> tuple[NodoParada | None, list[float]]:
        """(parada con la clave más cercana a km, claves visitadas desde la raíz).

        Al bajar por el árbol se guardan el predecesor (mayor clave ≤ km) y el sucesor (menor clave ≥ km);
        la respuesta es el más cercano de los dos. A igual distancia gana el predecesor.
        """
        predecesor: NodoParada | None = None
        sucesor: NodoParada | None = None
        visitados: list[float] = []
        actual = self.raiz
        while actual is not None:
            visitados.append(actual.clave)
            if km == actual.clave:
                return actual, visitados
            if km < actual.clave:
                sucesor = actual
                actual = actual.izquierdo
            else:
                predecesor = actual
                actual = actual.derecho
        if predecesor is None or sucesor is None:
            return predecesor or sucesor, visitados
        mejor = predecesor if km - predecesor.clave <= sucesor.clave - km else sucesor
        return mejor, visitados

    def rango(self, desde_km: float, hasta_km: float) -> list[NodoParada]:
        """Paradas con desde_km ≤ clave ≤ hasta_km, en orden (inorden podado)."""
        salida: list[NodoParada] = []

        def visitar(nodo: NodoParada | None) -> None:
            if nodo is None:
                return
            if desde_km < nodo.clave:
                visitar(nodo.izquierdo)
            if desde_km <= nodo.clave <= hasta_km:
                salida.append(nodo)
            if nodo.clave < hasta_km:
                visitar(nodo.derecho)

        visitar(self.raiz)
        return salida

    # ───────────── Recorridos ─────────────

    def inorden(self) -> list[NodoParada]:
        """Izquierdo → raíz → derecho: las paradas en orden de km."""
        salida: list[NodoParada] = []

        def visitar(nodo: NodoParada | None) -> None:
            if nodo:
                visitar(nodo.izquierdo)
                salida.append(nodo)
                visitar(nodo.derecho)

        visitar(self.raiz)
        return salida

    def preorden(self) -> list[NodoParada]:
        """Raíz → izquierdo → derecho."""
        salida: list[NodoParada] = []

        def visitar(nodo: NodoParada | None) -> None:
            if nodo:
                salida.append(nodo)
                visitar(nodo.izquierdo)
                visitar(nodo.derecho)

        visitar(self.raiz)
        return salida

    def postorden(self) -> list[NodoParada]:
        """Izquierdo → derecho → raíz."""
        salida: list[NodoParada] = []

        def visitar(nodo: NodoParada | None) -> None:
            if nodo:
                visitar(nodo.izquierdo)
                visitar(nodo.derecho)
                salida.append(nodo)

        visitar(self.raiz)
        return salida

    # ───────────── Medidas ─────────────

    def altura(self) -> int:
        """Número de niveles: árbol vacío = 0, solo la raíz = 1."""

        def medir(nodo: NodoParada | None) -> int:
            return 0 if nodo is None else 1 + max(medir(nodo.izquierdo), medir(nodo.derecho))

        return medir(self.raiz)

    def total_nodos(self) -> int:
        def contar(nodo: NodoParada | None) -> int:
            return 0 if nodo is None else 1 + contar(nodo.izquierdo) + contar(nodo.derecho)

        return contar(self.raiz)

    def a_dict(self) -> dict[str, Any] | None:
        return self.raiz.a_dict() if self.raiz else None

    def resumen(self) -> dict[str, Any]:
        """Lo que regresa GET /api/rutas/{id}/arbol."""

        def lista(nodos: list[NodoParada]) -> list[dict[str, Any]]:
            return [{"km": round(n.clave, 4), **n.parada} for n in nodos]

        return {
            "raiz": self.a_dict(),
            "altura": self.altura(),
            "total_nodos": self.total_nodos(),
            "inorden": lista(self.inorden()),
            "preorden": lista(self.preorden()),
            "postorden": lista(self.postorden()),
        }
