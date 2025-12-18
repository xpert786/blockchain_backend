"""
Document Utilities for Transfer Agreement Documents.

This module provides utilities for:
1. Generating PDF documents for transfer agreements
2. Managing signatures on documents
3. Creating different document types (transfer_request, acceptance, final_agreement)
"""

import os
import uuid
from io import BytesIO
from datetime import datetime
from django.core.files.base import ContentFile
from django.utils import timezone
from django.conf import settings

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_transfer_request_document(transfer, requester_signature, signature_ip, signature_type='text'):
    """
    Generate Transfer Request Document when Investor A confirms.
    
    This document contains:
    - Transfer details (SPV, amount, percentage)
    - Requester (Investor A) information
    - Recipient (Investor B) information
    - Requester's signature
    
    Args:
        transfer: Transfer model instance
        requester_signature: Signature data (text or base64 image)
        signature_ip: IP address of signer
        signature_type: 'text' or 'image'
    
    Returns:
        TransferAgreementDocument instance
    """
    from .models import TransferAgreementDocument
    
    # Generate document data
    document_data = {
        'transfer_id': transfer.transfer_id,
        'transfer_type': transfer.get_transfer_type_display(),
        'spv_name': transfer.spv.display_name,
        'spv_id': transfer.spv.id,
        
        # Requester Info
        'requester_name': transfer.requester.get_full_name() or transfer.requester.username,
        'requester_email': transfer.requester.email,
        'requester_id': transfer.requester.id,
        
        # Recipient Info
        'recipient_name': transfer.recipient.get_full_name() or transfer.recipient.username,
        'recipient_email': transfer.recipient.email,
        'recipient_id': transfer.recipient.id,
        
        # Transfer Details
        'ownership_percentage': float(transfer.ownership_percentage_transferred),
        'amount': float(transfer.amount),
        'transfer_fee': float(transfer.transfer_fee),
        'net_amount': float(transfer.net_amount),
        
        # Ownership Before
        'requester_ownership_before': float(transfer.requester_ownership_before),
        'recipient_ownership_before': float(transfer.recipient_ownership_before),
        
        # Signature Info
        'requester_signature': requester_signature,
        'requester_signature_type': signature_type,
        'requester_signed_at': timezone.now().isoformat(),
        'requester_signature_ip': signature_ip,
        
        # Document Generation Info
        'generated_at': timezone.now().isoformat(),
        'document_type': 'transfer_request',
    }
    
    # Generate PDF
    pdf_content = generate_pdf_content(
        document_type='transfer_request',
        document_data=document_data,
        title=f"Transfer Request - {transfer.transfer_id}"
    )
    
    # Create the document record
    agreement_doc = TransferAgreementDocument(
        transfer=transfer,
        document_type='transfer_request',
        title=f"Transfer Request Document - {transfer.transfer_id}",
        description=f"Transfer request from {document_data['requester_name']} to {document_data['recipient_name']} for {document_data['ownership_percentage']}% ownership in {document_data['spv_name']}",
        document_data=document_data,
        requester_signature_status='signed',
        requester_signed_at=timezone.now(),
        requester_signature_ip=signature_ip,
        requester_signature_data=requester_signature,
        recipient_signature_status='pending',
        can_requester_view=True,
        can_recipient_view=True,
        can_requester_download=True,
        can_recipient_download=True,
    )
    
    # Save PDF file
    filename = f"transfer_request_{transfer.transfer_id}_{uuid.uuid4().hex[:8]}.pdf"
    agreement_doc.file.save(filename, ContentFile(pdf_content), save=False)
    agreement_doc.file_size = len(pdf_content)
    agreement_doc.save()
    
    return agreement_doc


