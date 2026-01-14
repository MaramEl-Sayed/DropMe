from rest_framework import serializers
from django.utils import timezone
from django.db import transaction as db_transaction
from .models import User, RecyclingTransaction
from .rules import calculate_points, POINT_RULES
from .constants import DUPLICATE_SCAN_WINDOW_SECONDS, PHONE_LENGTH


class UserSerializer(serializers.ModelSerializer):
    """
    Used for user registration or identification.
    """

    class Meta:
        model = User
        fields = ["id", "name", "phone", "points", "is_active"]
        read_only_fields = ["points", "is_active"]

    def validate_name(self, value):
        """Validate name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value.strip()

    def validate_phone(self, value):
        """Validate phone number format."""
        if len(value) != PHONE_LENGTH or not value.isdigit():
            raise serializers.ValidationError(f"Phone number must be exactly {PHONE_LENGTH} digits.")
        return value


class RecyclingTransactionSerializer(serializers.ModelSerializer):
    """
    Used to create a recycling transaction.
    """

    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecyclingTransaction
        fields = [
            "id",
            "user_id",
            "material_type",
            "quantity",
            "points_awarded",
            "timestamp",
        ]
        read_only_fields = ["points_awarded", "timestamp"]

    def validate(self, attrs):
        user_id = attrs.get("user_id")
        material_type = attrs.get("material_type")
        quantity = attrs.get("quantity")

        # Validate user exists and is active
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"user_id": "User does not exist or is inactive."}
            )

        # Store user in validated_data to avoid re-fetching in create()
        attrs["user"] = user

        # Validate material type
        if material_type not in POINT_RULES:
            raise serializers.ValidationError(
                {"material_type": f"Invalid material. Allowed: {list(POINT_RULES.keys())}"}
            )

        # Validate quantity
        if quantity is None or quantity <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be a positive integer."}
            )

        # Note: Duplicate check moved to create() method inside atomic transaction
        # to prevent race conditions

        return attrs

    @db_transaction.atomic
    def create(self, validated_data):
        """
        Create recycling transaction and update user points atomically.
        Ensures data consistency if either operation fails.
        Duplicate check happens inside transaction to prevent race conditions.
        """
        # Get user (already validated and stored in validate())
        user = validated_data.pop("user")
        # Remove user_id as we're using user object directly
        validated_data.pop("user_id", None)
        
        # Re-fetch with lock to ensure we have latest data and prevent race conditions
        user = User.objects.select_for_update().get(id=user.id, is_active=True)

        quantity = validated_data["quantity"]
        material_type = validated_data["material_type"]

        # Duplicate scan prevention (inside atomic transaction to prevent race conditions)
        last_tx = RecyclingTransaction.objects.filter(
            user=user, material_type=material_type
        ).order_by("-timestamp").first()

        if last_tx:
            time_diff = timezone.now() - last_tx.timestamp
            if time_diff.total_seconds() < DUPLICATE_SCAN_WINDOW_SECONDS:
                raise serializers.ValidationError(
                    {
                        "duplicate": f"Duplicate scan detected. Please wait at least {DUPLICATE_SCAN_WINDOW_SECONDS} seconds between recycling the same material."
                    }
                )

        # Calculate points
        points = calculate_points(material_type, quantity)

        # Validate points won't go negative (defensive check)
        if user.points + points < 0:
            raise serializers.ValidationError(
                {"points": "Transaction would result in negative points."}
            )

        # Create transaction
        recycling_transaction = RecyclingTransaction.objects.create(
            user=user,
            material_type=material_type,
            quantity=quantity,
            points_awarded=points,
        )

        # Update user's total points (atomic with transaction creation)
        user.points += points
        user.save()

        return recycling_transaction
