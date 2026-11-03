<<<<<<< HEAD
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from core.models import Registro


class RegistroModelTest(TestCase):
    """Pruebas de la Fase 1 (Criterio 2.1.1): Base de datos, modelo y borrado lógico."""

    def test_creacion_registro_y_soft_delete(self):
        reg = Registro.objects.create(
            nombre_carta="Charizard",
            expansion="Base Set",
            cantidad_solicitada=2,
            resultado="Se puede vender. Stock disponible: 5."
        )
        self.assertFalse(reg.eliminado)
        self.assertIsNone(reg.fecha_eliminacion)

        # Probar borrado lógico
        reg.soft_delete()
        reg.refresh_from_db()
        self.assertTrue(reg.eliminado)
        self.assertNotNull = self.assertIsNotNone(reg.fecha_eliminacion)

        # Comprobar que filter(eliminado=False) no lo devuelve
        activos = Registro.objects.filter(eliminado=False)
        self.assertNotIn(reg, activos)


class CRUDyRolesTest(TestCase):
    """Pruebas de las Fases 3 y 4 (Criterios 2.1.3 y 2.1.4): CRUD y control de acceso por roles."""

    def setUp(self):
        self.client = Client()
        # Crear grupos
        self.grp_admin, _ = Group.objects.get_or_create(name="admin")
        self.grp_normal, _ = Group.objects.get_or_create(name="normal")
        self.grp_viewer, _ = Group.objects.get_or_create(name="viewer")

        # Crear usuarios para cada rol
        self.user_admin = User.objects.create_user("u_admin", password="password123")
        self.user_admin.groups.add(self.grp_admin)

        self.user_normal = User.objects.create_user("u_normal", password="password123")
        self.user_normal.groups.add(self.grp_normal)

        self.user_viewer = User.objects.create_user("u_viewer", password="password123")
        self.user_viewer.groups.add(self.grp_viewer)

        # Registro de prueba
        self.registro = Registro.objects.create(
            nombre_carta="Pikachu",
            expansion="Crown Zenith",
            cantidad_solicitada=1,
            resultado="Se puede vender. Stock disponible: 25."
        )

    def test_anonimo_redirige_a_login(self):
        """Los usuarios no autenticados deben ser redirigidos al login."""
        resp = self.client.get(reverse('lista'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_viewer_puede_ver_lista_pero_no_crear_ni_editar_ni_eliminar(self):
        """El rol viewer solo tiene permisos de lectura."""
        self.client.login(username="u_viewer", password="password123")

        # Puede ver lista
        resp = self.client.get(reverse('lista'))
        self.assertEqual(resp.status_code, 200)

        # Intento de crear debe ser rechazado por el decorador en el servidor
        resp_crear = self.client.get(reverse('crear'))
        self.assertEqual(resp_crear.status_code, 302)
        self.assertRedirects(resp_crear, reverse('lista'))

        # Intento de editar ingresando la URL a mano debe ser rechazado
        resp_edit = self.client.get(reverse('editar', args=[self.registro.pk]))
        self.assertEqual(resp_edit.status_code, 302)
        self.assertRedirects(resp_edit, reverse('lista'))

        # Intento de eliminar ingresando la URL a mano debe ser rechazado
        resp_del = self.client.get(reverse('eliminar', args=[self.registro.pk]))
        self.assertEqual(resp_del.status_code, 302)
        self.assertRedirects(resp_del, reverse('lista'))

    def test_normal_puede_crear_pero_no_editar_ni_eliminar(self):
        """El rol normal puede ver y crear, pero no editar ni eliminar."""
        self.client.login(username="u_normal", password="password123")

        # Puede acceder a crear
        resp_crear_get = self.client.get(reverse('crear'))
        self.assertEqual(resp_crear_get.status_code, 200)

        # Puede crear un nuevo registro
        resp_crear_post = self.client.post(reverse('crear'), {
            'nombre_carta': 'Mewtwo',
            'expansion': 'Base Set',
            'cantidad_solicitada': '1'
        })
        self.assertEqual(resp_crear_post.status_code, 302)
        self.assertTrue(Registro.objects.filter(nombre_carta="Mewtwo").exists())

        # No puede editar
        resp_edit = self.client.get(reverse('editar', args=[self.registro.pk]))
        self.assertEqual(resp_edit.status_code, 302)
        self.assertRedirects(resp_edit, reverse('lista'))

        # No puede eliminar
        resp_del = self.client.get(reverse('eliminar', args=[self.registro.pk]))
        self.assertEqual(resp_del.status_code, 302)
        self.assertRedirects(resp_del, reverse('lista'))

    def test_admin_puede_editar_con_recalculo_y_eliminar(self):
        """El rol admin tiene acceso total a editar y eliminar con borrado lógico."""
        self.client.login(username="u_admin", password="password123")

        # Puede acceder a editar
        resp_edit_get = self.client.get(reverse('editar', args=[self.registro.pk]))
        self.assertEqual(resp_edit_get.status_code, 200)

        # Edita cambiando la cantidad a 9999 (supera stock -> debe recalcular a Stock insuficiente)
        resp_edit_post = self.client.post(reverse('editar', args=[self.registro.pk]), {
            'nombre_carta': 'Pikachu',
            'expansion': 'Crown Zenith',
            'cantidad_solicitada': '9999'
        })
        self.assertEqual(resp_edit_post.status_code, 302)
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.cantidad_solicitada, 9999)
        self.assertIn("Stock insuficiente", self.registro.resultado)

        # Elimina (soft delete)
        resp_del_post = self.client.post(reverse('eliminar', args=[self.registro.pk]))
        self.assertEqual(resp_del_post.status_code, 302)
        self.registro.refresh_from_db()
        self.assertTrue(self.registro.eliminado)

    def test_crear_con_numero_gigante_no_lanza_error_500_y_valida_rango(self):
        """Si se envía un número gigante (desborde de entero en SQLite), no debe caer con Error 500 y debe validar rango."""
        self.client.login(username="u_admin", password="password123")
        numero_gigante = "99999999999999999999"
        resp = self.client.post(reverse('crear'), {
            'nombre_carta': 'Charizard',
            'expansion': 'Base Set',
            'cantidad_solicitada': numero_gigante
        })
        # Debe responder con 200 (re-renderiza formulario con error), jamás 500
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.context)
        self.assertIn("10000", resp.context["error"])
        # Verificar que no se creó ningún registro con ese valor
        self.assertFalse(Registro.objects.filter(nombre_carta="Charizard").exists())

    def test_editar_con_numero_gigante_no_lanza_error_500_y_valida_rango(self):
        """Al editar con un número gigante, debe retornar error de validación sin lanzar OverflowError ni 500."""
        self.client.login(username="u_admin", password="password123")
        numero_gigante = "99999999999999999999"
        resp = self.client.post(reverse('editar', args=[self.registro.pk]), {
            'nombre_carta': 'Pikachu',
            'expansion': 'Crown Zenith',
            'cantidad_solicitada': numero_gigante
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.context)
        self.assertIn("10000", resp.context["error"])
        # Verificar que el registro original permanece inalterado
        self.registro.refresh_from_db()
        self.assertEqual(self.registro.cantidad_solicitada, 1)

    def test_crear_con_cantidad_menor_a_uno_falla_validacion(self):
        """Cantidades menores a 1 deben ser rechazadas."""
        self.client.login(username="u_normal", password="password123")
        resp = self.client.post(reverse('crear'), {
            'nombre_carta': 'Blastoise',
            'expansion': 'Base Set',
            'cantidad_solicitada': '0'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.context)
        self.assertFalse(Registro.objects.filter(nombre_carta="Blastoise").exists())

    def test_formulario_contiene_atributos_min_y_max(self):
        """El campo de cantidad solicitada en form.html debe tener min='1' y max='10000'."""
        self.client.login(username="u_admin", password="password123")
        resp = self.client.get(reverse('crear'))
        self.assertEqual(resp.status_code, 200)
        contenido = resp.content.decode("utf-8")
        self.assertIn('min="1"', contenido)
        self.assertIn('max="10000"', contenido)

    def test_operaciones_crud_generan_mensajes_de_exito(self):
        """Las acciones de crear, editar y eliminar deben generar mensajes de éxito (messages framework)."""
        self.client.login(username="u_admin", password="password123")

        # 1. Crear con éxito
        resp_crear = self.client.post(reverse('crear'), {
            'nombre_carta': 'Snorlax',
            'expansion': 'Jungle',
            'cantidad_solicitada': '2'
        }, follow=True)
        self.assertEqual(resp_crear.status_code, 200)
        mensajes_crear = [m.message for m in resp_crear.context['messages']]
        self.assertTrue(any("creado con éxito" in m for m in mensajes_crear))

        reg_creado = Registro.objects.get(nombre_carta="Snorlax")

        # 2. Editar con éxito
        resp_editar = self.client.post(reverse('editar', args=[reg_creado.pk]), {
            'nombre_carta': 'Snorlax',
            'expansion': 'Jungle',
            'cantidad_solicitada': '3'
        }, follow=True)
        self.assertEqual(resp_editar.status_code, 200)
        mensajes_editar = [m.message for m in resp_editar.context['messages']]
        self.assertTrue(any("actualizado con éxito" in m for m in mensajes_editar))

        # 3. Eliminar con éxito
        resp_eliminar = self.client.post(reverse('eliminar', args=[reg_creado.pk]), follow=True)
        self.assertEqual(resp_eliminar.status_code, 200)
        mensajes_eliminar = [m.message for m in resp_eliminar.context['messages']]
        self.assertTrue(any("eliminado con éxito" in m for m in mensajes_eliminar))


class SolucionStockPathTest(TestCase):
    """Pruebas de la ruta de stock.json y función evaluar_disponibilidad."""

    def test_evaluar_disponibilidad_carga_stock_correctamente(self):
        from solucion import evaluar_disponibilidad
        # Comprobar que no lanza FileNotFoundError y evalúa según stock.json
        res_ok = evaluar_disponibilidad("Charizard", "Base Set", 2)
        self.assertIn("Se puede vender", res_ok)

        res_insuficiente = evaluar_disponibilidad("Charizard", "Base Set", 999)
        self.assertIn("Stock insuficiente", res_insuficiente)

        res_no_existe = evaluar_disponibilidad("CartaInexistente123", "Base Set", 1)
        self.assertIn("La carta no existe", res_no_existe)



from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


class APIRestfulTest(TestCase):
    """
    Pruebas completas de la API RESTful (Evaluación 3 · Criterios 3.1.1, 3.1.2, 3.1.3, 3.1.4).
    Verifica códigos de estado HTTP (200, 201, 204, 400, 401, 403, 404),
    autenticación por token, permisos diferenciados, serializadores y Swagger.
    """

    def setUp(self):
        self.api_client = APIClient()

        # Crear grupos de roles
        self.grp_admin, _ = Group.objects.get_or_create(name="admin")
        self.grp_normal, _ = Group.objects.get_or_create(name="normal")
        self.grp_viewer, _ = Group.objects.get_or_create(name="viewer")

        # Crear usuarios para cada rol
        self.u_admin = User.objects.create_user("api_admin", password="password123")
        self.u_admin.groups.add(self.grp_admin)
        self.token_admin, _ = Token.objects.get_or_create(user=self.u_admin)

        self.u_normal = User.objects.create_user("api_normal", password="password123")
        self.u_normal.groups.add(self.grp_normal)
        self.token_normal, _ = Token.objects.get_or_create(user=self.u_normal)

        self.u_viewer = User.objects.create_user("api_viewer", password="password123")
        self.u_viewer.groups.add(self.grp_viewer)
        self.token_viewer, _ = Token.objects.get_or_create(user=self.u_viewer)

        # Registro de prueba en base de datos
        self.registro = Registro.objects.create(
            nombre_carta="Charizard",
            expansion="Base Set",
            cantidad_solicitada=1,
            resultado="Se puede vender. Stock disponible: 5."
        )

    def test_endpoint_sin_token_responde_401_unauthorized(self):
        """Peticiones sin cabecera Authorization deben responder con HTTP 401 Unauthorized."""
        resp = self.api_client.get("/api/registros/")
        self.assertEqual(resp.status_code, 401)

        resp_post = self.api_client.post("/api/registros/", {
            "nombre_carta": "Pikachu",
            "expansion": "Crown Zenith",
            "cantidad_solicitada": 1
        }, format="json")
        self.assertEqual(resp_post.status_code, 401)

    def test_obtencion_de_token_con_credenciales_validas(self):
        """POST a /api/token/ entrega un token válido con credenciales correctas (HTTP 200)."""
        resp = self.api_client.post("/api/token/", {
            "username": "api_admin",
            "password": "password123"
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.data)
        self.assertEqual(resp.data["token"], self.token_admin.key)

    def test_obtencion_de_token_con_credenciales_invalidas(self):
        """POST a /api/token/ con credenciales incorrectas responde con HTTP 400 Bad Request."""
        resp = self.api_client.post("/api/token/", {
            "username": "api_admin",
            "password": "password_incorrecta"
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_get_registros_paginado_responde_200_ok(self):
        """GET /api/registros/ con token responde 200 OK con estructura paginada."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_viewer.key}")
        resp = self.api_client.get("/api/registros/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("count", resp.data)
        self.assertIn("results", resp.data)
        self.assertGreaterEqual(resp.data["count"], 1)

    def test_rol_viewer_solo_lectura_y_bloqueado_en_escritura(self):
        """Rol viewer puede listar (200 OK), pero POST, PUT, DELETE retornan 403 Forbidden."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_viewer.key}")

        # GET permitido
        resp_get = self.api_client.get(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(resp_get.status_code, 200)

        # POST bloqueado (403)
        resp_post = self.api_client.post("/api/registros/", {
            "nombre_carta": "Mewtwo",
            "expansion": "Base Set",
            "cantidad_solicitada": 1
        }, format="json")
        self.assertEqual(resp_post.status_code, 403)

        # PUT bloqueado (403)
        resp_put = self.api_client.put(f"/api/registros/{self.registro.pk}/", {
            "nombre_carta": "Charizard",
            "expansion": "Base Set",
            "cantidad_solicitada": 2
        }, format="json")
        self.assertEqual(resp_put.status_code, 403)

        # DELETE bloqueado (403)
        resp_del = self.api_client.delete(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(resp_del.status_code, 403)

    def test_rol_normal_puede_crear_pero_no_modificar_ni_eliminar(self):
        """Rol normal puede crear (201 Created), pero PUT y DELETE retornan 403 Forbidden."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_normal.key}")

        # POST permitido (201)
        resp_post = self.api_client.post("/api/registros/", {
            "nombre_carta": "Pikachu",
            "expansion": "Crown Zenith",
            "cantidad_solicitada": 2
        }, format="json")
        self.assertEqual(resp_post.status_code, 201)
        self.assertEqual(resp_post.data["nombre_carta"], "Pikachu")
        # El resultado lo calcula la regla del servidor
        self.assertIn("Se puede vender", resp_post.data["resultado"])

        # Intentar modificar retorna 403
        resp_patch = self.api_client.patch(f"/api/registros/{self.registro.pk}/", {
            "cantidad_solicitada": 5
        }, format="json")
        self.assertEqual(resp_patch.status_code, 403)

        # Intentar eliminar retorna 403
        resp_del = self.api_client.delete(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(resp_del.status_code, 403)

    def test_rol_admin_puede_actualizar_con_recalculo_y_eliminar_logico(self):
        """Rol admin tiene acceso total: PATCH (200 OK con recálculo) y DELETE (204 No Content con soft delete)."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_admin.key}")

        # PATCH para cambiar cantidad a 99 (supera stock -> debe recalcular resultado)
        resp_patch = self.api_client.patch(f"/api/registros/{self.registro.pk}/", {
            "cantidad_solicitada": 99
        }, format="json")
        self.assertEqual(resp_patch.status_code, 200)
        self.assertEqual(resp_patch.data["cantidad_solicitada"], 99)
        self.assertIn("Stock insuficiente", resp_patch.data["resultado"])

        # DELETE retorna 204 No Content
        resp_del = self.api_client.delete(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(resp_del.status_code, 204)

        # Verificar borrado lógico: el registro no se destruyó de la BD
        self.registro.refresh_from_db()
        self.assertTrue(self.registro.eliminado)
        self.assertIsNotNone(self.registro.fecha_eliminacion)

    def test_post_datos_invalidos_retorna_400_bad_request(self):
        """Datos inválidos (cantidad fuera de rango, campos vacíos) retornan HTTP 400 Bad Request."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_admin.key}")

        # Cantidad negativa
        resp_neg = self.api_client.post("/api/registros/", {
            "nombre_carta": "Venusaur",
            "expansion": "Base Set",
            "cantidad_solicitada": -1
        }, format="json")
        self.assertEqual(resp_neg.status_code, 400)
        self.assertIn("cantidad_solicitada", resp_neg.data)

        # Cantidad mayor a 10000
        resp_max = self.api_client.post("/api/registros/", {
            "nombre_carta": "Venusaur",
            "expansion": "Base Set",
            "cantidad_solicitada": 10001
        }, format="json")
        self.assertEqual(resp_max.status_code, 400)

        # Nombre vacío
        resp_empty = self.api_client.post("/api/registros/", {
            "nombre_carta": "   ",
            "expansion": "Base Set",
            "cantidad_solicitada": 1
        }, format="json")
        self.assertEqual(resp_empty.status_code, 400)

    def test_get_registro_no_existente_retorna_404_not_found(self):
        """Consultar un ID que no existe retorna HTTP 404 Not Found."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_viewer.key}")
        resp = self.api_client.get("/api/registros/999999/")
        self.assertEqual(resp.status_code, 404)

    def test_action_disponibles_retorna_200_ok(self):
        """GET /api/registros/disponibles/ retorna 200 OK con cartas vendibles."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_viewer.key}")
        resp = self.api_client.get("/api/registros/disponibles/")
        self.assertEqual(resp.status_code, 200)

    def test_documentacion_swagger_responde_200_ok(self):
        """Los endpoints de documentación /api/schema/ y /api/docs/ responden HTTP 200 OK."""
        resp_schema = self.api_client.get("/api/schema/")
        self.assertEqual(resp_schema.status_code, 200)

        resp_docs = self.api_client.get("/api/docs/")
        self.assertEqual(resp_docs.status_code, 200)

    def test_tcgplayer_precio_e_imagen_en_api(self):
        """Los registros serializados en /api/registros/ incluyen precio_tcgplayer, tcgplayer_url e imagen_url."""
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_viewer.key}")
        resp = self.api_client.get(f"/api/registros/{self.registro.pk}/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("precio_tcgplayer", resp.data)
        self.assertIn("tcgplayer_url", resp.data)
        self.assertIn("imagen_url", resp.data)
        self.assertTrue(len(resp.data["precio_tcgplayer"]) > 0)
        self.assertTrue(resp.data["tcgplayer_url"].startswith("http"))
=======
from django.test import TestCase

# Create your tests here.
>>>>>>> 414e181eddee75b0112ca15022d1bf61cc74b558
