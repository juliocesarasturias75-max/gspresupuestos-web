"""
GSPresupuestos Web - API mínima para Render
Versión inicial: comprueba que el despliegue funciona.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="GSPresupuestos Web")


@app.get("/", response_class=HTMLResponse)
def inicio():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GSPresupuestos Web</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f4f8; margin: 0; padding: 40px; }
            .card { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px;
                    padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #1e40af; }
            .ok { color: #10b981; font-size: 48px; }
            p { color: #64748b; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="ok">✅</div>
            <h1>GSPresupuestos Web</h1>
            <p>La aplicación está online en Render.</p>
            <p>Próximo paso: conectar la lógica de presupuestos.</p>
        </div>
    </body>
    </html>
    """


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "gspresupuestos-web"}
