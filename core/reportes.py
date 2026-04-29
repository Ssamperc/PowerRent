"""
Implementaciones concretas de IReporteGenerator.
DI: interfaz IReporteGenerator + clases ReportePDFGenerator y ReporteExcelGenerator.
"""
import io
import csv
import struct
import zlib
from .interfaces.reporte_interface import IReporteGenerator


def _pdf_string(s):
    """Escape string for PDF"""
    return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)').replace('\n', '\\n')


class ReportePDFGenerator(IReporteGenerator):
    """Genera un reporte en formato PDF válido (sin librerías externas)."""

    def generar(self, equipos, titulo: str) -> bytes:
        lines = []
        offsets = []

        def obj(n, content):
            offsets.append(len('\n'.join(lines).encode('latin-1', 'replace')))
            lines.append(f'{n} 0 obj')
            lines.append(content)
            lines.append('endobj')
            lines.append('')

        lines.append('%PDF-1.4')
        lines.append('%\xe2\xe3\xcf\xd3')  # binary marker
        lines.append('')

        # Build page content stream
        content_parts = []
        content_parts.append('BT')
        content_parts.append('/F1 16 Tf')
        content_parts.append('50 780 Td')
        content_parts.append(f'({_pdf_string(titulo[:60])}) Tj')
        content_parts.append('/F1 9 Tf')
        content_parts.append('0 -20 Td')
        content_parts.append('(Generado por PowerRent | powerrent.co) Tj')
        content_parts.append('0 -5 Td')

        # Divider line
        content_parts.append('ET')
        content_parts.append('0.8 0.8 0.8 RG')
        content_parts.append('50 745 m 545 745 l S')
        content_parts.append('0 0 0 RG')
        content_parts.append('BT')
        content_parts.append('/F1 8 Tf')
        content_parts.append('50 732 Td')

        # Headers
        content_parts.append('(Nombre) Tj')
        content_parts.append('200 0 Td')
        content_parts.append('(Categoria) Tj')
        content_parts.append('100 0 Td')
        content_parts.append('(Precio/Dia COP) Tj')
        content_parts.append('110 0 Td')
        content_parts.append('(Estado) Tj')
        content_parts.append('-410 0 Td')

        y = -16
        for i, eq in enumerate(list(equipos)[:40]):
            nombre = _pdf_string(eq.nombre[:30])
            cat = _pdf_string(eq.categoria.nombre[:18])
            precio = f'${float(eq.precio_por_dia):,.0f}'
            estado = 'Disponible' if eq.disponible else 'No disponible'
            content_parts.append(f'{y} Td')
            content_parts.append(f'({nombre}) Tj')
            content_parts.append('200 0 Td')
            content_parts.append(f'({cat}) Tj')
            content_parts.append('100 0 Td')
            content_parts.append(f'({precio}) Tj')
            content_parts.append('110 0 Td')
            content_parts.append(f'({estado}) Tj')
            content_parts.append('-410 0 Td')
            y = -14

        content_parts.append('ET')
        stream = '\n'.join(content_parts).encode('latin-1', 'replace')

        # Objects
        obj(1, '<</Type /Catalog /Pages 2 0 R>>')
        obj(2, '<</Type /Pages /Kids [3 0 R] /Count 1>>')
        obj(3, (
            '<</Type /Page /Parent 2 0 R '
            '/MediaBox [0 0 595 842] '
            '/Contents 4 0 R '
            '/Resources <</Font <</F1 5 0 R>>>>>>'
        ))

        offsets.append(len('\n'.join(lines).encode('latin-1', 'replace')))
        lines.append('4 0 obj')
        lines.append(f'<</Length {len(stream)}>>')
        lines.append('stream')
        raw = '\n'.join(lines).encode('latin-1', 'replace') + b'\n' + stream + b'\nendstream\nendobj\n\n'

        suffix_lines = []
        suffix_lines.append('5 0 obj')
        suffix_lines.append('<</Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding>>')
        suffix_lines.append('endobj')
        suffix_lines.append('')

        xref_offset = len(raw) + len('\n'.join(suffix_lines).encode('latin-1', 'replace'))
        suffix_lines.append('xref')
        suffix_lines.append(f'0 6')
        suffix_lines.append('0000000000 65535 f ')
        for off in offsets[:5]:
            suffix_lines.append(f'{off:010d} 00000 n ')
        suffix_lines.append('trailer')
        suffix_lines.append('<</Size 6 /Root 1 0 R>>')
        suffix_lines.append('startxref')
        suffix_lines.append(str(xref_offset))
        suffix_lines.append('%%EOF')

        return raw + '\n'.join(suffix_lines).encode('latin-1', 'replace')

    def content_type(self) -> str:
        return 'application/pdf'

    def extension(self) -> str:
        return 'pdf'


class ReporteExcelGenerator(IReporteGenerator):
    """Genera un reporte en formato CSV (compatible con Excel)."""

    def generar(self, equipos, titulo: str) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([titulo])
        writer.writerow(['Generado por PowerRent'])
        writer.writerow([])
        writer.writerow([
            'Nombre', 'Categoría', 'Código', 'Marca', 'Modelo',
            'Precio/Día (COP)', 'Precio/Semana (COP)', 'Precio/Mes (COP)',
            'Depósito Garantía', 'Estado', 'Disponible'
        ])
        for eq in equipos:
            writer.writerow([
                eq.nombre,
                eq.categoria.nombre,
                eq.codigo_interno,
                eq.marca or '',
                eq.modelo or '',
                float(eq.precio_por_dia),
                float(eq.precio_por_semana) if eq.precio_por_semana else '',
                float(eq.precio_por_mes) if eq.precio_por_mes else '',
                float(eq.deposito_garantia),
                eq.get_estado_display(),
                'Sí' if eq.disponible else 'No',
            ])
        return buffer.getvalue().encode('utf-8-sig')

    def content_type(self) -> str:
        return 'text/csv'

    def extension(self) -> str:
        return 'csv'


def get_reporte_generator(formato: str) -> IReporteGenerator:
    """Fábrica de generadores — aplica la Inversión de Dependencias."""
    generadores = {
        'pdf': ReportePDFGenerator,
        'excel': ReporteExcelGenerator,
        'csv': ReporteExcelGenerator,
    }
    return generadores.get(formato.lower(), ReporteExcelGenerator)()
