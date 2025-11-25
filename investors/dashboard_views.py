from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q, Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal

from .dashboard_models import Portfolio, Investment, Notification, KYCStatus
from .dashboard_serializers import (
    PortfolioSerializer,
    InvestmentSerializer,
    InvestmentCreateSerializer,
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationMarkReadSerializer,
    NotificationStatsSerializer,
    DashboardOverviewSerializer,
    KYCStatusSerializer
)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard overview and statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get complete dashboard overview"""
        user = request.user
        
        # Get or create portfolio
        portfolio, created = Portfolio.objects.get_or_create(user=user)
        if not created:
            portfolio.recalculate()
        
        # Get KYC status
        try:
            kyc_status = KYCStatus.objects.get(user=user)
            kyc_status_value = kyc_status.status
            kyc_verified = kyc_status.status == 'verified'
        except KYCStatus.DoesNotExist:
            kyc_status_value = 'not_started'
            kyc_verified = False
        
        # Get notification counts
        notifications = Notification.objects.filter(user=user)
        total_notifications = notifications.count()
        unread_count = notifications.filter(status='unread').count()
        action_required_count = notifications.filter(action_required=True, status='unread').count()
        
        # Get recent investments
        recent_investments = Investment.objects.filter(investor=user).order_by('-created_at')[:5]
        
        data = {
            'kyc_status': kyc_status_value,
            'kyc_verified': kyc_verified,
            'total_investments': portfolio.total_investments_count,
            'portfolio_value': portfolio.current_value,
            'total_invested': portfolio.total_invested,
            'unrealized_gain': portfolio.unrealized_gain,
            'portfolio_growth': portfolio.portfolio_growth_percentage,
            'total_notifications': total_notifications,
            'unread_notifications': unread_count,
            'action_required_notifications': action_required_count,
            'recent_investments': recent_investments,
        }
        
        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get detailed dashboard statistics"""
        user = request.user
        
        # Investment statistics
        investments = Investment.objects.filter(investor=user)
        
        stats = {
            'total_investments': investments.count(),
            'active_investments': investments.filter(status='active').count(),
            'pending_investments': investments.filter(status='pending').count(),
            'completed_investments': investments.filter(status='completed').count(),
            
            # By type
            'investments_by_type': {
                'syndicate_deal': investments.filter(investment_type='syndicate_deal').count(),
                'top_syndicate': investments.filter(investment_type='top_syndicate').count(),
                'invite': investments.filter(investment_type='invite').count(),
            },
            
            # By sector
            'investments_by_sector': dict(
                investments.values('sector')
                .annotate(count=Count('id'))
                .values_list('sector', 'count')
            ),
            
            # Financial summary
            'total_allocated': investments.aggregate(Sum('allocated'))['allocated__sum'] or 0,
            'total_raised': investments.aggregate(Sum('raised'))['raised__sum'] or 0,
            'total_invested': investments.aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0,
        }
        
        return Response(stats)


class PortfolioViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user portfolio
    """
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return portfolio for current user"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Portfolio.objects.all()
        
        return Portfolio.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_portfolio(self, request):
        """Get current user's portfolio"""
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        
        # Recalculate portfolio values
        portfolio.recalculate()
        
        serializer = self.get_serializer(portfolio)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Manually recalculate portfolio values"""
        portfolio = self.get_object()
        portfolio.recalculate()
        
        serializer = self.get_serializer(portfolio)
        return Response({
            'message': 'Portfolio recalculated successfully',
            'portfolio': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def snapshot(self, request):
        """Get portfolio snapshot with performance data"""
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        portfolio.recalculate()
        
        # Get performance data (for chart)
        # This would typically pull from historical data
        snapshot_data = {
            'total_invested': portfolio.total_invested,
            'current_value': portfolio.current_value,
            'unrealized_gain': portfolio.unrealized_gain,
            'portfolio_growth': portfolio.portfolio_growth_percentage,
            'performance_history': [
                # Mock data - replace with actual historical data
                {'date': '2025-01-01', 'value': portfolio.total_invested},
                {'date': '2025-11-25', 'value': portfolio.current_value},
            ]
        }
        
        return Response(snapshot_data)


class InvestmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing investments
    """
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return investments for current user"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Investment.objects.all()
        
        return Investment.objects.filter(investor=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return InvestmentCreateSerializer
        return InvestmentSerializer
    
    @action(detail=False, methods=['get'])
    def my_investments(self, request):
        """Get all investments for current user"""
        investments = Investment.objects.filter(investor=request.user).order_by('-created_at')
        serializer = self.get_serializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active investments"""
        investments = Investment.objects.filter(investor=request.user, status='active')
        serializer = self.get_serializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending investments"""
        investments = Investment.objects.filter(investor=request.user, status='pending')
        serializer = self.get_serializer(investments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get investments grouped by type"""
        user = request.user
        
        data = {
            'syndicate_deals': InvestmentSerializer(
                Investment.objects.filter(investor=user, investment_type='syndicate_deal'),
                many=True
            ).data,
            'top_syndicates': InvestmentSerializer(
                Investment.objects.filter(investor=user, investment_type='top_syndicate'),
                many=True
            ).data,
            'invites': InvestmentSerializer(
                Investment.objects.filter(investor=user, investment_type='invite'),
                many=True
            ).data,
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def mark_active(self, request, pk=None):
        """Mark investment as active"""
        investment = self.get_object()
        investment.status = 'active'
        investment.invested_at = timezone.now()
        investment.save()
        
        serializer = self.get_serializer(investment)
        return Response({
            'message': 'Investment marked as active',
            'investment': serializer.data
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for current user"""
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            return Notification.objects.all()
        
        return Notification.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer"""
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'mark_read' or self.action == 'mark_all_read':
            return NotificationMarkReadSerializer
        elif self.action == 'stats':
            return NotificationStatsSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def my_notifications(self, request):
        """Get all notifications for current user"""
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        # Filter by type if provided
        notification_type = request.query_params.get('type', None)
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status', None)
        if status_filter:
            notifications = notifications.filter(status=status_filter)
        
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = Notification.objects.filter(user=request.user, status='unread').order_by('-created_at')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def action_required(self, request):
        """Get notifications that require action"""
        notifications = Notification.objects.filter(
            user=request.user,
            action_required=True,
            status='unread'
        ).order_by('-created_at')
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        
        serializer = self.get_serializer(notification)
        return Response({
            'message': 'Notification marked as read',
            'notification': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark a notification as unread"""
        notification = self.get_object()
        notification.mark_as_unread()
        
        serializer = self.get_serializer(notification)
        return Response({
            'message': 'Notification marked as unread',
            'notification': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        notifications = Notification.objects.filter(user=request.user, status='unread')
        count = notifications.count()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return Response({
            'message': f'{count} notification(s) marked as read',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics"""
        user = request.user
        notifications = Notification.objects.filter(user=user)
        
        stats = {
            'total_notifications': notifications.count(),
            'unread_count': notifications.filter(status='unread').count(),
            'action_required_count': notifications.filter(action_required=True, status='unread').count(),
            
            'by_type': {
                'investment': notifications.filter(notification_type='investment').count(),
                'document': notifications.filter(notification_type='document').count(),
                'transfer': notifications.filter(notification_type='transfer').count(),
                'system': notifications.filter(notification_type='system').count(),
            },
            
            'by_priority': {
                'low': notifications.filter(priority='low').count(),
                'normal': notifications.filter(priority='normal').count(),
                'high': notifications.filter(priority='high').count(),
                'urgent': notifications.filter(priority='urgent').count(),
            },
        }
        
        serializer = NotificationStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Clear all notifications (mark as archived)"""
        notifications = Notification.objects.filter(user=request.user)
        count = notifications.count()
        notifications.update(status='archived')
        
        return Response({
            'message': f'{count} notification(s) archived',
            'count': count
        })
