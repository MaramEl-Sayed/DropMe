from django.urls import path
from .views import RegisterUserView, RecyclingTransactionView, UserPointsView

urlpatterns = [
    path("register/", RegisterUserView.as_view(), name="register-user"),
    path("recycle/", RecyclingTransactionView.as_view(), name="recycle"),
    path("users/<int:user_id>/", UserPointsView.as_view(), name="user-points"),
]