def generate_acceptance_document(transfer, recipient_signature, signature_ip, signature_type='text'):
    """
    Generate Acceptance Document when Investor B accepts.
    
    This document contains:
    - Transfer details
    - Recipient (Investor B) acceptance confirmation
    - Recipient's signature
    
    Args:
        transfer: Transfer model instance
        recipient_signature: Signature data (text or base64 image)
        signature_ip: IP address of signer
        signature_type: 'text' or 'image'
    
    Returns:
        TransferAgreementDocument instance
    """
    from .models import TransferAgreementDocument
    
    document_data = {
        'transfer_id': transfer.transfer_id,
        'transfer_type': transfer.get_transfer_type_display(),
        'spv_name': transfer.spv.display_name,
        'spv_id': transfer.spv.id,
        
        # Requester Info
        'requester_name': transfer.requester.get_full_name() or transfer.requester.username,
        'requester_email': transfer.requester.email,
        'requester_id': transfer.requester.id,
        
        # Recipient Info
        'recipient_name': transfer.recipient.get_full_name() or transfer.recipient.username,
        'recipient_email': transfer.recipient.email,
        'recipient_id': transfer.recipient.id,
        
        # Transfer Details
        'ownership_percentage': float(transfer.ownership_percentage_transferred),
        'amount': float(transfer.amount),
        'transfer_fee': float(transfer.transfer_fee),
        'net_amount': float(transfer.net_amount),
        
        # Ownership
        'requester_ownership_before': float(transfer.requester_ownership_before),
        'recipient_ownership_before': float(transfer.recipient_ownership_before),
        
        # Signature Info
        'recipient_signature': recipient_signature,
        'recipient_signature_type': signature_type,
        'recipient_signed_at': timezone.now().isoformat(),
        'recipient_signature_ip': signature_ip,
        
        # Document Generation Info
        'generated_at': timezone.now().isoformat(),
        'document_type': 'acceptance',
    }
    
    # Generate PDF
    pdf_content = generate_pdf_content(
        document_type='acceptance',
        document_data=document_data,
        title=f"Transfer Acceptance - {transfer.transfer_id}"
    )
    
    # Create the document record
    agreement_doc = TransferAgreementDocument(
        transfer=transfer,
        document_type='acceptance',
        title=f"Acceptance Document - {transfer.transfer_id}",
        description=f"Acceptance by {document_data['recipient_name']} for transfer from {document_data['requester_name']}",
        document_data=document_data,
        requester_signature_status='pending',
        recipient_signature_status='signed',
        recipient_signed_at=timezone.now(),
        recipient_signature_ip=signature_ip,
        recipient_signature_data=recipient_signature,
        can_requester_view=True,
        can_recipient_view=True,
        can_requester_download=True,
        can_recipient_download=True,
    )
    
    # Save PDF file
    filename = f"acceptance_{transfer.transfer_id}_{uuid.uuid4().hex[:8]}.pdf"
    agreement_doc.file.save(filename, ContentFile(pdf_content), save=False)
    agreement_doc.file_size = len(pdf_content)
    agreement_doc.save()
    
    return agreement_doc


def generate_final_agreement_document(transfer, requester_signature, requester_signature_ip, 
                                       recipient_signature, recipient_signature_ip,
                                       requester_signature_type='text', recipient_signature_type='text'):
    """
    Generate Final Transfer Agreement with both signatures.
    
    This document contains:
    - Complete transfer details
    - Both parties' information
    - Both signatures
    
    Args:
        transfer: Transfer model instance
        requester_signature: Requester's signature data
        requester_signature_ip: Requester's IP address
        recipient_signature: Recipient's signature data
        recipient_signature_ip: Recipient's IP address
        requester_signature_type: 'text' or 'image'
        recipient_signature_type: 'text' or 'image'
    
    Returns:
        TransferAgreementDocument instance
    """
    from .models import TransferAgreementDocument
    
    # Get previous signatures from the transfer request document
    transfer_request_doc = transfer.agreement_documents.filter(
        document_type='transfer_request',
        is_latest=True
    ).first()
    
    if transfer_request_doc and transfer_request_doc.requester_signature_data:
        requester_signature = transfer_request_doc.requester_signature_data
        requester_signature_ip = transfer_request_doc.requester_signature_ip
        requester_signed_at = transfer_request_doc.requester_signed_at
    else:
        requester_signed_at = timezone.now()
    
    document_data = {
        'transfer_id': transfer.transfer_id,
        'transfer_type': transfer.get_transfer_type_display(),
        'spv_name': transfer.spv.display_name,
        'spv_id': transfer.spv.id,
        
        # Requester Info
        'requester_name': transfer.requester.get_full_name() or transfer.requester.username,
        'requester_email': transfer.requester.email,
        'requester_id': transfer.requester.id,
        
        # Recipient Info
        'recipient_name': transfer.recipient.get_full_name() or transfer.recipient.username,
        'recipient_email': transfer.recipient.email,
        'recipient_id': transfer.recipient.id,
        
        # Transfer Details
        'ownership_percentage': float(transfer.ownership_percentage_transferred),
        'amount': float(transfer.amount),
        'transfer_fee': float(transfer.transfer_fee),
        'net_amount': float(transfer.net_amount),
        
        # Ownership
        'requester_ownership_before': float(transfer.requester_ownership_before),
        'recipient_ownership_before': float(transfer.recipient_ownership_before),
        
        # Requester Signature Info
        'requester_signature': requester_signature,
        'requester_signature_type': requester_signature_type,
        'requester_signed_at': requester_signed_at.isoformat() if requester_signed_at else timezone.now().isoformat(),
        'requester_signature_ip': requester_signature_ip,
        
        # Recipient Signature Info
        'recipient_signature': recipient_signature,
        'recipient_signature_type': recipient_signature_type,
        'recipient_signed_at': timezone.now().isoformat(),
        'recipient_signature_ip': recipient_signature_ip,
        
        # Document Generation Info
        'generated_at': timezone.now().isoformat(),
        'document_type': 'final_agreement',
    }
    
    # Generate PDF
    pdf_content = generate_pdf_content(
        document_type='final_agreement',
        document_data=document_data,
        title=f"Transfer Agreement - {transfer.transfer_id}"
    )
    
    # Create the document record
    agreement_doc = TransferAgreementDocument(
        transfer=transfer,
        document_type='final_agreement',
        title=f"Final Transfer Agreement - {transfer.transfer_id}",
        description=f"Final transfer agreement between {document_data['requester_name']} and {document_data['recipient_name']} for {document_data['ownership_percentage']}% ownership in {document_data['spv_name']}",
        document_data=document_data,
        requester_signature_status='signed',
        requester_signed_at=requester_signed_at,
        requester_signature_ip=requester_signature_ip,
        requester_signature_data=requester_signature,
        recipient_signature_status='signed',
        recipient_signed_at=timezone.now(),
        recipient_signature_ip=recipient_signature_ip,
        recipient_signature_data=recipient_signature,
        can_requester_view=True,
        can_recipient_view=True,
        can_requester_download=True,
        can_recipient_download=True,
    )
    
    # Save PDF file
    filename = f"final_agreement_{transfer.transfer_id}_{uuid.uuid4().hex[:8]}.pdf"
    agreement_doc.file.save(filename, ContentFile(pdf_content), save=False)
    agreement_doc.file_size = len(pdf_content)
    agreement_doc.save()
    
    return agreement_doc


