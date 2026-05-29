from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import MembroSerializer

class PerfilLogadoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MembroSerializer(request.user)
        return Response(serializer.data)
