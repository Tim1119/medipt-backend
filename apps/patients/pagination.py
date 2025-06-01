from rest_framework.pagination import PageNumberPagination

class DiagnosisHistoryPagination(PageNumberPagination):
    """
    Pagination for diagnosis history (can have different page size)
    """
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'message': 'Diagnosis history retrieved successfully',
            'pagination': {
                'links': {
                    'next': self.get_next_link(),
                    'previous': self.get_previous_link()
                },
                'count': self.page.paginator.count,
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'page_size': self.page_size
            },
            'data': data
        })