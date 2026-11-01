from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

ROOM_TYPES = (
    ('DELUXE', 'Deluxe Room'),
    ('SUPERIOR', 'Superior Room'),
    ('SUITE', 'Executive Suite'),
)

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='DELUXE')
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    capacity = models.IntegerField(default=2)
    description = models.TextField()
    image = models.ImageField(upload_to='rooms/', blank =True, null = True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.get_room_type_display()} - Room {self.room_number}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=15)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Razorpay Specific Fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)  # NEW: For Razorpay verification
    is_paid = models.BooleanField(default=False)
    
    
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_nights(self):
        """Calculates total nights stayed."""
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    def clean(self):
        """Ensures check-out is after check-in."""
        if self.check_in and self.check_out:
            if self.check_out <= self.check_in:
                raise ValidationError("Check-out date must be after check-in date.")

    def save(self, *args, **kwargs):
        """Auto-calculate total price before saving."""
        self.full_clean()
        if self.room and self.check_in and self.check_out:
            self.total_price = self.room.price_per_night * self.total_nights
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking by {self.guest_name} for {self.room}"