def generate_pdf_content(document_type, document_data, title):
    """
    Generate PDF content for a document.
    
    Args:
        document_type: 'transfer_request', 'acceptance', or 'final_agreement'
        document_data: Dictionary containing all document data
        title: Document title
    
    Returns:
        bytes: PDF content
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback: generate a simple text-based PDF representation
        return generate_simple_pdf(document_type, document_data, title)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Build story (content)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.darkblue
    )
    
    # Title based on document type
    if document_type == 'transfer_request':
        doc_title = "TRANSFER REQUEST DOCUMENT"
        description = "This document confirms the transfer request initiated by the Seller (Investor A)"
    elif document_type == 'acceptance':
        doc_title = "TRANSFER ACCEPTANCE DOCUMENT"
        description = "This document confirms the acceptance by the Buyer (Investor B)"
    else:  # final_agreement
        doc_title = "FINAL TRANSFER AGREEMENT"
        description = "This document serves as the final binding agreement between both parties"
    
    story.append(Paragraph(doc_title, title_style))
    story.append(Paragraph(f"Transfer ID: {document_data.get('transfer_id', 'N/A')}", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(description, normal_style))
    story.append(Spacer(1, 24))
    
    # SPV Information
    story.append(Paragraph("SPV INFORMATION", heading_style))
    story.append(Paragraph(f"SPV Name: {document_data.get('spv_name', 'N/A')}", normal_style))
    story.append(Paragraph(f"Transfer Type: {document_data.get('transfer_type', 'N/A')}", normal_style))
    story.append(Spacer(1, 18))
    
    # Parties Information
    story.append(Paragraph("PARTIES", heading_style))
    
    # Seller (Requester)
    story.append(Paragraph("<b>Seller (Transferor):</b>", normal_style))
    story.append(Paragraph(f"Name: {document_data.get('requester_name', 'N/A')}", normal_style))
    story.append(Paragraph(f"Email: {document_data.get('requester_email', 'N/A')}", normal_style))
    story.append(Spacer(1, 12))
    
    # Buyer (Recipient)
    story.append(Paragraph("<b>Buyer (Transferee):</b>", normal_style))
    story.append(Paragraph(f"Name: {document_data.get('recipient_name', 'N/A')}", normal_style))
    story.append(Paragraph(f"Email: {document_data.get('recipient_email', 'N/A')}", normal_style))
    story.append(Spacer(1, 18))
    
    # Transfer Details
    story.append(Paragraph("TRANSFER DETAILS", heading_style))
    
    transfer_data = [
        ['Description', 'Value'],
        ['Ownership Percentage', f"{document_data.get('ownership_percentage', 0)}%"],
        ['Transfer Amount', f"${document_data.get('amount', 0):,.2f}"],
        ['Transfer Fee', f"${document_data.get('transfer_fee', 0):,.2f}"],
        ['Net Amount', f"${document_data.get('net_amount', 0):,.2f}"],
        ['Seller Ownership Before', f"{document_data.get('requester_ownership_before', 0)}%"],
        ['Buyer Ownership Before', f"{document_data.get('recipient_ownership_before', 0)}%"],
    ]
    
    table = Table(transfer_data, colWidths=[3*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 24))
    
    # Signatures Section
    story.append(Paragraph("SIGNATURES", heading_style))
    
    # Requester Signature
    if document_type in ['transfer_request', 'final_agreement']:
        story.append(Paragraph("<b>Seller (Investor A) Signature:</b>", normal_style))
        signature = document_data.get('requester_signature', 'N/A')
        if document_data.get('requester_signature_type') == 'text':
            story.append(Paragraph(f"<i>{signature}</i>", signature_style))
        else:
            story.append(Paragraph(f"[Digital Signature Attached]", signature_style))
        story.append(Paragraph(f"Signed at: {document_data.get('requester_signed_at', 'N/A')}", normal_style))
        story.append(Paragraph(f"IP Address: {document_data.get('requester_signature_ip', 'N/A')}", normal_style))
        story.append(Spacer(1, 18))
    
    # Recipient Signature
    if document_type in ['acceptance', 'final_agreement']:
        story.append(Paragraph("<b>Buyer (Investor B) Signature:</b>", normal_style))
        signature = document_data.get('recipient_signature', 'N/A')
        if document_data.get('recipient_signature_type') == 'text':
            story.append(Paragraph(f"<i>{signature}</i>", signature_style))
        else:
            story.append(Paragraph(f"[Digital Signature Attached]", signature_style))
        story.append(Paragraph(f"Signed at: {document_data.get('recipient_signed_at', 'N/A')}", normal_style))
        story.append(Paragraph(f"IP Address: {document_data.get('recipient_signature_ip', 'N/A')}", normal_style))
    
    # Footer
    story.append(Spacer(1, 36))
    story.append(Paragraph("-" * 60, normal_style))
    story.append(Paragraph(f"Document Generated: {document_data.get('generated_at', 'N/A')}", normal_style))
    story.append(Paragraph("This document is electronically generated and is valid without manual signature.", normal_style))
    
    # Build PDF
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def generate_simple_pdf(document_type, document_data, title):
    """
    Fallback PDF generation without reportlab.
    Creates a simple text file with .pdf extension.
    """
    content_lines = [
        "=" * 60,
        title.upper(),
        "=" * 60,
        "",
        f"Transfer ID: {document_data.get('transfer_id', 'N/A')}",
        f"Document Type: {document_type.replace('_', ' ').title()}",
        f"Generated: {document_data.get('generated_at', 'N/A')}",
        "",
        "-" * 40,
        "SPV INFORMATION",
        "-" * 40,
        f"SPV Name: {document_data.get('spv_name', 'N/A')}",
        f"Transfer Type: {document_data.get('transfer_type', 'N/A')}",
        "",
        "-" * 40,
        "PARTIES",
        "-" * 40,
        "Seller (Transferor):",
        f"  Name: {document_data.get('requester_name', 'N/A')}",
        f"  Email: {document_data.get('requester_email', 'N/A')}",
        "",
        "Buyer (Transferee):",
        f"  Name: {document_data.get('recipient_name', 'N/A')}",
        f"  Email: {document_data.get('recipient_email', 'N/A')}",
        "",
        "-" * 40,
        "TRANSFER DETAILS",
        "-" * 40,
        f"Ownership Percentage: {document_data.get('ownership_percentage', 0)}%",
        f"Transfer Amount: ${document_data.get('amount', 0):,.2f}",
        f"Transfer Fee: ${document_data.get('transfer_fee', 0):,.2f}",
        f"Net Amount: ${document_data.get('net_amount', 0):,.2f}",
        "",
        "-" * 40,
        "SIGNATURES",
        "-" * 40,
    ]
    
    if document_type in ['transfer_request', 'final_agreement']:
        content_lines.extend([
            "Seller Signature:",
            f"  Signature: {document_data.get('requester_signature', 'N/A')}",
            f"  Signed at: {document_data.get('requester_signed_at', 'N/A')}",
            f"  IP Address: {document_data.get('requester_signature_ip', 'N/A')}",
            "",
        ])
    
    if document_type in ['acceptance', 'final_agreement']:
        content_lines.extend([
            "Buyer Signature:",
            f"  Signature: {document_data.get('recipient_signature', 'N/A')}",
            f"  Signed at: {document_data.get('recipient_signed_at', 'N/A')}",
            f"  IP Address: {document_data.get('recipient_signature_ip', 'N/A')}",
            "",
        ])
    
    content_lines.extend([
        "=" * 60,
        "This document is electronically generated.",
        "=" * 60,
    ])
    
    return '\n'.join(content_lines).encode('utf-8')

