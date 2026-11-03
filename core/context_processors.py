def roles_context(request):
    """
    Context processor para exponer el rol del usuario en todas las plantillas.
    Permite usar {% if es_admin %} en los templates para adaptar la interfaz visual.
    """
    if request.user.is_authenticated:
        grupos = list(request.user.groups.values_list('name', flat=True))
        es_admin = 'admin' in grupos or request.user.is_superuser
        es_normal = 'normal' in grupos
        es_viewer = 'viewer' in grupos
        rol = 'admin' if es_admin else ('normal' if es_normal else ('viewer' if es_viewer else 'sin rol'))
        return {
            'es_admin': es_admin,
            'es_normal': es_normal,
            'es_viewer': es_viewer,
            'rol_usuario': rol,
        }
    return {
        'es_admin': False,
        'es_normal': False,
        'es_viewer': False,
        'rol_usuario': '',
    }
