from django import forms


class DatasetUploadForm(forms.Form):
    archivo = forms.FileField(
        label="Selecciona tu dataset (CSV o XLSX)",
        help_text="Se guardará como data/Final_data.csv"
    )

    def clean_archivo(self):
        f = self.cleaned_data['archivo']
        nombre = f.name.lower()
        if not (nombre.endswith('.csv') or nombre.endswith('.xlsx')):
            raise forms.ValidationError("Solo se permiten archivos .csv o .xlsx")
        return f


class PredictionForm(forms.Form):
    GENERO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino')]
    TIPO_CHOICES = [
        ('Cardio', 'Cardio'),
        ('Fuerza', 'Fuerza'),
        ('Mixto', 'Mixto'),
        ('Movilidad', 'Movilidad/Estiramientos'),
    ]
    NIVEL_CHOICES = [
        ('Principiante', 'Principiante'),
        ('Intermedio', 'Intermedio'),
        ('Avanzado', 'Avanzado'),
    ]

    edad = forms.IntegerField(
        min_value=10, max_value=100, label='Edad',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    genero = forms.ChoiceField(
        choices=GENERO_CHOICES, label='Género',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    peso = forms.FloatField(
        min_value=30, max_value=250, label='Peso (kg)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    altura = forms.FloatField(
        min_value=1.2, max_value=2.3, label='Altura (m)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    reposo_latidos = forms.IntegerField(
        min_value=35, max_value=120, label='Latidos en reposo (ppm)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    promedio_latidos = forms.IntegerField(
        min_value=60, max_value=200, label='Latidos promedio en sesión (ppm)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    duracion_sesion = forms.FloatField(
        min_value=0.1, max_value=6, label='Duración de sesión (horas)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    calorias_quemadas = forms.IntegerField(
        min_value=0, max_value=6000, label='Calorías quemadas por sesión',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    tipo_entrenamiento = forms.ChoiceField(
        choices=TIPO_CHOICES, label='Tipo de entrenamiento',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    porcentaje_grasa = forms.FloatField(
        min_value=3, max_value=60, label='Porcentaje de grasa (%)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    agua_litros = forms.FloatField(
        min_value=0, max_value=10, label='Agua al día (litros)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    frecuencia = forms.IntegerField(
        min_value=0, max_value=7, label='Frecuencia semanal (días)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    nivel_experiencia = forms.ChoiceField(
        choices=NIVEL_CHOICES, label='Nivel de experiencia',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned = super().clean()
        prom = cleaned.get('promedio_latidos')
        rep = cleaned.get('reposo_latidos')
        if prom is not None and rep is not None and prom <= rep:
            self.add_error(
                'promedio_latidos',
                'El promedio de latidos debe ser mayor que los latidos en reposo.'
            )
        return cleaned
    
    def to_dataset_row(self):
        """
        Retorna un dict con claves alineadas a las columnas del CSV Final_data.csv.
        Ajusta los nombres si tu archivo usa encabezados distintos.
        """
        c = self.cleaned_data
        imc = round(c['peso'] / (c['altura'] ** 2), 2)

        return {
            "Edad": c["edad"],
            "Genero": c["genero"],
            "Peso (kg)": c["peso"],
            "Altura (m)": c["altura"],
            "Promedio_LATIDOS_POR_MINUTO": c["promedio_latidos"],
            "Reposo_LATIDOS_POR_MINUTO": c["reposo_latidos"],
            "Duracion_Sesion (horas)": c["duracion_sesion"],
            "Calorias_Quemadas": c["calorias_quemadas"],
            "Tipo_Entrenamiento": c["tipo_entrenamiento"],
            "Porcentaje_Grasa": c["porcentaje_grasa"],
            "Agua (litros)": c["agua_litros"],
            "Frecuencia (dias/semanal)": c["frecuencia"],
            "Nivel_Experiencia": c["nivel_experiencia"],
            "Indice_De_Masa_Corporal": imc,
        }

from django import forms

class ContactForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre completo",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"})
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tu@correo.com"})
    )
    asunto = forms.CharField(
        label="Asunto",
        max_length=120,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Motivo del mensaje"})
    )
    mensaje = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Cuéntanos en qué podemos ayudarte"})
    )
    acepta = forms.BooleanField(
        label="Acepto ser contactad@ para recibir respuesta",
        required=True
    )
