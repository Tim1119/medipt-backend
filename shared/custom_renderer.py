from rest_framework.renderers import JSONRenderer

class SuccessJsonRenderer(JSONRenderer):
    """
    Custom renderer to wrap successful responses in a standard format
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Only modify the response if it's not an error response
        if renderer_context and not renderer_context['response'].exception:
            wrapped_data = {
                "success": True,
                "data": data
            }
            return super().render(wrapped_data, accepted_media_type, renderer_context)
        return super().render(data, accepted_media_type, renderer_context)