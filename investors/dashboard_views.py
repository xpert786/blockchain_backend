from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q, Sum
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from decimal import Decimal
from datetime import datetime, timedelta

from .dashboard_models import Portfolio, Investment, Notification, KYCStatus, Wishlist, PortfolioPerformance, TaxDocument, TaxSummary, InvestorDocument
from .models import InvestorProfile
from .dashboard_serializers import (
    PortfolioSerializer,
    InvestmentSerializer,
    InvestmentCreateSerializer,
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationMarkReadSerializer,
    NotificationStatsSerializer,
    DashboardOverviewSerializer,
    KYCStatusSerializer,
    PortfolioPerformanceSerializer,
    PortfolioOverviewSerializer,
    InvestmentByRoundSerializer,
    InvestmentBySectorSerializer,
    InvestorInvestmentDetailSerializer,
    TaxDocumentSerializer,
    TaxSummarySerializer,
    TaxOverviewSerializer,
    InvestorDocumentSerializer,
    InvestorDocumentUploadSerializer,
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
        """Get complete dashboard overview with all cards data for investor"""
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
        active_investments = Investment.objects.filter(investor=user, status='active')
        active_spvs_count = active_investments.count()
        
        # Calculate portfolio growth label
        portfolio_growth_value = portfolio.portfolio_growth_percentage
        portfolio_growth_label = f"+{portfolio_growth_value}% from invested capital" if portfolio_growth_value >= 0 else f"{portfolio_growth_value}% from invested capital"
        
        # Get recent investments
        recent_investments = Investment.objects.filter(investor=user).order_by('-created_at')[:5]
        
        # Structure data to match UI cards
        data = {
            'success': True,
            'kyc_card': {
                'title': 'KYC Status',
                'status': kyc_status_value,
                'status_label': kyc_status_value.replace('_', ' ').title(),
                'verified': kyc_verified,
            },
            'investments_card': {
                'title': 'Total Investments',
                'count': active_spvs_count,
                'label': 'Active SPVs',
            },
            'portfolio_card': {
                'title': 'Portfolio Value',
                'value': float(portfolio.current_value),
                'formatted_value': f"${portfolio.current_value:,.0f}",
                'growth_percentage': portfolio_growth_value,
                'growth_label': portfolio_growth_label,
                'total_invested': float(portfolio.total_invested),
                'unrealized_gain': float(portfolio.unrealized_gain),
            },
            'notification_card': {
                'title': 'Notification',
                'count': unread_count,
                'label': 'Unread Updates',
                'total_notifications': total_notifications,
                'action_required': action_required_count,
            },
            # Additional data
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
        """Get all SPV invites sent by syndicates"""
        # Get all SPVs that have sent invites (lp_invite_emails is not empty)
        invited_spvs = SPV.objects.filter(
            status__in=['active', 'approved', 'pending_review']
        ).exclude(
            lp_invite_emails__isnull=True  # Exclude SPVs with no invites
        ).exclude(
            lp_invite_emails=[]  # Exclude SPVs with empty invite list
        ).order_by('-created_at')
        
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
            
            # Count investors (allocated count)
            allocated_count = Investment.objects.filter(spv=spv).count()
            
            # Sum raised amount
            raised_amount = Investment.objects.filter(spv=spv, status__in=['active', 'pending']).aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0
            
            # Determine status based on deadline
            if deadline_days <= 0:
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
                'description': spv.lp_invite_message or f"Invitation to invest in {spv.display_name}",
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
                'investment_type': 'invite',
                'invited_at': spv.updated_at.strftime('%d/%m/%Y'),
                'invited_emails': spv.lp_invite_emails or [],  # List of all invited emails
                'total_invites': len(spv.lp_invite_emails) if spv.lp_invite_emails else 0,
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
    
    @action(detail=False, methods=['post'])
    def toggle_wishlist(self, request):
        """Add or remove SPV from wishlist based on is_in_wishlist flag"""
        spv_id = request.data.get('spv_id')
        is_in_wishlist = request.data.get('is_in_wishlist')
        
        if not spv_id:
            return Response(
                {'error': 'spv_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if is_in_wishlist is None:
            return Response(
                {'error': 'is_in_wishlist is required (true or false)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            spv = SPV.objects.get(id=spv_id)
        except SPV.DoesNotExist:
            return Response(
                {'error': 'SPV not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Convert to boolean if string
        if isinstance(is_in_wishlist, str):
            is_in_wishlist = is_in_wishlist.lower() in ('true', '1', 'yes')
        is_in_wishlist = bool(is_in_wishlist)
        
        # Check if already in wishlist
        wishlist_item = Wishlist.objects.filter(
            investor=request.user,
            spv=spv
        ).first()
        
        if is_in_wishlist:
            # Add to wishlist
            if wishlist_item:
                # Already in wishlist
                return Response({
                    'success': True,
                    'message': f'{spv.display_name} is already in wishlist',
                    'is_in_wishlist': True,
                    'spv_id': spv.id,
                    'spv_name': spv.display_name
                })
            else:
                # Create new wishlist entry
                Wishlist.objects.create(
                    investor=request.user,
                    spv=spv
                )
                return Response({
                    'success': True,
                    'message': f'{spv.display_name} added to wishlist',
                    'is_in_wishlist': True,
                    'spv_id': spv.id,
                    'spv_name': spv.display_name
                }, status=status.HTTP_201_CREATED)
        else:
            # Remove from wishlist
            if wishlist_item:
                wishlist_item.delete()
                return Response({
                    'success': True,
                    'message': f'{spv.display_name} removed from wishlist',
                    'is_in_wishlist': False,
                    'spv_id': spv.id,
                    'spv_name': spv.display_name
                })
            else:
                # Not in wishlist
                return Response({
                    'success': True,
                    'message': f'{spv.display_name} is not in wishlist',
                    'is_in_wishlist': False,
                    'spv_id': spv.id,
                    'spv_name': spv.display_name
                })
    
    @action(detail=False, methods=['get'])
    def wishlist(self, request):
        """Get all SPVs in investor's wishlist"""
        user = request.user
        
        # Get all wishlist items for this investor
        wishlist_items = Wishlist.objects.filter(investor=user).select_related('spv').order_by('-created_at')
        
        # Paginate results
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(wishlist_items, request)
        
        wishlist_spvs = []
        for item in page:
            spv = item.spv
            
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
            
            wishlist_spvs.append({
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
                'added_to_wishlist_at': item.created_at.strftime('%d/%m/%Y'),
            })
        
        return paginator.get_paginated_response(wishlist_spvs)
    
    @action(detail=False, methods=['get'])
    def check_wishlist(self, request):
        """Check if specific SPV is in wishlist"""
        spv_id = request.query_params.get('spv_id')
        
        if not spv_id:
            return Response(
                {'error': 'spv_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            spv = SPV.objects.get(id=spv_id)
        except SPV.DoesNotExist:
            return Response(
                {'error': 'SPV not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_in_wishlist = Wishlist.objects.filter(
            investor=request.user,
            spv=spv
        ).exists()
        
        return Response({
            'success': True,
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'is_in_wishlist': is_in_wishlist
        })
    
    @action(detail=False, methods=['delete'])
    def delete_wishlist(self, request):
        """Delete SPV from wishlist"""
        spv_id = request.data.get('spv_id') or request.query_params.get('spv_id')
        
        if not spv_id:
            return Response(
                {'error': 'spv_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            spv = SPV.objects.get(id=spv_id)
        except SPV.DoesNotExist:
            return Response(
                {'error': 'SPV not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find and delete wishlist item
        try:
            wishlist_item = Wishlist.objects.get(
                investor=request.user,
                spv=spv
            )
            wishlist_item.delete()
            
            return Response({
                'success': True,
                'message': f'{spv.display_name} removed from wishlist',
                'spv_id': spv.id,
                'spv_name': spv.display_name
            }, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': 'SPV is not in your wishlist',
                    'spv_id': spv.id,
                    'spv_name': spv.display_name
                },
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get', 'put', 'patch'], url_path='settings/identity')
    def identity_settings(self, request):
        """Get or update investor identity and jurisdiction settings"""
        user = request.user
        
        # Get or create investor profile
        try:
            investor_profile = InvestorProfile.objects.get(user=user)
        except InvestorProfile.DoesNotExist:
            return Response({
                'error': 'Investor profile not found. Please complete onboarding first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            # Format date of birth
            dob_formatted = None
            if investor_profile.date_of_birth:
                dob_formatted = investor_profile.date_of_birth.strftime('%d-%m-%Y')
            
            # Format full address
            full_address = None
            if investor_profile.street_address:
                address_parts = [
                    investor_profile.street_address,
                    investor_profile.city,
                    investor_profile.state_province,
                    investor_profile.zip_postal_code
                ]
                full_address = ', '.join([part for part in address_parts if part])
            
            # Determine jurisdiction status
            jurisdiction_status = 'approved'
            
            response_data = {
                'success': True,
                'identity': {
                    'full_legal_name': investor_profile.full_legal_name or investor_profile.full_name or '',
                    'country_of_residence': investor_profile.country_of_residence or '',
                    'tax_domicile': investor_profile.country_of_residence or '',
                    'national_id_passport': '',
                    'date_of_birth': dob_formatted or '',
                    'date_of_birth_raw': str(investor_profile.date_of_birth) if investor_profile.date_of_birth else None,
                    'full_address': full_address or '',
                    'street_address': investor_profile.street_address or '',
                    'city': investor_profile.city or '',
                    'state_province': investor_profile.state_province or '',
                    'zip_postal_code': investor_profile.zip_postal_code or '',
                    'country': investor_profile.country or investor_profile.country_of_residence or '',
                },
                'jurisdiction': {
                    'status': jurisdiction_status,
                    'status_label': 'Approved',
                    'message': 'Auto-tagged based on residence',
                },
                'government_id_uploaded': bool(investor_profile.government_id),
                'government_id_url': investor_profile.government_id.url if investor_profile.government_id else None,
            }
            
            return Response(response_data)
        
        elif request.method in ['PUT', 'PATCH']:
            # Update identity information
            data = request.data
            
            # Update fields if provided
            if 'full_legal_name' in data:
                investor_profile.full_legal_name = data['full_legal_name']
                if not investor_profile.full_name:
                    investor_profile.full_name = data['full_legal_name']
            
            if 'country_of_residence' in data:
                investor_profile.country_of_residence = data['country_of_residence']
            
            if 'date_of_birth' in data:
                try:
                    dob_str = data['date_of_birth']
                    if isinstance(dob_str, str):
                        from datetime import datetime
                        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                            try:
                                investor_profile.date_of_birth = datetime.strptime(dob_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        else:
                            return Response({
                                'error': 'Invalid date format. Use YYYY-MM-DD, DD-MM-YYYY, or MM/DD/YYYY'
                            }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        investor_profile.date_of_birth = dob_str
                except Exception as e:
                    return Response({
                        'error': f'Invalid date of birth: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update address fields
            if 'street_address' in data:
                investor_profile.street_address = data['street_address']
            if 'city' in data:
                investor_profile.city = data['city']
            if 'state_province' in data:
                investor_profile.state_province = data['state_province']
            if 'zip_postal_code' in data:
                investor_profile.zip_postal_code = data['zip_postal_code']
            if 'country' in data:
                investor_profile.country = data['country']
            
            if 'tax_domicile' in data:
                if not investor_profile.country_of_residence:
                    investor_profile.country_of_residence = data['tax_domicile']
            
            national_id_provided = 'national_id_passport' in data and data['national_id_passport']
            
            investor_profile.save()
            
            # Format response
            dob_formatted = None
            if investor_profile.date_of_birth:
                dob_formatted = investor_profile.date_of_birth.strftime('%d-%m-%Y')
            
            full_address = None
            if investor_profile.street_address:
                address_parts = [
                    investor_profile.street_address,
                    investor_profile.city,
                    investor_profile.state_province,
                    investor_profile.zip_postal_code
                ]
                full_address = ', '.join([part for part in address_parts if part])
            
            response_data = {
                'success': True,
                'message': 'Identity information updated successfully',
                'identity': {
                    'full_legal_name': investor_profile.full_legal_name or investor_profile.full_name or '',
                    'country_of_residence': investor_profile.country_of_residence or '',
                    'tax_domicile': investor_profile.country_of_residence or '',
                    'national_id_passport': 'Provided' if national_id_provided else '',
                    'date_of_birth': dob_formatted or '',
                    'date_of_birth_raw': str(investor_profile.date_of_birth) if investor_profile.date_of_birth else None,
                    'full_address': full_address or '',
                    'street_address': investor_profile.street_address or '',
                    'city': investor_profile.city or '',
                    'state_province': investor_profile.state_province or '',
                    'zip_postal_code': investor_profile.zip_postal_code or '',
                    'country': investor_profile.country or investor_profile.country_of_residence or '',
                },
                'jurisdiction': {
                    'status': 'approved',
                    'status_label': 'Approved',
                    'message': 'Auto-tagged based on residence',
                },
            }
            
            return Response(response_data, status=status.HTTP_200_OK)


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
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get portfolio overview for dashboard cards"""
        user = request.user
        portfolio, created = Portfolio.objects.get_or_create(user=user)
        portfolio.recalculate()
        
        # Calculate totals
        investments = Investment.objects.filter(investor=user)
        active_count = investments.filter(status='active').count()
        pending_count = investments.filter(status='pending').count()
        total_count = investments.count()
        
        # Calculate gains
        total_gains = portfolio.current_value - portfolio.total_invested
        
        data = {
            'success': True,
            'total_portfolio_value': float(portfolio.current_value),
            'total_portfolio_value_formatted': f"${portfolio.current_value:,.0f}",
            'growth_percentage': portfolio.portfolio_growth_percentage,
            'total_invested': float(portfolio.total_invested),
            'total_invested_formatted': f"${portfolio.total_invested:,.0f}",
            'investments_count': total_count,
            'total_gains': float(total_gains),
            'total_gains_formatted': f"${total_gains:,.0f}",
            'unrealized_gains': float(portfolio.unrealized_gain),
            'active_investments': active_count,
            'pending_investments': pending_count,
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get portfolio performance time-series data for chart (last 90 days)"""
        user = request.user
        portfolio, created = Portfolio.objects.get_or_create(user=user)
        
        # Get days parameter (default 90)
        days = int(request.query_params.get('days', 90))
        
        # Get performance history
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        performance_data = PortfolioPerformance.objects.filter(
            portfolio=portfolio,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # If no historical data, generate mock data based on current values
        if not performance_data.exists():
            performance_list = []
            # Generate data points
            for i in range(0, days, 7):  # Weekly data points
                date = start_date + timedelta(days=i)
                progress = (i + 1) / days
                invested = float(portfolio.total_invested) * progress
                value = invested * (1 + (float(portfolio.portfolio_growth_percentage) / 100) * progress)
                performance_list.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'total_invested': round(invested, 2),
                    'current_value': round(value, 2),
                })
            # Add current point
            performance_list.append({
                'date': end_date.strftime('%Y-%m-%d'),
                'total_invested': float(portfolio.total_invested),
                'current_value': float(portfolio.current_value),
            })
        else:
            performance_list = PortfolioPerformanceSerializer(performance_data, many=True).data
        
        return Response({
            'success': True,
            'period_days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data': performance_list,
        })
    
    @action(detail=False, methods=['get'], url_path='by-round')
    def by_round(self, request):
        """Get investments aggregated by round/stage for pie chart"""
        user = request.user
        
        # Color mapping for stages
        stage_colors = {
            'Seed': '#4ECDC4',
            'Pre-Seed': '#45B7AA',
            'Series A': '#FFD93D',
            'Series B': '#9B59B6',
            'Series C': '#3498DB',
            'Series D': '#E74C3C',
            'Series E': '#2ECC71',
            'Growth': '#F39C12',
            'Late Stage': '#1ABC9C',
        }
        default_color = '#95A5A6'
        
        # Aggregate by stage
        investments = Investment.objects.filter(investor=user, status__in=['active', 'pending'])
        stage_data = investments.values('stage').annotate(
            amount=Sum('invested_amount'),
            count=Count('id')
        ).order_by('-amount')
        
        result = []
        total = Decimal('0.00')
        for item in stage_data:
            stage = item['stage'] or 'Unknown'
            amount = item['amount'] or Decimal('0.00')
            total += amount
            result.append({
                'round': stage,
                'stage': stage,
                'amount': float(amount),
                'count': item['count'],
                'color': stage_colors.get(stage, default_color),
            })
        
        return Response({
            'success': True,
            'data': result,
            'total': float(total),
        })
    
    @action(detail=False, methods=['get'], url_path='by-sector')
    def by_sector(self, request):
        """Get investments aggregated by sector for pie chart"""
        user = request.user
        
        # Color mapping for sectors
        sector_colors = {
            'Technology': '#3498DB',
            'Healthcare': '#E74C3C',
            'Finance': '#2ECC71',
            'Energy': '#F39C12',
            'Consumer': '#9B59B6',
            'Real Estate': '#1ABC9C',
            'Education': '#FF6B6B',
            'Fintech': '#4ECDC4',
            'AI/ML': '#45B7AA',
            'SaaS': '#FFD93D',
        }
        default_color = '#95A5A6'
        
        # Aggregate by sector
        investments = Investment.objects.filter(investor=user, status__in=['active', 'pending'])
        sector_data = investments.values('sector').annotate(
            amount=Sum('invested_amount'),
            count=Count('id')
        ).order_by('-amount')
        
        # Calculate total for percentage
        total = investments.aggregate(total=Sum('invested_amount'))['total'] or Decimal('0.00')
        
        result = []
        for item in sector_data:
            sector = item['sector'] or 'Other'
            amount = item['amount'] or Decimal('0.00')
            percentage = (amount / total * 100) if total > 0 else Decimal('0.00')
            result.append({
                'sector': sector,
                'amount': float(amount),
                'count': item['count'],
                'percentage': round(float(percentage), 2),
                'color': sector_colors.get(sector, default_color),
            })
        
        return Response({
            'success': True,
            'data': result,
            'total': float(total),
        })
    
    @action(detail=False, methods=['get'])
    def investments(self, request):
        """Get investor's investments list with SPV details"""
        user = request.user
        
        # Get query params for filtering
        status_filter = request.query_params.get('status', None)
        sector = request.query_params.get('sector', None)
        stage = request.query_params.get('stage', None)
        
        investments = Investment.objects.filter(investor=user).select_related('spv').order_by('-updated_at')
        
        # Apply filters
        if status_filter:
            investments = investments.filter(status=status_filter)
        if sector:
            investments = investments.filter(sector__icontains=sector)
        if stage:
            investments = investments.filter(stage__icontains=stage)
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(investments, request)
        
        serializer = InvestorInvestmentDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='investment-detail')
    def investment_detail(self, request, pk=None):
        """Get single investment detail with SPV info"""
        user = request.user
        
        try:
            investment = Investment.objects.select_related('spv').get(id=pk, investor=user)
        except Investment.DoesNotExist:
            return Response(
                {'error': 'Investment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InvestorInvestmentDetailSerializer(investment)
        return Response({
            'success': True,
            'data': serializer.data,
        })


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


class TaxCenterViewSet(viewsets.ViewSet):
    """
    ViewSet for Tax Center - Tax Documents and Tax Summary
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get Tax Center overview cards data"""
        user = request.user
        
        # Get tax year from query params (default current year)
        current_year = timezone.now().year
        tax_year = int(request.query_params.get('year', current_year - 1))  # Default to last year
        
        # Get or create tax summary for the year
        tax_summary, created = TaxSummary.objects.get_or_create(
            investor=user,
            tax_year=tax_year,
            defaults={
                'total_income': Decimal('0.00'),
                'total_deductions': Decimal('0.00'),
                'net_taxable_income': Decimal('0.00'),
                'estimated_tax': Decimal('0.00'),
            }
        )
        
        # If no data, calculate from investments
        if created or tax_summary.total_income == 0:
            # Calculate from investments for the tax year
            year_investments = Investment.objects.filter(
                investor=user,
                status='active',
                invested_at__year=tax_year
            )
            
            # Sum up gains as income
            total_gains = sum(
                inv.gain_loss for inv in year_investments if inv.gain_loss > 0
            )
            
            # Estimate deductions (e.g., 18% of gains for expenses)
            estimated_deductions = float(total_gains) * 0.18
            
            tax_summary.total_income = Decimal(str(total_gains))
            tax_summary.total_deductions = Decimal(str(estimated_deductions))
            tax_summary.calculate()
        
        data = {
            'success': True,
            'tax_year': tax_year,
            'total_income': float(tax_summary.total_income),
            'total_income_formatted': f"${tax_summary.total_income:,.0f}",
            'total_income_label': 'From Investments',
            'total_deductions': float(tax_summary.total_deductions),
            'total_deductions_formatted': f"${tax_summary.total_deductions:,.0f}",
            'total_deductions_label': 'Investment Expenses',
            'net_taxable_income': float(tax_summary.net_taxable_income),
            'net_taxable_income_formatted': f"${tax_summary.net_taxable_income:,.0f}",
            'net_taxable_income_label': 'After Deductions',
            'estimated_tax': float(tax_summary.estimated_tax),
            'estimated_tax_formatted': f"${tax_summary.estimated_tax:,.0f}",
            'estimated_tax_label': 'Approximate Liability',
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def documents(self, request):
        """Get tax documents list"""
        user = request.user
        
        # Get filters from query params
        tax_year = request.query_params.get('year', None)
        doc_type = request.query_params.get('type', None)
        doc_status = request.query_params.get('status', None)
        
        documents = TaxDocument.objects.filter(investor=user)
        
        # Apply filters
        if tax_year:
            documents = documents.filter(tax_year=int(tax_year))
        if doc_type:
            documents = documents.filter(document_type=doc_type)
        if doc_status:
            documents = documents.filter(status=doc_status)
        
        # Order by tax year and issue date
        documents = documents.order_by('-tax_year', '-issue_date')
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(documents, request)
        
        serializer = TaxDocumentSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a specific tax document"""
        user = request.user
        
        try:
            document = TaxDocument.objects.get(id=pk, investor=user)
        except TaxDocument.DoesNotExist:
            return Response(
                {'error': 'Tax document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not document.file:
            return Response(
                {'error': 'No file attached to this document'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as downloaded
        document.status = 'downloaded'
        document.downloaded_at = timezone.now()
        document.save()
        
        from django.http import FileResponse
        response = FileResponse(document.file.open(), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{document.document_name}.pdf"'
        return response
    
    @action(detail=False, methods=['get'], url_path='download-all')
    def download_all(self, request):
        """Download all tax documents as ZIP"""
        user = request.user
        tax_year = request.query_params.get('year', None)
        
        documents = TaxDocument.objects.filter(investor=user, status='available')
        if tax_year:
            documents = documents.filter(tax_year=int(tax_year))
        
        if not documents.exists():
            return Response(
                {'error': 'No documents available for download'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create ZIP file in memory
        import zipfile
        from io import BytesIO
        from django.http import HttpResponse
        
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in documents:
                if doc.file:
                    filename = f"{doc.get_document_type_display()}_{doc.document_name}_{doc.tax_year}.pdf"
                    zip_file.writestr(filename, doc.file.read())
                    
                    # Mark as downloaded
                    doc.status = 'downloaded'
                    doc.downloaded_at = timezone.now()
                    doc.save()
        
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        year_str = f"_{tax_year}" if tax_year else ""
        response['Content-Disposition'] = f'attachment; filename="tax_documents{year_str}.zip"'
        return response
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get tax summary for a specific year"""
        user = request.user
        tax_year = int(request.query_params.get('year', timezone.now().year - 1))
        
        try:
            tax_summary = TaxSummary.objects.get(investor=user, tax_year=tax_year)
        except TaxSummary.DoesNotExist:
            return Response(
                {'error': f'No tax summary found for year {tax_year}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TaxSummarySerializer(tax_summary)
        return Response({
            'success': True,
            'data': serializer.data,
        })
    
    @action(detail=False, methods=['get'], url_path='summary-breakdown')
    def summary_breakdown(self, request):
        """Get detailed tax summary breakdown for Tax Summary tab"""
        user = request.user
        tax_year = int(request.query_params.get('year', timezone.now().year - 1))
        
        # Get or create tax summary
        tax_summary, created = TaxSummary.objects.get_or_create(
            investor=user,
            tax_year=tax_year,
            defaults={
                'dividend_income': Decimal('0.00'),
                'capital_gains': Decimal('0.00'),
                'interest_income': Decimal('0.00'),
                'management_fees': Decimal('0.00'),
                'professional_services': Decimal('0.00'),
                'other_expenses': Decimal('0.00'),
            }
        )
        
        data = {
            'success': True,
            'tax_year': tax_year,
            'income_breakdown': {
                'dividend_income': float(tax_summary.dividend_income),
                'dividend_income_formatted': f"${tax_summary.dividend_income:,.0f}",
                'capital_gains': float(tax_summary.capital_gains),
                'capital_gains_formatted': f"${tax_summary.capital_gains:,.0f}",
                'interest_income': float(tax_summary.interest_income),
                'interest_income_formatted': f"${tax_summary.interest_income:,.0f}",
                'total_income': float(tax_summary.total_income),
                'total_income_formatted': f"${tax_summary.total_income:,.0f}",
            },
            'deductions_breakdown': {
                'management_fees': float(tax_summary.management_fees),
                'management_fees_formatted': f"${tax_summary.management_fees:,.0f}",
                'professional_services': float(tax_summary.professional_services),
                'professional_services_formatted': f"${tax_summary.professional_services:,.0f}",
                'other_expenses': float(tax_summary.other_expenses),
                'other_expenses_formatted': f"${tax_summary.other_expenses:,.0f}",
                'total_deductions': float(tax_summary.total_deductions),
                'total_deductions_formatted': f"${tax_summary.total_deductions:,.0f}",
            },
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def years(self, request):
        """Get available tax years for the investor"""
        user = request.user
        
        # Get unique years from tax documents
        doc_years = TaxDocument.objects.filter(investor=user).values_list('tax_year', flat=True).distinct()
        summary_years = TaxSummary.objects.filter(investor=user).values_list('tax_year', flat=True).distinct()
        
        all_years = sorted(set(list(doc_years) + list(summary_years)), reverse=True)
        
        # If no years, return current and last year
        if not all_years:
            current_year = timezone.now().year
            all_years = [current_year - 1, current_year - 2]
        
        return Response({
            'success': True,
            'years': all_years,
        })
    
    @action(detail=False, methods=['get'], url_path='planning')
    def tax_planning(self, request):
        """Get tax planning tips and important dates for Tax Planning tab"""
        user = request.user
        current_year = timezone.now().year
        tax_year = int(request.query_params.get('year', current_year))
        
        # Tax Planning Tips (can be customized per user in future)
        tips = [
            {
                'id': 1,
                'title': 'Harvest Tax Losses',
                'description': 'Consider selling underperforming investments to offset gains.',
                'color': '#FFF3CD',  # Yellow
                'icon': 'harvest',
            },
            {
                'id': 2,
                'title': 'Maximize Deductions',
                'description': 'Track all investment-related expenses for deductions.',
                'color': '#D4EDDA',  # Green
                'icon': 'deductions',
            },
            {
                'id': 3,
                'title': 'Retirement Accounts',
                'description': 'Consider tax-advantaged retirement account investments.',
                'color': '#FFE4CC',  # Orange
                'icon': 'retirement',
            },
        ]
        
        # Important Tax Dates
        important_dates = [
            {
                'id': 1,
                'title': 'Q1 Estimated Tax Due',
                'date': f'April 15, {tax_year}',
                'date_iso': f'{tax_year}-04-15',
                'icon': 'calendar',
            },
            {
                'id': 2,
                'title': 'K-1 Deadline',
                'date': f'March 15, {tax_year}',
                'date_iso': f'{tax_year}-03-15',
                'icon': 'calendar',
            },
            {
                'id': 3,
                'title': 'Tax Filing Deadline',
                'date': f'April 15, {tax_year}',
                'date_iso': f'{tax_year}-04-15',
                'icon': 'calendar',
            },
            {
                'id': 4,
                'title': 'Q2 Estimated Tax Due',
                'date': f'June 15, {tax_year}',
                'date_iso': f'{tax_year}-06-15',
                'icon': 'calendar',
            },
            {
                'id': 5,
                'title': 'Q3 Estimated Tax Due',
                'date': f'September 15, {tax_year}',
                'date_iso': f'{tax_year}-09-15',
                'icon': 'calendar',
            },
            {
                'id': 6,
                'title': 'Q4 Estimated Tax Due',
                'date': f'January 15, {tax_year + 1}',
                'date_iso': f'{tax_year + 1}-01-15',
                'icon': 'calendar',
            },
        ]
        
        return Response({
            'success': True,
            'tax_year': tax_year,
            'tips': tips,
            'important_dates': important_dates,
        })


class DocumentCenterViewSet(viewsets.ViewSet):
    """
    ViewSet for Document Center - Investor Documents Management
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get all documents with optional filters"""
        user = request.user
        
        # Get filters
        category = request.query_params.get('category', None)
        search = request.query_params.get('search', None)
        status_filter = request.query_params.get('status', None)
        
        documents = InvestorDocument.objects.filter(investor=user)
        
        # Apply filters
        if category and category != 'all':
            documents = documents.filter(category=category)
        if status_filter:
            documents = documents.filter(status=status_filter)
        if search:
            documents = documents.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search) |
                Q(fund_name__icontains=search)
            )
        
        # Order by upload date (newest first)
        documents = documents.order_by('-uploaded_at')
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(documents, request)
        
        serializer = InvestorDocumentSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get category counts for tabs"""
        user = request.user
        
        documents = InvestorDocument.objects.filter(investor=user)
        
        # Count by category
        all_count = documents.count()
        investment_count = documents.filter(category='investment').count()
        reports_count = documents.filter(category='reports').count()
        kyc_count = documents.filter(category='kyc').count()
        other_count = documents.filter(category='other').count()
        
        return Response({
            'success': True,
            'categories': [
                {'key': 'all', 'label': 'All Documents', 'count': all_count},
                {'key': 'investment', 'label': 'Investment', 'count': investment_count},
                {'key': 'reports', 'label': 'Reports', 'count': reports_count},
                {'key': 'kyc', 'label': 'KYC', 'count': kyc_count},
                {'key': 'other', 'label': 'Other', 'count': other_count},
            ],
        })
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new document"""
        serializer = InvestorDocumentUploadSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            document = serializer.save()
            return Response({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': InvestorDocumentSerializer(document, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'error': 'Invalid data',
            'details': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a specific document"""
        user = request.user
        
        try:
            document = InvestorDocument.objects.get(id=pk, investor=user)
        except InvestorDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not document.file:
            return Response(
                {'error': 'No file attached to this document'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.http import FileResponse
        response = FileResponse(document.file.open(), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{document.title}.{document.file_type.lower()}"'
        return response
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """Delete a document"""
        user = request.user
        
        try:
            document = InvestorDocument.objects.get(id=pk, investor=user)
        except InvestorDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        document.delete()
        
        return Response({
            'success': True,
            'message': 'Document deleted successfully',
        })
    
    def retrieve(self, request, pk=None):
        """Get single document detail"""
        user = request.user
        
        try:
            document = InvestorDocument.objects.get(id=pk, investor=user)
        except InvestorDocument.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InvestorDocumentSerializer(document, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data,
        })

