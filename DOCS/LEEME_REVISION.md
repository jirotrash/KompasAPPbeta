# Primer sprint de Brújula Urbana — entrega 0.4.0

La carpeta `Brujula-Urbana/` contiene los entregables completos de IA y manual técnico. Esta revisión añade el diagrama de endpoints del equipo, la transcripción de 15 operaciones y una guía que identifica las seis tareas de Einar.

## Abrir en VS Code

Descargar este ZIP en Descargas y ejecutar en PowerShell de Windows:

```powershell
Set-Location "$env:USERPROFILE\Downloads"
Expand-Archive -LiteralPath ".\Entregables_Brujula_Urbana_Einar_v0_4.zip" -DestinationPath ".\Entrega-Brujula-v04"
code ".\Entrega-Brujula-v04\Brujula-Urbana"
```

Si ya existe la carpeta de destino, usar otra nueva para no sobrescribir trabajo. Si `code` no está disponible, abrir VS Code y seleccionar Archivo → Abrir carpeta.

Comenzar en `docs/sprint-1/guia-de-entrega.md`. Presionar Ctrl + Shift + V para leer su vista previa. Allí están las seis tareas, sus enlaces, lo que se debe explicar y los comandos de la demo. Los dos diagramas originales están en `docs/referencias` y se pueden abrir como imágenes.

## Contenido principal

| Tarea | Archivo dentro del proyecto |
| --- | --- |
| 1. Variables | `docs/sistema-experto/variables.md` |
| 2. Veinte reglas | `docs/sistema-experto/reglas.md` y `reglas.json` |
| 3. Ejemplo de inferencia | `docs/sistema-experto/ejemplo-inferencia.md` |
| 4. Diccionario | `docs/manual-tecnico/diccionario-datos.md` |
| 5. Manual del sistema experto | `docs/manual-tecnico/sistema-experto.md` |
| 6. Arquitectura, tecnologías, API e instalación | `docs/manual-tecnico/arquitectura-api-instalacion.md` |

Complementos de la tarea 6: `docs/api/catalogo-endpoints.md` y `docs/api/integracion-sistema-experto.md`.

## Aplicar a Git: elegir una sola alternativa

El ZIP no contiene el directorio de Git. Leer los archivos desde la copia extraída no publica cambios. Los parches permiten incorporarlos al clon del repositorio conservando los commits.

Antes de aplicar un parche, ejecutar `git status` en el clon y comprobar que no haya cambios pendientes ni otra operación Git en curso. Si Git necesita identidad, configurar nombre y correo reales antes de `git am`:

```powershell
git config user.name "TU NOMBRE"
git config user.email "TU CORREO DE GITHUB"
```

### A. Si ya se incorporó la revisión 0.3.0

Desde el clon que contiene esa revisión, sin modificaciones posteriores incompatibles:

```powershell
git switch docs/einar-sistema-experto-manual
git am "$env:USERPROFILE\Downloads\Entrega-Brujula-v04\actualizacion-endpoints-v0.4.patch"
```

Este parche contiene únicamente el cambio de 0.3.0 a 0.4.0. No requiere que los hashes sean idénticos a los de esta entrega: `git am` puede generar otros hashes al aplicar commits. Sí requiere que el contenido de partida corresponda a la revisión anterior.

### B. Si se parte del repositorio inicial

Usar una carpeta nueva. El paquete completo está preparado sobre el main inicial `83ae9356c85f6abbcab119b0d082c6923ff978b2`. Si main ya contiene cambios posteriores, revisar la diferencia antes de continuar.

```powershell
Set-Location "$env:USERPROFILE\Downloads"
git clone https://github.com/Sebastianyael/Brujula-Urbana.git Brujula-Urbana-sprint1
Set-Location .\Brujula-Urbana-sprint1
git switch -c docs/einar-sistema-experto-manual origin/main
git am "$env:USERPROFILE\Downloads\Entrega-Brujula-v04\cambios-completos-v0.4.patch"
code .
```

No aplicar A y B a la misma historia ni volver a aplicar revisiones que ya estén incorporadas. Si cualquier comando falla, detenerse en ese paso. Si `git am` informa un conflicto, revisarlo o usar `git am --abort` para cancelar esa aplicación; no avanzar al push.

### Publicar la rama después de revisar

Con la aplicación del parche terminada y desde el clon:

```powershell
git status
git push -u origin docs/einar-sistema-experto-manual
```

Crear un pull request hacia `main` y utilizar `PR_BORRADOR.md` como descripción. La aprobación e integración corresponden a backend. Esta entrega no publica una rama remota ni fusiona cambios.

## Alcance y comprobaciones

El diagrama identifica FastAPI y MySQL, 15 endpoints y siete candados. No aporta cuerpos/respuestas HTTP, versión de dependencias, firma de `recomendar()` ni instrucciones de arranque. Esos elementos quedan por acordar, así como el guardado antes o después de seleccionar una de las opciones.

La observación de una salida real, el esquema MySQL implementado y la instalación del servidor siguen pendientes. La demo y los documentos están disponibles para revisión del primer sprint.

Se comprobaron 89 enlaces locales, el catálogo y la conservación de 39 campos, ocho PK y nueve FK. La fuente de endpoints se conserva idéntica al adjunto. Motor, variables, reglas, casos y ejemplo no cambiaron. Las 36 comprobaciones de inferencia y la activación de las 20 reglas son evidencia de la versión previa; no se repitieron pruebas de aplicación ni se ejecutó PowerShell en el entorno de preparación.

Rama local: `docs/einar-sistema-experto-manual`.
Commit local: `49756db3caccdbfc6518e83013e2f2f7a8ac7da2`.
Documentación: 0.4.0. Reglas: 0.1.0.
