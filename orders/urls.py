from rest_framework_nested import routers
from .views import BrandViewSet, OrderViewSet, ConfirmationViewSet

router = routers.SimpleRouter()
router.register('brands', BrandViewSet, basename="brand")
router.register('orders', OrderViewSet, basename="order")
router.register('confirmations', ConfirmationViewSet, basename="confirmation")

# Nested router for orders under brands
brands_router = routers.NestedDefaultRouter(router, 'brands', lookup='brand')
brands_router.register('orders', OrderViewSet, basename='brand-orders')

urlpatterns = router.urls + brands_router.urls 
