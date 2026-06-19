from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """PageNumberPagination que permite al cliente elegir el tamaño de página.

    Mantiene el PAGE_SIZE por defecto (definido en settings) pero habilita el
    parámetro ``page_size`` en la query string, acotado por ``max_page_size``.
    """

    page_size_query_param = 'page_size'
    max_page_size = 200
