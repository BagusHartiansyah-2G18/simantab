from django.urls import path,include
from app.views.Vpage import dashboard,data,pengusaha,denda,wilaya
from app.views.Vapi.VAsimtax import simtax_login,simtax_get_transaksi,TransaksiPajakViewSet


from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'transaksipajak', TransaksiPajakViewSet)



urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('pengusaha', pengusaha, name='pengusaha'),
    path('data', data, name='data'),
    path('denda', denda, name='denda'),
    path('wilaya', wilaya, name='wilaya'),
    
    
    path("proxy/simtax/login/", simtax_login),
    path("proxy/simtax/data/", simtax_get_transaksi),
    path('api/', include(router.urls)),
]
