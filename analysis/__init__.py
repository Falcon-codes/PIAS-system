"""
Predictive Inventory Analyzer System (PIAS)
Professional Inventory Analysis Engine

This package provides comprehensive inventory management and analytics capabilities:
- Intelligent CSV data processing and validation
- Professional inventory calculations and KPI analysis
- Advanced chart generation with publication-ready visualizations
- AI-powered insights and recommendations

Author: Tijani
Version: 2.0.0
"""

from .data_processor import DataProcessor
from .calculations import InventoryCalculations
from .chart_generator import ChartGenerator

__version__ = "2.0.0"
__author__ = "Tijani"

# Professional constants and configurations
DEFAULT_CHART_DPI = 150
MAX_PRODUCTS_DISPLAY = 50
DEFAULT_TURNOVER_THRESHOLD = 4.0
SAFETY_STOCK_MULTIPLIER = 1.5
CRITICAL_DAYS_THRESHOLD = 15
LOW_STOCK_DAYS_THRESHOLD = 30
HEALTHY_STOCK_MAX_DAYS = 90

# Export main classes
__all__ = [
    'DataProcessor',
    'InventoryCalculations', 
    'ChartGenerator',
    'DEFAULT_CHART_DPI',
    'MAX_PRODUCTS_DISPLAY',
    'DEFAULT_TURNOVER_THRESHOLD',
    'SAFETY_STOCK_MULTIPLIER',
    'CRITICAL_DAYS_THRESHOLD',
    'LOW_STOCK_DAYS_THRESHOLD',
    'HEALTHY_STOCK_MAX_DAYS'
]

def get_package_info():
    """Get package information and health check"""
    try:
        import pandas as pd
        import numpy as np
        import matplotlib
        import seaborn as sns
        
        return {
            'package_version': __version__,
            'author': __author__,
            'dependencies': {
                'pandas': pd.__version__,
                'numpy': np.__version__,
                'matplotlib': matplotlib.__version__,
                'seaborn': sns.__version__
            },
            'modules_loaded': {
                'DataProcessor': 'data_processor.py',
                'InventoryCalculations': 'calculations.py', 
                'ChartGenerator': 'chart_generator.py'
            },
            'status': 'healthy'
        }
    except ImportError as e:
        return {
            'package_version': __version__,
            'status': 'error',
            'error': f'Missing dependency: {str(e)}'
        }
