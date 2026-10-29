from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

TIMEOUT = 8  # segundos de espera máxima por la API


def llamar_api(metodo, ruta, token=None, **kwargs):
    """Hace una petición a la API FastAPI (agrega el JWT si se pasa `token`)."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return requests.request(
        metodo, f"{settings.API_URL}{ruta}", headers=headers, timeout=TIMEOUT, **kwargs
    )


def detalle_error(respuesta, por_defecto):
    """Saca el mensaje `detail` que devuelve FastAPI (si es un texto)."""
    try:
        detalle = respuesta.json().get("detail")
    except ValueError:
        return por_defecto
    return detalle if isinstance(detalle, str) else por_defecto


def login_requerido(vista):
    """Si no hay JWT en la sesión, manda al login."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.warning(request, "Inicia sesión para ver el catálogo.")
            return redirect("login")
        return vista(request, *args, **kwargs)
    return envoltura


def login_view(request):
    if request.session.get("token"):
        return redirect("catalogo")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        try:
            r = llamar_api("post", "/usuarios/login", json={"email": email, "password": password})
        except requests.RequestException:
            messages.error(request, "No se pudo conectar con la API. ¿Está corriendo uvicorn?")
            return render(request, "store/login.html", {"email": email})

        if r.status_code == 200:
            datos = r.json()
            request.session.cycle_key()  # nueva sesión al autenticarse
            request.session["token"] = datos["access_token"]
            request.session["usuario"] = {
                "username": datos["usuario"]["username"],
                "email": datos["usuario"]["email"],
                "full_name": datos["usuario"].get("full_name"),
            }
            return redirect("catalogo")

        if r.status_code == 422:
            messages.error(request, "Revisa el formato del correo.")
        else:
            messages.error(request, detalle_error(r, "No se pudo iniciar sesión."))
        return render(request, "store/login.html", {"email": email})

    return render(request, "store/login.html")


def registro(request):
    if request.session.get("token"):
        return redirect("catalogo")

    if request.method == "POST":
        form = {
            "username": request.POST.get("username", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "full_name": request.POST.get("full_name", "").strip(),
        }
        password = request.POST.get("password", "")

        if password != request.POST.get("password2", ""):
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "store/registro.html", {"form": form})

        payload = {**form, "password": password}
        if not payload["full_name"]:
            payload["full_name"] = None
        try:
            r = llamar_api("post", "/usuarios/", json=payload)
        except requests.RequestException:
            messages.error(request, "No se pudo conectar con la API. ¿Está corriendo uvicorn?")
            return render(request, "store/registro.html", {"form": form})

        if r.status_code == 201:
            messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
            return redirect("login")

        if r.status_code == 422:
            messages.error(
                request,
                "Datos inválidos: usuario de 3 a 50 caracteres, correo válido "
                "y contraseña de 6 a 72 caracteres.",
            )
        else:
            messages.error(request, detalle_error(r, "No se pudo crear la cuenta."))
        return render(request, "store/registro.html", {"form": form})

    return render(request, "store/registro.html")


@require_POST
def logout_view(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("login")


@login_requerido
def catalogo(request):
    token = request.session["token"]

    try:
        # Verifica que el JWT siga siendo válido (firma y expiración las revisa la API)
        me = llamar_api("get", "/usuarios/me", token=token)
        if me.status_code == 401:
            request.session.flush()
            messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
            return redirect("login")

        r = llamar_api("get", "/productos/")
        r.raise_for_status()
        productos = r.json()
    except (requests.RequestException, ValueError):
        messages.error(request, "No se pudo cargar el catálogo desde la API.")
        return render(request, "store/catalogo.html", {"productos": [], "categorias": []})

    # Django no permite variables que empiecen con "_", así que pasamos _id -> id
    productos = [{**p, "id": p.get("_id")} for p in productos if p.get("activo", True)]

    categorias = sorted({p["categoria"] for p in productos if p.get("categoria")})

    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    if q:
        productos = [
            p for p in productos
            if q.lower() in p["nombre"].lower() or q.lower() in (p.get("descripcion") or "").lower()
        ]
    if categoria:
        productos = [p for p in productos if p.get("categoria") == categoria]

    return render(request, "store/catalogo.html", {
        "productos": productos,
        "categorias": categorias,
        "q": q,
        "categoria": categoria,
    })
