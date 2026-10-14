"""
Distancia Euclidiana vs. Distancia Manhattan (interactivo, versión de escritorio)
Usa las mismas funciones que la API y la app: app/ia/metricas_distancia.py

Desde la carpeta backend:
    pip install matplotlib          (y en WSL/Ubuntu: sudo apt install python3-tk)
    python -m scripts.distancias_clic

Se abre la gráfica y tú colocas los puntos con el mouse:
  - Primer clic: punto A
  - Segundo clic: punto B  -> se dibujan las dos distancias
  - Otro clic: empieza de nuevo con un nuevo punto A
  - Clic derecho o tecla N: borrar y empezar de nuevo
"""
import math

import matplotlib
import matplotlib.pyplot as plt

from app.ia.metricas_distancia import comparar_distancias, fmt

MAX = 6       # los ejes van de 0 a 6
PASO = 1      # los clics se ajustan a la cuadrícula (0.5 = medios, None = libre)

AZUL = "royalblue"
NARANJA = "darkorange"
ROJO = "crimson"


def plural(n, singular, plural_):
    return singular if n == 1 else plural_


class Graficador:
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax
        self.puntos = []
        fig.canvas.mpl_connect("button_press_event", self.al_hacer_clic)
        fig.canvas.mpl_connect("key_press_event", self.al_presionar_tecla)
        self.dibujar()

    # ---------- Eventos ----------
    def al_hacer_clic(self, evento):
        if evento.inaxes is not self.ax or evento.xdata is None:
            return
        barra = getattr(self.fig.canvas, "toolbar", None)
        if barra is not None and getattr(barra, "mode", ""):
            return  # el usuario está usando zoom o mover de la barra
        if evento.button == 3:      # clic derecho
            self.reiniciar()
            return
        self.colocar(evento.xdata, evento.ydata)

    def al_presionar_tecla(self, evento):
        if evento.key == "n":
            self.reiniciar()

    # ---------- Lógica ----------
    @staticmethod
    def ajustar(v):
        if PASO:
            v = round(v / PASO) * PASO
        return min(max(v, 0), MAX)

    def colocar(self, x, y):
        if len(self.puntos) == 2:
            self.puntos = []
        self.puntos.append((self.ajustar(x), self.ajustar(y)))
        self.dibujar()
        if len(self.puntos) == 2:
            self.imprimir_calculos()

    def reiniciar(self):
        self.puntos = []
        self.dibujar()

    # ---------- Dibujo ----------
    def preparar_ejes(self):
        ax = self.ax
        ax.clear()
        ax.set_xlim(0, MAX)
        ax.set_ylim(0, MAX)
        ax.set_xticks(range(MAX + 1))
        ax.set_yticks(range(MAX + 1))
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", color="gray", alpha=0.7)
        ax.set_xlabel("Eje X", fontsize=12)
        ax.set_ylabel("Eje Y", fontsize=12)

        if len(self.puntos) == 0:
            instruccion = "Haz clic para colocar el punto A"
        elif len(self.puntos) == 1:
            instruccion = "Ahora haz clic para colocar el punto B"
        else:
            instruccion = "Clic para empezar de nuevo · Clic derecho o tecla N: borrar"
        ax.set_title(instruccion, fontsize=11, color="dimgray")

    def dibujar(self):
        self.preparar_ejes()
        ax = self.ax

        for i, (nombre, (x, y)) in enumerate(zip("AB", self.puntos)):
            ax.scatter(x, y, s=120, color=ROJO, zorder=5)
            # La etiqueta va del lado contrario al otro punto, sin salirse
            if len(self.puntos) == 2:
                ox, oy = self.puntos[1 - i]
                derecha, arriba = x >= ox, y >= oy
            else:
                derecha, arriba = True, True
            if x > MAX - 1:
                derecha = False
            elif x < 1:
                derecha = True
            if y > MAX - 0.5:
                arriba = False
            elif y < 0.5:
                arriba = True
            dx_txt = 10 if derecha else -10
            dy_txt = 10 if arriba else -18
            ax.annotate(f"{nombre}({fmt(x)}, {fmt(y)})", (x, y),
                        textcoords="offset points", xytext=(dx_txt, dy_txt),
                        ha="right" if dx_txt < 0 else "left",
                        fontsize=12, fontweight="bold", zorder=6)

        if len(self.puntos) == 2:
            self.dibujar_distancias(*self.puntos)

        self.fig.canvas.draw_idle()

    def dibujar_distancias(self, A, B):
        ax = self.ax
        r = comparar_distancias(A, B)
        dx, dy = r["horizontal"], r["vertical"]
        euclidiana, manhattan = r["euclidiana"], r["manhattan"]

        if dx == 0 and dy == 0:
            ax.set_title("A y B son el mismo punto: las dos distancias valen 0",
                         fontsize=11, color="dimgray")
            return

        esquina = (B[0], A[1])

        # Línea Euclidiana (directa)
        ax.plot([A[0], B[0]], [A[1], B[1]], color=AZUL, linewidth=2.5,
                label=f"Distancia Euclidiana = {fmt(euclidiana)}")

        # Camino Manhattan (horizontal y luego vertical)
        ax.plot([A[0], esquina[0], B[0]], [A[1], esquina[1], B[1]],
                color=NARANJA, linewidth=2.5, linestyle="--",
                label=f"Distancia Manhattan = {fmt(manhattan)} "
                      f"({fmt(dx)} {plural(dx, 'horizontal', 'horizontales')} + "
                      f"{fmt(dy)} {plural(dy, 'vertical', 'verticales')})")

        # Marca de ángulo recto en la esquina
        if dx > 0 and dy > 0:
            s = 0.2
            sx = 1 if A[0] > B[0] else -1   # hacia donde está A
            sy = 1 if B[1] > A[1] else -1   # hacia donde está B
            cx, cy = esquina
            ax.plot([cx + sx * s, cx + sx * s, cx], [cy, cy + sy * s, cy + sy * s],
                    color=NARANJA, linewidth=1.2)

        # Etiqueta Euclidiana: sobre la diagonal, del lado contrario a la esquina
        mx, my = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
        vx, vy = B[0] - A[0], B[1] - A[1]
        largo = math.hypot(vx, vy)
        nx, ny = -vy / largo, vx / largo
        if dx > 0 and dy > 0 and nx * (esquina[0] - mx) + ny * (esquina[1] - my) > 0:
            nx, ny = -nx, -ny
        angulo = math.degrees(math.atan2(vy, vx))
        if angulo > 90:
            angulo -= 180
        elif angulo < -90:
            angulo += 180
        ax.annotate(f"Euclidiana = {fmt(euclidiana)}", (mx, my),
                    textcoords="offset points", xytext=(14 * nx, 14 * ny),
                    rotation=angulo, rotation_mode="anchor",
                    ha="center", va="center", color=AZUL,
                    fontsize=11, fontweight="bold")

        # Etiqueta del tramo horizontal (del lado contrario a B, sin salirse)
        if dx > 0 and dy > 0:
            arriba = B[1] < A[1]
            if A[1] > MAX - 0.3:
                arriba = False
            elif A[1] < 0.3:
                arriba = True
            ax.annotate(f"{fmt(dx)} {plural(dx, 'unidad horizontal', 'unidades horizontales')}",
                        ((A[0] + B[0]) / 2, A[1]), textcoords="offset points",
                        xytext=(0, 8 if arriba else -16), ha="center",
                        color=NARANJA, fontsize=10)

        # Etiqueta del tramo vertical (del lado contrario a A, sin salirse)
        if dx > 0 and dy > 0:
            derecha = B[0] > A[0]
            if B[0] > MAX - 1:
                derecha = False
            elif B[0] < 1:
                derecha = True
            ax.annotate(f"{fmt(dy)} {plural(dy, 'unidad', 'unidades')}\n"
                        f"{plural(dy, 'vertical', 'verticales')}",
                        (B[0], (A[1] + B[1]) / 2), textcoords="offset points",
                        xytext=(8 if derecha else -8, 0),
                        ha="left" if derecha else "right", va="center",
                        color=NARANJA, fontsize=10)

        if dx == 0 or dy == 0:
            ax.set_title("Los puntos están alineados: las dos distancias coinciden",
                         fontsize=11, color="dimgray")

        # Leyenda debajo de la gráfica para que nunca tape los puntos
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=10)

    def imprimir_calculos(self):
        A, B = self.puntos
        pasos = comparar_distancias(A, B)["pasos"]
        print(f"\nA = ({fmt(A[0])}, {fmt(A[1])})   B = ({fmt(B[0])}, {fmt(B[1])})")
        print(f"  Euclidiana = {pasos['euclidiana']}")
        print(f"  Manhattan  = {pasos['manhattan']}")


def main():
    if matplotlib.get_backend().lower() == "agg":
        print("No se puede abrir una ventana: falta el soporte gráfico.")
        print("En WSL/Ubuntu instala Tkinter con:  sudo apt install python3-tk")
        return

    fig, ax = plt.subplots(figsize=(8, 9))
    fig.subplots_adjust(bottom=0.2)
    fig.suptitle("Métricas de distancia: Euclidiana vs. Manhattan", fontsize=14)
    fig.canvas.manager.set_window_title("Distancias")
    # Se guarda en una variable: matplotlib solo guarda una referencia débil
    # a los eventos, y si no la guardamos Python la borra y los clics no hacen nada.
    graficador = Graficador(fig, ax)
    print("Haz clic en la gráfica para colocar A y luego B.")
    plt.show()
    return graficador


if __name__ == "__main__":
    main()
