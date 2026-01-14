from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, RecyclingTransaction
from .serializers import UserSerializer, RecyclingTransactionSerializer


def error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST, field: str = None) -> Response:
    """
    Standardized error response format.
    
    Args:
        message: Error message
        status_code: HTTP status code
        field: Optional field name for field-specific errors
        
    Returns:
        Response with standardized error format
    """
    error_data = {"error": message}
    if field:
        error_data["field"] = field
    return Response(error_data, status=status_code)


class RegisterUserView(APIView):
    """
    Register a new user.
    Allows multiple users with the same phone number.
    Creates a new user regardless of whether phone exists.
    """

    def post(self, request):
        phone = request.data.get("phone")
        name = request.data.get("name")

        if not phone:
            return error_response("Phone number is required.", status.HTTP_400_BAD_REQUEST, "phone")

        if not name or not name.strip():
            return error_response("Name is required.", status.HTTP_400_BAD_REQUEST, "name")

        name = name.strip()

        # Create new active user (phone can be duplicate)
        serializer = UserSerializer(data={"name": name, "phone": phone})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecyclingTransactionView(APIView):
    """
    Create a recycling transaction.
    """

    def post(self, request):
        serializer = RecyclingTransactionSerializer(data=request.data)

        if serializer.is_valid():
            tx = serializer.save()
            return Response(
                {
                    "message": "Recycling transaction recorded.",
                    "transaction": RecyclingTransactionSerializer(tx).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPointsView(APIView):
    """
    Get a user's profile + points.
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return error_response("User not found or inactive.", status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
