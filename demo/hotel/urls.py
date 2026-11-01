from django.urls import path
from .import views

urlpatterns =[
    path("", views.home, name = "home") ,
    path('about/', views.about, name='about'),
    path('rooms/', views.room_list, name='room_list'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('payment-verify/<int:booking_id>/', views.payment_verify, name='payment_verify'),
]
    
