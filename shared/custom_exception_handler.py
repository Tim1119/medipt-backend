from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse

class MyExceptionFormatter(ExceptionFormatter):
   

   def format_error_response(self, error_response: ErrorResponse):
       error_messages = []
       for error in error_response.errors:
           if error_response.type == "validation_error" and error.attr != "non_field_errors" and error.attr is not None:
               error_messages.append(f"{error.attr}: {error.detail}")
           else:
               error_messages.append(error.detail)
       
       return {
           "success": False,
           "type": error_response.type,
           "code": error.code,
           "errors": error_messages
       }