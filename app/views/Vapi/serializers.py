from rest_framework import serializers
from app.models import TransaksiPajak

class TransaksiPajakSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransaksiPajak
        fields = '__all__'