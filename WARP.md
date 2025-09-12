# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PIAS (Predictive Inventory Analyzer System) v2.0 is a professional Flask-based web application for comprehensive inventory management and analytics. It features AI-powered insights via Groq integration, advanced data processing, professional calculations, and modern web UI.

## Core Architecture

### Modular Design
The application follows a clean modular architecture:

- **`api.py`**: Main Flask application server with REST API endpoints
- **`analysis/`**: Core analysis engine package containing:
  - `data_processor.py`: Intelligent CSV processing and column detection
  - `calculations.py`: Professional inventory KPI calculations (EOQ, ABC analysis, turnover rates)  
  - `chart_generator.py`: Advanced matplotlib/seaborn chart generation
- **`database.py`**: SQLite database layer for session management and persistence
- **`templates/`**: Frontend templates with modern UI

### Data Flow Architecture
1. **Upload Phase**: CSV files processed via `DataProcessor` with intelligent column mapping
2. **Analysis Phase**: `InventoryCalculations` performs professional inventory metrics
3. **Visualization Phase**: `ChartGenerator` creates publication-ready charts
4. **Storage Phase**: Session data persisted in SQLite via `database.py`
5. **AI Phase**: Optional Groq AI integration for intelligent recommendations

### Session Management System
The app uses a hybrid session storage:
- **Production**: SQLite database with expiration handling
- **Development**: In-memory fallback when database unavailable
- Session data includes DataFrame JSON, column mappings, KPIs, and metadata

## Essential Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (required for AI features)
cp .env.example .env
# Edit .env file with your API keys

# Run development server
python api.py

# Run with debug mode
# Set debug=True in api.py for detailed error messages
```

### Production Deployment
```bash
# Run with Gunicorn (production ready)
gunicorn -c gunicorn_config.py api:app

# Database cleanup (remove expired sessions)
python -c "from database import db; db.cleanup_expired_sessions()"
```

### Testing and Debugging
```bash
# Test API health
curl http://localhost:5000/api/health

# Test with sample data
# Upload sample_inventory.csv through the web interface at http://localhost:5000

# Debug mode for detailed errors
# Modify api.py: app.run(debug=True, host='0.0.0.0', port=5000)
```

## Key Technical Concepts

### Professional Inventory Calculations
The system implements industry-standard formulas:
- **Inventory Turnover**: COGS / Average Inventory Value
- **Days of Supply**: (Current Stock / Monthly Sales) × 30
- **Economic Order Quantity (EOQ)**: √((2 × Annual Demand × Ordering Cost) / Holding Cost)
- **ABC Analysis**: Pareto classification based on revenue impact
- **Priority Scoring**: Multi-factor algorithm for reorder prioritization

### Intelligent Column Detection
`DataProcessor` uses fuzzy matching with keyword priorities to automatically detect CSV columns:
- Handles variations in column names (e.g., "stock", "inventory", "quantity", "qty")
- Supports multiple languages and naming conventions
- Provides data quality analysis and recommendations

### AI Integration Architecture
- **Primary**: Groq API for context-aware inventory advice
- **Fallback**: Rule-based professional response system  
- **Graceful Degradation**: System fully functional without API keys
- **Context Awareness**: AI receives actual inventory data for intelligent recommendations

### Chart Generation System
- **Engine**: matplotlib + seaborn for publication-quality visualizations
- **Output**: Base64-encoded charts for web display
- **Charts**: Category performance, health distribution, turnover analysis, priority reorders
- **Fallback**: Simple chart generator when advanced dependencies unavailable

## API Endpoints Reference

- **`GET /api/health`**: System health check and feature availability
- **`POST /api/upload-csv`**: Upload and process inventory CSV files (25MB limit)
- **`POST /api/filter-products`**: Advanced filtering with category/status/search/ABC class
- **`POST /api/chat`**: AI assistant interaction with context awareness
- **`POST /api/export-report`**: Generate JSON reports and insights
- **`POST /api/columns-info`**: CSV structure analysis and validation

## CSV Data Requirements

### Required Columns (auto-detected)
- **Product Name**: `name`, `product`, `item`, `description`
- **Category**: `category`, `type`, `class`, `group`
- **Current Stock**: `stock`, `inventory`, `quantity`, `qty`
- **Monthly Sales**: `sales`, `sold`, `demand`, `volume`

### Optional Columns (enhance analysis)
- **Reorder Level**: `reorder`, `reorder_level`, `min_stock`
- **Unit Price**: `price`, `cost`, `unit_price`
- **Supplier**: `supplier`, `vendor`, `source`

## Environment Configuration

Essential environment variables in `.env`:
- **`GROQ_API_KEY`**: For AI features (get from https://console.groq.com/keys)
- **`SECRET_KEY`**: Flask session security (generate secure random string)

## Database Schema

SQLite database with three main tables:
- **`sessions`**: CSV processing sessions with expiration
- **`users`**: User information and authentication  
- **`analytics`**: Event logging and usage statistics

## Common Development Workflows

### Adding New Calculation Metrics
1. Extend `InventoryCalculations` class in `analysis/calculations.py`
2. Update KPI calculation in `calculate_kpis()` method
3. Add corresponding chart in `chart_generator.py` if needed
4. Update API response structure in `api.py`

### Enhancing AI Capabilities
1. Modify chat endpoint in `api.py` around line 500+
2. Update context preparation for Groq API
3. Enhance fallback response system for non-API scenarios
4. Test both API and fallback modes

### Adding New Chart Types
1. Extend `ChartGenerator` class in `analysis/chart_generator.py`
2. Follow matplotlib/seaborn best practices for publication quality
3. Ensure charts are base64 encoded for web display
4. Update chart generation call in `api.py` upload endpoint

## Performance Characteristics

- **Processing Speed**: ~1000 products/second
- **Memory Usage**: ~50MB for 10K products
- **File Size Limit**: 25MB (configurable)
- **Chart Generation**: 2-3 seconds per chart set
- **Session Expiry**: 24 hours (configurable)

## Error Handling Patterns

The application uses comprehensive error handling:
- **Validation Errors**: CSV format and column requirements
- **Processing Errors**: Data quality issues and calculation failures  
- **AI Errors**: Groq API failures with intelligent fallbacks
- **System Errors**: Database, file system, and resource issues
- **User-Friendly**: Sanitized error messages with actionable suggestions
