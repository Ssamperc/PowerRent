"""
Inversión de Dependencias (DI) para generación de reportes.

Existe una interfaz abstracta IReporteGenerator y dos implementaciones concretas:
  - ReportePDFGenerator  → genera reporte en PDF
  - ReporteExcelGenerator → genera reporte en Excel (CSV-compatible)

El controlador ReporteView inyecta la implementación según el parámetro 'formato'.
"""
from abc import ABC, abstractmethod


class IReporteGenerator(ABC):
    """Interfaz abstracta para generar reportes de equipos"""

    @abstractmethod
    def generar(self, equipos, titulo: str) -> bytes:
        """
        Genera el reporte y retorna bytes del archivo.
        :param equipos: QuerySet/lista de Equipo
        :param titulo: Título del reporte
        :return: bytes del archivo generado
        """
        pass

    @abstractmethod
    def content_type(self) -> str:
        """MIME type del archivo generado"""
        pass

    @abstractmethod
    def extension(self) -> str:
        """Extensión del archivo (sin punto)"""
        pass
