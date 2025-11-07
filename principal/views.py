from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import pandas as pd

def home(request):
    return render(request, 'principal/home.html')

def probar_dataset(request):
    ruta = settings.DATA_DIR / 'Final_data.csv'   # <-- tu archivo
    # Si tu CSV usa ';', cambia sep=';'
    df = pd.read_csv(ruta)  
    filas, cols = df.shape
    cols_str = ", ".join(df.columns.tolist())
    preview = df.head(5).to_string(index=False)
    html = (
        f"OK ✅ {ruta.name}<br>"
        f"Filas: {filas} | Columnas: {cols}<br>"
        f"Columnas: {cols_str}<br><br>"
        f"<pre>{preview}</pre>"
    )
    return HttpResponse(html)