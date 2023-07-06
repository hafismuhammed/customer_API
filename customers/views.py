from datetime import datetime, timedelta, timezone
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from customers.serializers import LoginSerializer, ProductSerializer, UserSerializer
from customers.models import Product


class RegisterAPIView(APIView):
    
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
        "message": "customer register successfully",
        "user": UserSerializer(user).data,
        })   


class LoginAPIView(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=(serializer.validated_data["username"]).lower(),
                            password=serializer.validated_data["password"])
        response = {"message": "Invalid credentials"}
        if user:
            if user.is_active:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                response["message"] = "Logged in successfully"
                response["token"] = token.key
                response["name"] = user.get_full_name()
                if user.is_superuser:
                    user_type = "super_admin"
                else:
                    user_type = "customer"
                response["user_type"] = user_type
                response["user_id"] = user.id
                return Response(response, status=200)
            else:
                response = {"message": "Your account has been deactivated. Please contact your system administrator"}
        return Response(response, status=400)


class UserManagementAPIView(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_superuser=False)
    
    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q', None)
        if q is not None:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q))
        return queryset

    def update(self, request, pk, *args, **kwargs):
        user_profile = User.objects.get(id=pk)
        partial = kwargs.pop('partial', True)
        serializer = self.get_serializer(user_profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=200)
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        self.perform_destroy(user)
        return Response({'message': 'user deleted'}, status=200)


class ProductAPIView(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer
    queryset = Product.objects.all().order_by('-created_at')
    
    def create(self, request):
        request.data['user'] = request.user.id 
        request.data['product_status'] = True
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        response = {"message": "Successfully added products", "data": serializer.data}
        return Response(response, status=200)
    
    def update(self, request, pk, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            product = Product.objects.get(id=pk)
        except Product.DoesNotExist:
            return Response({"message": "Product doesn't exist"}, status=400)
        if product.user != request.user:
            return Response({'message': 'you have no permission to update this product'}, status=400)
        request.data['private_status'] = request.data.get('private') or False
        serializer = ProductSerializer(product, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)
    
    def list(self, request, *args, **kwargs):
        queryset = self.queryset
        for product in queryset:
            date_diff = datetime.now(timezone.utc) - timedelta(days=60)
            if product.created_at < date_diff:
                product.product_status = False
                product.save()
        q = self.request.query_params.get('q', None)
        if q is not None:
            queryset = queryset.filter(product_name_icontains=q)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        product = self.get_object()
        if product.user != request.user:
            return Response({'message': 'you have no permission to delete this product'}, status=400)
        self.perform_destroy(product)
        return Response({'messege': 'product deleted'}, status=200)
    
    