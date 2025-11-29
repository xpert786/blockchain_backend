from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q, Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from datetime import datetime, timedelta

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
from .models import InvestorProfile
from spv.models import SPV
from spv.serializers import SPVSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard overview and statistics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get complete dashboard overview with all cards data"""
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
        
        # Count active SPVs (investments)
        active_spvs = Investment.objects.filter(investor=user, status='active').count()
        
        # Get recent investments
        recent_investments = Investment.objects.filter(investor=user).order_by('-created_at')[:5]
        
        data = {
            'kyc_status': kyc_status_value,
            'kyc_verified': kyc_verified,
            'total_investments': active_spvs,
            'portfolio_value': str(portfolio.current_value),
            'total_invested': str(portfolio.total_invested),
            'unrealized_gain': str(portfolio.unrealized_gain),
            'portfolio_growth': portfolio.portfolio_growth_percentage,
            'total_notifications': total_notifications,
            'unread_notifications': unread_count,
            'action_required_notifications': action_required_count,
            'recent_investments': InvestmentSerializer(recent_investments, many=True).data,
        }
        
        return Response(data)
    
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
    
    @action(detail=False, methods=['get'])
    def discover_deals(self, request):
        """Get all available SPVs for discovery"""
        # Get all SPVs that are open for investment
        spvs = SPV.objects.filter(
            status__in=['active', 'approved', 'pending_review']
        ).order_by('-created_at')
        
        # Apply filters if provided
        sector = request.query_params.get('sector', None)
        if sector:
            spvs = spvs.filter(deal_tags__contains=[sector])
        
        stage = request.query_params.get('stage', None)
        if stage:
            spvs = spvs.filter(company_stage__name__icontains=stage)
        
        status_filter = request.query_params.get('status', None)
        if status_filter:
            spvs = spvs.filter(status=status_filter)
        
        # Paginate results
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(spvs, request)
        
        # Convert to investment-like format for frontend
        deals = []
        for spv in page:
            # Calculate days left from target_closing_date
            days_left = 22  # Default
            if spv.target_closing_date:
                delta = spv.target_closing_date - timezone.now().date()
                days_left = max(0, delta.days)
            
            # Count investors (allocated count)
            allocated_count = Investment.objects.filter(spv=spv).count()
            
            # Sum raised amount
            raised_amount = Investment.objects.filter(spv=spv, status__in=['active', 'pending']).aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0
            
            # Determine status label
            status_label = 'Raising'
            if spv.status == 'closed':
                status_label = 'Closed'
            elif spv.status == 'pending_review':
                status_label = 'Pending'
            elif days_left <= 0:
                status_label = 'Expired'
            
            deals.append({
                'id': spv.id,
                'spv_id': spv.id,
                'syndicate_name': spv.display_name,
                'company_name': spv.portfolio_company_name,
                'sector': spv.deal_tags[0] if spv.deal_tags and len(spv.deal_tags) > 0 else 'Technology',
                'stage': str(spv.company_stage) if spv.company_stage else 'Series B',
                'tags': spv.deal_tags or [],
                'allocated': allocated_count,
                'raised': float(raised_amount),
                'target': float(spv.round_size) if spv.round_size else 0,
                'allocation': float(spv.allocation) if spv.allocation else 0,
                'min_investment': float(spv.minimum_lp_investment) if spv.minimum_lp_investment else 25000,
                'days_left': days_left,
                'target_closing_date': str(spv.target_closing_date) if spv.target_closing_date else None,
                'status': status_label,
                'status_code': spv.status,
                'investment_type': 'syndicate_deal',
                'created_at': spv.created_at.strftime('%d/%m/%Y'),
                'lead_name': f"{spv.created_by.first_name} {spv.created_by.last_name}".strip() or spv.created_by.username if spv.created_by else 'Unknown',
            })
        
        return paginator.get_paginated_response(deals)
    
    @action(detail=False, methods=['get'])
    def top_syndicates(self, request):
        """Get all syndicates (SPV leads/creators)"""
        # Get all unique syndicate leads who have created SPVs
        from django.db.models import Count as DjCount, Max, Avg
        from users.models import CustomUser
        
        # Get syndicate leads with their SPV stats
        syndicate_leads = CustomUser.objects.filter(
            created_spvs__isnull=False
        ).annotate(
            total_spvs=DjCount('created_spvs'),
            total_raised=Sum('created_spvs__allocation'),
            latest_spv_date=Max('created_spvs__created_at')
        ).order_by('-total_spvs', '-latest_spv_date')
        
        # Paginate results
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(syndicate_leads, request)
        
        syndicates = []
        for lead in page:
            # Get all SPVs for this lead
            lead_spvs = SPV.objects.filter(created_by=lead)
            active_spvs = lead_spvs.filter(status__in=['active', 'approved'])
            
            # Calculate total investors across all SPVs
            total_investors = Investment.objects.filter(spv__in=lead_spvs).values('investor').distinct().count()
            total_raised = Investment.objects.filter(spv__in=lead_spvs, status='active').aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0
            
            # Get sectors from deal tags
            all_tags = []
            for spv in lead_spvs[:5]:  # Get tags from recent 5 SPVs
                if spv.deal_tags:
                    all_tags.extend(spv.deal_tags)
            unique_sectors = list(set(all_tags))[:3]  # Top 3 unique sectors
            
            syndicates.append({
                'id': lead.id,
                'syndicate_lead_id': lead.id,
                'syndicate_name': f"{lead.first_name} {lead.last_name}".strip() or lead.username,
                'lead_email': lead.email,
                'total_spvs': lead.total_spvs,
                'active_spvs': active_spvs.count(),
                'sectors': unique_sectors if unique_sectors else ['Technology'],
                'total_investors': total_investors,
                'total_raised': float(total_raised),
                'total_allocation': float(lead.total_raised) if lead.total_raised else 0,
                'min_investment': 50000,  # Default
                'track_record': '+23.4% IRR',  # Mock - can be calculated from actual performance
                'status': 'Active' if active_spvs.exists() else 'Inactive',
                'investment_type': 'top_syndicate',
                'joined_date': lead.date_joined.strftime('%d/%m/%Y') if lead.date_joined else None,
            })
        
        return paginator.get_paginated_response(syndicates)
    
    @action(detail=False, methods=['get'])
    def invites(self, request):
        """Get all SPV invites sent to the investor"""
        user = request.user
        
        # Get investor's email from InvestorProfile or user.email
        investor_email = None
        try:
            investor_profile = InvestorProfile.objects.get(user=user)
            investor_email = investor_profile.email_address
        except InvestorProfile.DoesNotExist:
            pass
        
        # Fallback to user email if profile email not available
        if not investor_email:
            investor_email = user.email
        
        if not investor_email:
            return Response({
                'success': False,
                'error': 'No email found for this investor',
                'invites': []
            })
        
        # Normalize email for case-insensitive comparison
        investor_email_lower = investor_email.lower().strip()
        
        # Get all SPVs that have lp_invite_emails set (include draft status since invites can be sent before approval)
        all_spvs = SPV.objects.filter(
            status__in=['draft', 'active', 'approved', 'pending_review']
        ).exclude(
            created_by=user  # Exclude SPVs created by the investor themselves
        ).exclude(
            lp_invite_emails__isnull=True  # Exclude SPVs with no invites
        ).exclude(
            lp_invite_emails=[]  # Exclude SPVs with empty invite list
        )
        
        # Filter SPVs where investor email is in lp_invite_emails (case-insensitive)
        invited_spvs = []
        for spv in all_spvs:
            if spv.lp_invite_emails:
                # Convert all emails in the list to lowercase for comparison
                spv_emails_lower = [email.lower().strip() for email in spv.lp_invite_emails]
                if investor_email_lower in spv_emails_lower:
                    invited_spvs.append(spv)
        
        # Paginate results
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(invited_spvs, request)
        
        invites = []
        for spv in page:
            # Calculate deadline from target_closing_date
            deadline_days = 7  # Default
            if spv.target_closing_date:
                delta = spv.target_closing_date - timezone.now().date()
                deadline_days = max(0, delta.days)
            
            # Check if investor has already invested in this SPV
            already_invested = Investment.objects.filter(investor=user, spv=spv).exists()
            
            # Count investors (allocated count)
            allocated_count = Investment.objects.filter(spv=spv).count()
            
            # Sum raised amount
            raised_amount = Investment.objects.filter(spv=spv, status__in=['active', 'pending']).aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0
            
            # Determine status
            if already_invested:
                invite_status = 'Invested'
            elif deadline_days <= 0:
                invite_status = 'Expired'
            else:
                invite_status = 'Active'
            
            invites.append({
                'id': spv.id,
                'spv_id': spv.id,
                'syndicate_name': spv.display_name,
                'company_name': spv.portfolio_company_name,
                'led_by': f"{spv.created_by.first_name} {spv.created_by.last_name}".strip() or spv.created_by.username if spv.created_by else 'Unknown',
                'lead_email': spv.created_by.email if spv.created_by else None,
                'description': spv.lp_invite_message or f"You've been invited to invest in {spv.display_name}",
                'sector': spv.deal_tags[0] if spv.deal_tags and len(spv.deal_tags) > 0 else 'Technology',
                'stage': str(spv.company_stage) if spv.company_stage else 'Series B',
                'tags': spv.deal_tags or [],
                'allocated': allocated_count,
                'raised': float(raised_amount),
                'target': float(spv.round_size) if spv.round_size else 0,
                'allocation': float(spv.allocation) if spv.allocation else 0,
                'min_investment': float(spv.minimum_lp_investment) if spv.minimum_lp_investment else 25000,
                'deadline': deadline_days,
                'target_closing_date': str(spv.target_closing_date) if spv.target_closing_date else None,
                'status': invite_status,
                'status_code': spv.status,
                'already_invested': already_invested,
                'investment_type': 'invite',
                'invited_at': spv.updated_at.strftime('%d/%m/%Y'),
                'private_note': spv.invite_private_note,
                'lead_carry_percentage': float(spv.lead_carry_percentage) if spv.lead_carry_percentage else 0,
                'investment_visibility': spv.investment_visibility,
            })
        
        return paginator.get_paginated_response(invites)
    
    @action(detail=False, methods=['post'])
    def invest_in_syndicate(self, request):
        """Invest in a syndicate/SPV"""
        spv_id = request.data.get('spv_id')
        amount = request.data.get('amount')
        
        if not spv_id or not amount:
            return Response(
                {'error': 'spv_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            spv = SPV.objects.get(id=spv_id)
        except SPV.DoesNotExist:
            return Response(
                {'error': 'SPV not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create investment
        investment = Investment.objects.create(
            investor=request.user,
            spv=spv,
            syndicate_name=spv.display_name,
            sector=getattr(spv.portfolio_company, 'sector', 'Technology') if spv.portfolio_company else 'Technology',
            stage=str(spv.company_stage) if spv.company_stage else 'Series B',
            investment_type=request.data.get('investment_type', 'syndicate_deal'),
            invested_amount=amount,
            current_value=amount,  # Initial value same as invested
            allocated=0,
            raised=spv.allocation or 0,
            target=spv.round_size or 0,
            min_investment=25000,
            status='pending',
        )
        
        # Update portfolio
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        portfolio.recalculate()
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            notification_type='investment',
            title='Investment Submitted',
            message=f'Your investment of ${amount} in {spv.display_name} has been submitted for processing.',
            status='unread'
        )
        
        return Response({
            'message': 'Investment submitted successfully',
            'investment': InvestmentSerializer(investment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def accept_invite(self, request):
        """Accept an investment invite"""
        notification_id = request.data.get('notification_id')
        amount = request.data.get('amount')
        
        if not notification_id:
            return Response(
                {'error': 'notification_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        spv = notification.related_spv
        if not spv:
            return Response(
                {'error': 'No SPV associated with this invite'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create investment
        investment = Investment.objects.create(
            investor=request.user,
            spv=spv,
            syndicate_name=spv.display_name,
            sector=getattr(spv.portfolio_company, 'sector', 'Technology') if spv.portfolio_company else 'Technology',
            stage=str(spv.company_stage) if spv.company_stage else 'Series C',
            investment_type='invite',
            invested_amount=amount,
            current_value=amount,
            allocated=0,
            raised=spv.allocation or 0,
            target=spv.round_size or 0,
            min_investment=25000,
            status='pending',
        )
        
        # Mark notification as read
        notification.mark_as_read()
        
        # Update portfolio
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
        portfolio.recalculate()
        
        return Response({
            'message': 'Invite accepted and investment created',
            'investment': InvestmentSerializer(investment).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def decline_invite(self, request):
        """Decline an investment invite"""
        notification_id = request.data.get('notification_id')
        
        if not notification_id:
            return Response(
                {'error': 'notification_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Mark notification as read and archived
        notification.status = 'archived'
        notification.save()
        
        return Response({
            'message': 'Invite declined successfully'
        })


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
        """Get portfolio snapshot with performance data matching Figma design"""
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        portfolio.recalculate()
        
        # Generate performance chart data (mock data showing growth)
        # In production, this would pull from historical portfolio values
        today = timezone.now().date()
        performance_history = []
        
        # Generate data points for the last 6 months
        for i in range(6):
            date = today - timedelta(days=30 * (5 - i))
            # Simulate growth from invested to current value
            progress = (i + 1) / 6
            value = float(portfolio.total_invested) + (float(portfolio.unrealized_gain) * progress)
            performance_history.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(value, 2)
            })
        
        snapshot_data = {
            'total_invested': str(portfolio.total_invested),
            'current_value': str(portfolio.current_value),
            'unrealized_gain': str(portfolio.unrealized_gain),
            'portfolio_growth': portfolio.portfolio_growth_percentage,
            'portfolio_growth_label': f"{portfolio.portfolio_growth_percentage}% Portfolio Growth",
            'performance_history': performance_history
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
