"""
Syndicate Investment Request Approval Views

APIs for syndicate managers to:
1. View pending investment requests
2. Approve investment requests
3. Reject investment requests
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from investors.dashboard_models import Investment, Notification
from spv.models import SPV


class IsSyndicateManager(permissions.BasePermission):
    """Check if user is a syndicate manager or admin"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or getattr(request.user, 'role', '') in ['admin', 'syndicate']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investment_requests_list(request):
    """
    List all investment requests for syndicate manager.
    
    GET /api/syndicates/investment-requests/
    
    Query params:
    - status: pending_approval, approved, rejected, all (default: pending_approval)
    - spv_id: Filter by SPV
    - priority: low, medium, high
    """
    user = request.user
    
    # Get SPVs owned by this user (or all if admin)
    if user.is_staff or getattr(user, 'role', '') == 'admin':
        spv_ids = SPV.objects.values_list('id', flat=True)
    else:
        spv_ids = SPV.objects.filter(created_by=user).values_list('id', flat=True)
    
    # Base queryset - investments for user's SPVs
    queryset = Investment.objects.filter(
        spv_id__in=spv_ids
    ).select_related('investor', 'spv', 'approved_by')
    
    # Filter by status
    status_filter = request.query_params.get('status', 'pending_approval')
    if status_filter == 'all':
        queryset = queryset.filter(status__in=['pending_approval', 'approved', 'rejected'])
    elif status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Filter by SPV
    spv_id = request.query_params.get('spv_id')
    if spv_id:
        queryset = queryset.filter(spv_id=spv_id)
    
    # Filter by priority
    priority = request.query_params.get('priority')
    if priority:
        queryset = queryset.filter(priority=priority)
    
    queryset = queryset.order_by('-priority', '-created_at')
    
    # Build response
    requests_list = []
    for inv in queryset:
        requests_list.append({
            'id': inv.id,
            'investor': {
                'id': inv.investor.id,
                'name': inv.investor.get_full_name() or inv.investor.username,
                'email': inv.investor.email,
            },
            'spv': {
                'id': inv.spv.id if inv.spv else None,
                'name': inv.syndicate_name,
                'code': f'SPV-{inv.spv.id:03d}' if inv.spv else None,
            },
            'amount': float(inv.invested_amount),
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'priority': inv.priority,
            'request_message': inv.request_message,
            'created_at': inv.created_at.isoformat(),
            'approved_by': inv.approved_by.get_full_name() if inv.approved_by else None,
            'approved_at': inv.approved_at.isoformat() if inv.approved_at else None,
            'rejection_reason': inv.rejection_reason,
        })
    
    # Calculate stats
    all_requests = Investment.objects.filter(spv_id__in=spv_ids)
    stats = {
        'pending_requests': all_requests.filter(status='pending_approval').count(),
        'approved_today': all_requests.filter(
            status='approved',
            approved_at__date=timezone.now().date()
        ).count(),
        'rejected': all_requests.filter(status='rejected').count(),
        'high_priority': all_requests.filter(status='pending_approval', priority='high').count(),
    }
    
    return Response({
        'success': True,
        'stats': stats,
        'count': len(requests_list),
        'requests': requests_list
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investment_request_detail(request, request_id):
    """
    Get detailed view of an investment request.
    
    GET /api/syndicates/investment-requests/{id}/
    """
    user = request.user
    
    try:
        investment = Investment.objects.select_related(
            'investor', 'spv', 'approved_by'
        ).get(id=request_id)
    except Investment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Investment request not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission - must own the SPV or be admin
    if not (user.is_staff or getattr(user, 'role', '') == 'admin'):
        if investment.spv and investment.spv.created_by != user:
            return Response({
                'success': False,
                'error': 'You do not have permission to view this request'
            }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'success': True,
        'request': {
            'id': investment.id,
            'investor': {
                'id': investment.investor.id,
                'name': investment.investor.get_full_name() or investment.investor.username,
                'email': investment.investor.email,
            },
            'spv': {
                'id': investment.spv.id if investment.spv else None,
                'name': investment.syndicate_name,
                'display_name': investment.spv.display_name if investment.spv else None,
            },
            'amount': float(investment.invested_amount),
            'investment_type': investment.investment_type,
            'status': investment.status,
            'status_display': investment.get_status_display(),
            'priority': investment.priority,
            'request_message': investment.request_message,
            'created_at': investment.created_at.isoformat(),
            'approved_by': {
                'id': investment.approved_by.id,
                'name': investment.approved_by.get_full_name(),
            } if investment.approved_by else None,
            'approved_at': investment.approved_at.isoformat() if investment.approved_at else None,
            'rejection_reason': investment.rejection_reason,
        }
    })


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def approve_investment_request(request, request_id):
    """
    Approve an investment request.
    
    PATCH /api/syndicates/investment-requests/{id}/approve/
    
    After approval, investor can proceed to payment.
    """
    user = request.user
    
    try:
        investment = Investment.objects.select_related('investor', 'spv').get(
            id=request_id,
            status='pending_approval'
        )
    except Investment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Investment request not found or already processed'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    if not (user.is_staff or getattr(user, 'role', '') == 'admin'):
        if investment.spv and investment.spv.created_by != user:
            return Response({
                'success': False,
                'error': 'You do not have permission to approve this request'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Update investment
    investment.status = 'approved'
    investment.approved_by = user
    investment.approved_at = timezone.now()
    investment.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
    
    # Create notification for investor
    Notification.objects.create(
        user=investment.investor,
        notification_type='investment',
        title='Investment Request Approved!',
        message=f'Your investment request of ${investment.invested_amount:,.2f} in {investment.syndicate_name} has been approved. You can now proceed with payment.',
        priority='high',
        action_required=True,
        action_url=f'/investments/{investment.id}/pay',
        action_label='Proceed to Payment',
        related_investment=investment,
        related_spv=investment.spv,
    )
    
    return Response({
        'success': True,
        'message': 'Investment request approved successfully',
        'investment': {
            'id': investment.id,
            'status': investment.status,
            'approved_by': user.get_full_name() or user.username,
            'approved_at': investment.approved_at.isoformat(),
        }
    })


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def reject_investment_request(request, request_id):
    """
    Reject an investment request.
    
    PATCH /api/syndicates/investment-requests/{id}/reject/
    
    Payload:
    {
        "reason": "Investor does not meet minimum requirements"
    }
    """
    user = request.user
    reason = request.data.get('reason', '')
    
    try:
        investment = Investment.objects.select_related('investor', 'spv').get(
            id=request_id,
            status='pending_approval'
        )
    except Investment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Investment request not found or already processed'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    if not (user.is_staff or getattr(user, 'role', '') == 'admin'):
        if investment.spv and investment.spv.created_by != user:
            return Response({
                'success': False,
                'error': 'You do not have permission to reject this request'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Update investment
    investment.status = 'rejected'
    investment.approved_by = user
    investment.approved_at = timezone.now()
    investment.rejection_reason = reason
    investment.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
    
    # Create notification for investor
    Notification.objects.create(
        user=investment.investor,
        notification_type='investment',
        title='Investment Request Update',
        message=f'Your investment request of ${investment.invested_amount:,.2f} in {investment.syndicate_name} could not be approved at this time.' + (f' Reason: {reason}' if reason else ''),
        priority='high',
        action_required=False,
        related_investment=investment,
        related_spv=investment.spv,
    )
    
    return Response({
        'success': True,
        'message': 'Investment request rejected',
        'investment': {
            'id': investment.id,
            'status': investment.status,
            'rejection_reason': reason,
        }
    })
