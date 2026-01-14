from django.db import models
from django.utils import timezone


class User(models.Model):
    name = models.CharField(max_length=80)
    phone = models.CharField(max_length=11)  # Removed unique=True to allow duplicate phone numbers
    points = models.IntegerField(default=0)
    # The flag to handle soft deletes
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        status = "Active" if self.is_active else "Deleted"
        return f"{self.name} ({self.phone}) - {status}"


class RecyclingTransaction(models.Model):
    MATERIAL_CHOICES = [
        ("plastic", "Plastic"),
        ("can", "Can"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions", db_index=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_CHOICES, db_index=True)
    quantity = models.PositiveIntegerField()
    points_awarded = models.PositiveIntegerField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "material_type", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.material_type} - {self.points_awarded} points"
