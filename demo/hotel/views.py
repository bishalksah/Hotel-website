from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
import razorpay
from .models import Room, Booking

# Initialize Razorpay Client once at top level
razorpay_client = razorpay.Client(
    auth=(
        getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_TssxY6AtkbY144'), 
        getattr(settings, 'RAZORPAY_KEY_SECRET', 's7xxj6483hPtKRW28PUbj5KS')
    )
)                             

def home(request):
    featured_rooms = Room.objects.filter(is_available=True)[:3]
    return render(request, 'index.html', {'rooms': featured_rooms})

def room_list(request):
    rooms = Room.objects.filter(is_available=True)
    return render(request, 'room_list.html', {'rooms': rooms})


def about(request):
    return render(request, 'about.html')

def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        name = request.POST.get('guest_name')
        email = request.POST.get('email')
        phone = request.POST.get('guest_phone')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        # 1. Create temporary/unpaid booking in DB
        booking = Booking.objects.create(
            guest_name=name,
            guest_email=email,
            guest_phone=phone,
            room=room,
            check_in=check_in,
            check_out=check_out,
            user=request.user if request.user.is_authenticated else None
        )

        # 2. Convert total_price to Paise (1 INR = 100 Paise)
        amount_in_paise = int(booking.total_price * 100)

        # 3. Create Razorpay Order
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1"
        }
        razorpay_order = razorpay_client.order.create(data=order_data)

        # 4. Save razorpay_order_id in booking model
        booking.razorpay_order_id = razorpay_order['id']
        booking.save()

        # 5. Render payment modal page with order details
        context = {
            'room': room,
            'booking': booking,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_merchant_key': getattr(settings, 'RAZORPAY_KEY_ID', ''),
            'razorpay_amount': amount_in_paise,
            'currency': 'INR',
        }
        return render(request, 'payment.html', context)

    return render(request, 'book_room.html', {'room': room , 'razorpay_key_id': settings.RAZORPAY_KEY_ID})


@csrf_exempt
def payment_verify(request, booking_id):
    """
    Handles payment callback from Razorpay JS SDK and verifies payment signature.
    """
    if request.method == "POST":
        booking = get_object_or_404(Booking, id=booking_id)
        
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # Verify signature against Razorpay secret key
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            # Payment Successful: Update database record
            booking.razorpay_payment_id = payment_id
            booking.razorpay_signature = signature
            booking.is_paid = True
            booking.save()

            messages.success(request, f"Payment successful! Booking confirmed for Room {booking.room.room_number}.")
            return render(request, 'hotel/success.html', {'booking': booking})

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed. Invalid signature.")
            return HttpResponseBadRequest("Payment Verification Failed")

    return HttpResponseBadRequest("Invalid Request")