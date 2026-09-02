import os
import io
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.accounting.statements import FinancialStatementGenerator
from app.storage.base import BaseStorage

class PDFReportGenerator:
    """
    Generates downloadable PDF Financial Reports (BRD §47).
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.statement_gen = FinancialStatementGenerator(storage)

    def generate_pdf_report(self, start_date: str, end_date: str, output_path: Optional[str] = None) -> bytes:
        """
        Builds a PDF report for period [start_date, end_date]. Returns bytes or writes to output_path.
        """
        income_stmt = self.statement_gen.generate_income_statement(start_date, end_date)
        balance_sheet = self.statement_gen.generate_balance_sheet()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            output_path if output_path else buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=15
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            "NormalText",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )

        # 1. Header
        story.append(Paragraph("Personal Finance Report", title_style))
        story.append(Paragraph(f"Periode Laporan: <b>{start_date}</b> s/d <b>{end_date}</b> | Tanggal Cetak: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # 2. Executive Summary Cards Table
        net_inc = income_stmt["net_income"]
        net_worth = balance_sheet["net_worth"]
        total_assets = balance_sheet["assets"]["total_assets"]
        total_liab = balance_sheet["liabilities"]["total_liabilities"]

        integrity_status = "VERIFIED / BALANCE" if balance_sheet["is_balanced"] else f"WARNING ({balance_sheet['discrepancy']:,.0f})"
        integrity_color = "#16a34a" if balance_sheet["is_balanced"] else "#dc2626"

        summary_data = [
            [
                Paragraph(f"<b>Pemasukan:</b><br/>Rp{income_stmt['total_income']:,.0f}", normal_style),
                Paragraph(f"<b>Pengeluaran:</b><br/>Rp{income_stmt['total_expense']:,.0f}", normal_style),
                Paragraph(f"<b>Net Income:</b><br/>Rp{net_inc:,.0f}", normal_style)
            ],
            [
                Paragraph(f"<b>Total Aset:</b><br/>Rp{total_assets:,.0f}", normal_style),
                Paragraph(f"<b>Total Liabilitas:</b><br/>Rp{total_liab:,.0f}", normal_style),
                Paragraph(f"<b>Net Worth:</b><br/>Rp{net_worth:,.0f}", normal_style)
            ]
        ]
        sum_table = Table(summary_data, colWidths=[2.4*inch, 2.4*inch, 2.4*inch])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(sum_table)
        story.append(Spacer(1, 10))

        # Financial Integrity Banner
        int_table = Table([[
            Paragraph(f"<b>Status Integritas Keuangan:</b> <font color='{integrity_color}'><b>{integrity_status}</b></font> (Assets = Liabilities + Equity)", normal_style)
        ]], colWidths=[7.2*inch])
        int_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (0,0), 1, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (0,0), 6),
        ]))
        story.append(int_table)
        story.append(Spacer(1, 14))

        # 3. Income Statement Breakdown
        story.append(Paragraph("1. Laporan Laba Rugi (Income Statement)", section_heading))
        inc_rows = [["Kategori", "Tipe", "Jumlah (IDR)"]]
        for cat, amt in income_stmt["income_by_category"].items():
            inc_rows.append([cat, "Pemasukan", f"Rp{amt:,.0f}"])
        for cat, amt in income_stmt["expense_by_category"].items():
            inc_rows.append([cat, "Pengeluaran", f"Rp{amt:,.0f}"])
        inc_rows.append(["NET INCOME", "", f"Rp{income_stmt['net_income']:,.0f}"])

        t_inc = Table(inc_rows, colWidths=[3.6*inch, 1.8*inch, 1.8*inch])
        t_inc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#f1f5f9")),
        ]))
        story.append(t_inc)
        story.append(Spacer(1, 14))

        # 4. Balance Sheet Breakdown
        story.append(Paragraph("2. Neraca Keuangan (Balance Sheet)", section_heading))
        ast = balance_sheet["assets"]
        lia = balance_sheet["liabilities"]
        eq = balance_sheet["equity"]

        bs_rows = [
            ["Komponen Financial Position", "Jumlah (IDR)"],
            ["ASET", ""],
            ["  Cash & Bank", f"Rp{ast['cash_bank']:,.0f}"],
            ["  E-Wallet", f"Rp{ast['ewallet']:,.0f}"],
            ["  Prepaid Balance", f"Rp{ast['prepaid']:,.0f}"],
            ["  Investasi", f"Rp{ast['investment']:,.0f}"],
            ["  Aset Tetap (Net Book Value)", f"Rp{ast['fixed_assets_nbv']:,.0f}"],
            ["TOTAL ASET", f"Rp{ast['total_assets']:,.0f}"],
            ["LIABILITAS & EKUITAS", ""],
            ["  Kartu Kredit", f"Rp{lia['credit_card']:,.0f}"],
            ["  Cicilan & Pinjaman", f"Rp{lia['installments'] + lia['loans']:,.0f}"],
            ["TOTAL LIABILITAS", f"Rp{lia['total_liabilities']:,.0f}"],
            ["  Ekuitas Awal", f"Rp{eq['opening_equity']:,.0f}"],
            ["  Akumulasi Net Income", f"Rp{eq['accumulated_net_income']:,.0f}"],
            ["TOTAL EKUITAS", f"Rp{eq['total_equity']:,.0f}"],
            ["TOTAL LIABILITAS & EKUITAS", f"Rp{balance_sheet['liabilities_and_equity']:,.0f}"]
        ]

        t_bs = Table(bs_rows, colWidths=[4.8*inch, 2.4*inch])
        t_bs.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
            ('FONTNAME', (0,1), (0,1), 'Helvetica-Bold'),
            ('FONTNAME', (0,7), (-1,7), 'Helvetica-Bold'),
            ('FONTNAME', (0,8), (0,8), 'Helvetica-Bold'),
            ('FONTNAME', (0,11), (-1,11), 'Helvetica-Bold'),
            ('FONTNAME', (0,14), (-1,14), 'Helvetica-Bold'),
            ('FONTNAME', (0,15), (-1,15), 'Helvetica-Bold'),
            ('BACKGROUND', (0,7), (-1,7), colors.HexColor("#f1f5f9")),
            ('BACKGROUND', (0,15), (-1,15), colors.HexColor("#f1f5f9")),
        ]))
        story.append(t_bs)
        story.append(Spacer(1, 14))

        # 5. Account Balances Table
        story.append(Paragraph("3. Saldo Rekening / Accounts", section_heading))
        acc_rows = [["Nama Account", "Tipe", "Saldo Saat Ini (IDR)"]]
        for acc in self.storage.get_all_accounts():
            acc_rows.append([acc.account_name, acc.account_type.value, f"Rp{acc.current_balance:,.0f}"])

        t_acc = Table(acc_rows, colWidths=[3.0*inch, 2.1*inch, 2.1*inch])
        t_acc.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        story.append(t_acc)

        doc.build(story)

        if output_path:
            with open(output_path, "rb") as f:
                return f.read()
        return buffer.getvalue()
