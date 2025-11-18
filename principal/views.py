from pathlib import Path
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect

from principal.ml import predict_estado_salud, model_loaded
from .forms import DatasetUploadForm, PredictionForm, ContactForm


def home(request):
    return render(request, 'principal/home.html')


def _leer_csv_con_fallback(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    if df.shape[1] == 1:
        df = pd.read_csv(ruta, sep=';')
    return df


def probar_dataset(request):
    ruta = settings.DATA_DIR / 'Final_data.csv'
    if not ruta.exists():
        return HttpResponse("No hay data/Final_data.csv aún.")
    try:
        df = _leer_csv_con_fallback(ruta)
    except Exception as e:
        return HttpResponse(f"No se pudo leer el CSV: {e}")

    filas, cols = df.shape
    cols_str = ", ".join(map(str, df.columns.tolist()[:15]))
    preview = df.head(5).to_string(index=False)
    html = (
        f"OK ✅ {ruta.name}<br>"
        f"Filas: {filas} | Columnas: {cols}<br>"
        f"Columnas: {cols_str}<br><br>"
        f"<pre>{preview}</pre>"
    )
    return HttpResponse(html)


def subir_dataset(request):
    form = DatasetUploadForm()
    info = None
    preview_html = None
    just_uploaded = False

    if request.method == 'POST':
        form = DatasetUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['archivo']

            hist_dir = Path(settings.MEDIA_ROOT) / 'datasets'
            hist_dir.mkdir(parents=True, exist_ok=True)
            hist_path = hist_dir / f.name
            with open(hist_path, 'wb+') as dest:
                for chunk in f.chunks():
                    dest.write(chunk)

            try:
                nombre = f.name.lower()
                if nombre.endswith('.csv'):
                    df = _leer_csv_con_fallback(hist_path)
                else:
                    df = pd.read_excel(hist_path)

                Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
                out = Path(settings.DATA_DIR) / 'Final_data.csv'
                df.to_csv(out, index=False)

                info = {
                    "filas": df.shape[0],
                    "cols": df.shape[1],
                    "nombres": ", ".join(map(str, df.columns[:15])),
                    "ruta": str(out),
                }
                preview_html = df.head(10).to_html(
                    classes="table table-sm table-striped", index=False
                )
                just_uploaded = True
                messages.success(
                    request,
                    f"Dataset cargado: {df.shape[0]} filas, {df.shape[1]} columnas."
                )
            except Exception as e:
                messages.error(request, f"Error leyendo el archivo: {e}")

        return render(
            request,
            'principal/subir_dataset.html',
            {
                "form": form,
                "info": info,
                "preview_html": preview_html,
                "just_uploaded": just_uploaded
            }
        )

    actual = Path(settings.DATA_DIR) / 'Final_data.csv'
    if actual.exists():
        try:
            df = _leer_csv_con_fallback(actual)
            info = {
                "filas": df.shape[0],
                "cols": df.shape[1],
                "nombres": ", ".join(map(str, df.columns[:15])),
                "ruta": str(actual),
            }
            preview_html = df.head(10).to_html(
                classes="table table-sm table-striped", index=False
            )
        except Exception:
            info = {"error": "No se pudo leer el CSV actual."}

    return render(
        request,
        'principal/subir_dataset.html',
        {"form": form, "info": info, "preview_html": preview_html}
    )


def _calcular_saludable(data):
    razones = []
    puntos = 0

    imc = data['peso'] / (data['altura'] ** 2)
    if 18.5 <= imc <= 29:
        puntos += 1
    else:
        razones.append(f"IMC fuera de rango recomendado (18.5–29). IMC ≈ {imc:.1f}")

    if 50 <= data['reposo_latidos'] <= 80:
        puntos += 1
    else:
        razones.append("Frecuencia cardiaca en reposo fuera de 50–80 ppm.")

    if data['agua_litros'] >= 1.5:
        puntos += 1
    else:
        razones.append("Aumenta la hidratación a ≥ 1.5 L/día.")

    if data['frecuencia'] >= 3:
        puntos += 1
    else:
        razones.append("Entrena al menos 3 días/semana.")

    if data['duracion_sesion'] >= 0.5 and 90 <= data['promedio_latidos'] <= 160:
        puntos += 1
    else:
        razones.append("Procura ≥ 30 min/sesión y mantener 90–160 ppm en actividad.")

    limite = 32 if data['genero'] == 'F' else 25
    if data['porcentaje_grasa'] <= limite:
        puntos += 1
    else:
        razones.append(f"Porcentaje de grasa por encima de lo recomendado (≤ {limite}%).")

    estado = "Saludable" if puntos >= 4 else "No saludable"
    return estado, puntos, razones, imc


def prediccion(request):
    df_info = None
    try:
        csv = settings.DATA_DIR / 'Final_data.csv'
        if csv.exists():
            dft = pd.read_csv(csv)
            if dft.shape[1] == 1:
                dft = pd.read_csv(csv, sep=';')
            df_info = {
                "filas": int(dft.shape[0]),
                "cols": int(dft.shape[1]),
                "cols_str": ", ".join(map(str, dft.columns[:15])),
            }
    except Exception:
        df_info = None

    resultado = None
    razones = []
    imc = None
    puntaje = 0

    if request.method == 'POST':
        form = PredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            etiqueta, proba = predict_estado_salud(data)
            if etiqueta is not None:
                resultado = etiqueta
                puntaje = round(proba * 100) if proba is not None else None
                razones = []
                imc = (
                    (data.get('peso') or 0)
                    / ((data.get('altura') or 1) ** 2)
                    if data.get('peso') and data.get('altura')
                    else None
                )
            else:
                resultado, puntaje, razones, imc = _calcular_saludable(data)

            request.session['ultimo_resultado_salud'] = resultado
    else:
        form = PredictionForm()

    return render(
        request,
        'principal/prediccion.html',
        {
            "form": form,
            "resultado": resultado,
            "razones": razones,
            "imc": imc,
            "puntaje": puntaje,
            "df_info": df_info,
        }
    )


def consejos(request):
    estado = request.GET.get('estado') or request.session.get('ultimo_resultado_salud', 'Saludable')

    if estado == 'No saludable':
        tips = [
            "Empieza con 3 días/semana, 30–45 min por sesión.",
            "Hidrátate: al menos 1.5–2.0 L/día.",
            "Incluye caminatas rápidas o bici a intensidad moderada.",
            "Reduce ultraprocesados, prioriza proteína magra y vegetales.",
            "Duerme 7–8 h; el descanso acelera tu progreso.",
        ]
    else:
        tips = [
            "Sostén 3–5 sesiones/semana con progresión gradual.",
            "Incluye 2–3 días de fuerza para preservar masa muscular.",
            "Prioriza proteína (1.2–1.6 g/kg) y frutas/verduras.",
            "Mantén hidratación y control del estrés.",
            "Reevalúa objetivos cada 8–12 semanas.",
        ]

    return render(request, 'principal/consejos.html', {"estado": estado, "tips": tips})


def contacto(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            data_dir = Path(settings.BASE_DIR) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            out = data_dir / "contacto.csv"

            campos = ["nombre", "correo", "asunto", "mensaje"]
            fila = [
                form.cleaned_data["nombre"],
                form.cleaned_data["correo"],
                form.cleaned_data["asunto"],
                form.cleaned_data["mensaje"].replace("\n", " ").strip(),
            ]

            nueva_linea = ",".join(['"{}"'.format(x.replace('"', "'")) for x in fila]) + "\n"
            if not out.exists():
                encabezados = ",".join(campos) + "\n"
                out.write_text(encabezados, encoding="utf-8")

            with out.open("a", encoding="utf-8") as f:
                f.write(nueva_linea)

            messages.success(request, "¡Gracias! Recibimos tu mensaje y te contactaremos pronto.")
            return redirect("principal:contacto")
        else:
            messages.error(request, "Por favor corrige los campos marcados.")
    else:
        form = ContactForm()

    info = {
        "correo_publico": "salud@vidasaludable.com",
        "telefono": "+57 300 000 0000",
        "whatsapp": "573000000000",
        "direccion": "Ibagué, Colombia",
        "instagram": "https://instagram.com/",
    }

    return render(request, "principal/contacto.html", {"form": form, "info": info})