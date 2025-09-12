import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
import warnings

warnings.filterwarnings('ignore')


class DataProcessor:
    """
    Enhanced CSV Processing Engine for Inventory Analysis
    Handles intelligent column detection, data cleaning, and validation
    """

    def __init__(self):
        self.data = None
        self.columns_map = {}
        self.data_quality_report = {}

    def find_column(self, keywords: List[str], columns: List[str]) -> Optional[str]:
        """Enhanced column finder with fuzzy matching and priority ranking"""
        column_scores = {}
        
        for col in columns:
            col_lower = col.lower().strip()
            score = 0
            
            # Exact match gets highest score
            for keyword in keywords:
                if keyword.lower() == col_lower:
                    score += 100
                elif keyword.lower() in col_lower:
                    score += 50
                # Partial fuzzy matching
                elif any(k in col_lower for k in keyword.lower().split('_')):
                    score += 25
                    
            # Bonus for common inventory terms
            inventory_terms = ['qty', 'amount', 'level', 'count', 'volume', 'units']
            if any(term in col_lower for term in inventory_terms):
                score += 10
                
            if score > 0:
                column_scores[col] = score
        
        # Return column with highest score
        if column_scores:
            return max(column_scores, key=column_scores.get)
        return None

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """Intelligent column detection with comprehensive keyword matching"""
        
        columns_map = {}
        
        # Enhanced keyword mapping for better detection
        column_keywords = {
            'name': [
                'name', 'product', 'item', 'description', 'title', 'product_name', 
                'item_name', 'prod_name', 'sku', 'code', 'id'
            ],
            'category': [
                'category', 'catagory', 'cat', 'type', 'class', 'group', 'segment',
                'product_category', 'item_category', 'classification'
            ],
            'stock': [
                'stock', 'inventory', 'quantity', 'qty', 'current_stock', 
                'on_hand', 'available', 'balance', 'units', 'count', 'level',
                'current_quantity', 'stock_level', 'inventory_level'
            ],
            'sales': [
                'sales', 'sold', 'volume', 'demand', 'usage', 'consumption',
                'monthly_sales', 'sales_volume', 'units_sold', 'turnover_qty',
                'demand_qty', 'usage_rate', 'monthly_demand'
            ],
            'reorder': [
                'reorder', 'reorder_level', 'reorder_point', 'min_stock', 
                'minimum', 'safety_stock', 'threshold', 'trigger_level',
                'min_level', 'reorder_qty', 'minimum_stock'
            ],
            'price': [
                'price', 'cost', 'unit_price', 'unit_cost', 'value', 'amount',
                'rate', 'price_per_unit', 'cost_per_unit', 'unit_value'
            ],
            'supplier': [
                'supplier', 'vendor', 'source', 'provider', 'manufacturer',
                'supplier_name', 'vendor_name', 'supplier_id'
            ],
            'lead_time': [
                'lead_time', 'leadtime', 'delivery_time', 'order_time',
                'procurement_time', 'lead_days'
            ],
            'max_stock': [
                'max_stock', 'maximum', 'max_level', 'maximum_stock',
                'max_quantity', 'upper_limit', 'ceiling'
            ]
        }
        
        # Detect each column type
        for col_type, keywords in column_keywords.items():
            detected_col = self.find_column(keywords, df.columns.tolist())
            columns_map[col_type] = detected_col
            
        # Special handling for turnover (often calculated)
        turnover_keywords = ['turnover', 'turns', 'rotation', 'velocity', 'frequency']
        columns_map['turnover'] = self.find_column(turnover_keywords, df.columns.tolist())
        
        return columns_map

    def validate_required_columns(self, columns_map: Dict[str, Optional[str]]) -> Tuple[bool, List[str]]:
        """Enhanced validation with detailed reporting"""
        
        # Core required columns for basic analysis
        required_cols = ['name', 'category', 'stock', 'sales']
        
        # Preferred columns for advanced analysis
        preferred_cols = ['reorder', 'price']
        
        missing_required = [name for name in required_cols if not columns_map.get(name)]
        missing_preferred = [name for name in preferred_cols if not columns_map.get(name)]
        
        # Store validation results
        self.validation_report = {
            'required_missing': missing_required,
            'preferred_missing': missing_preferred,
            'detected_columns': {k: v for k, v in columns_map.items() if v is not None},
            'total_columns_detected': len([v for v in columns_map.values() if v is not None])
        }
        
        is_valid = len(missing_required) == 0
        
        return is_valid, missing_required

    def analyze_data_quality(self, df: pd.DataFrame, columns_map: Dict[str, str]) -> Dict:
        """Comprehensive data quality analysis"""
        
        quality_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_analysis': {},
            'data_issues': [],
            'recommendations': []
        }
        
        for col_type, col_name in columns_map.items():
            if col_name and col_name in df.columns:
                col_data = df[col_name]
                
                analysis = {
                    'null_count': col_data.isnull().sum(),
                    'null_percentage': (col_data.isnull().sum() / len(df)) * 100,
                    'unique_values': col_data.nunique(),
                    'data_type': str(col_data.dtype)
                }
                
                # Numeric column analysis
                if col_type in ['stock', 'sales', 'reorder', 'price', 'turnover']:
                    numeric_col = pd.to_numeric(col_data, errors='coerce')
                    
                    analysis.update({
                        'min_value': numeric_col.min(),
                        'max_value': numeric_col.max(),
                        'mean_value': numeric_col.mean(),
                        'median_value': numeric_col.median(),
                        'negative_values': (numeric_col < 0).sum(),
                        'zero_values': (numeric_col == 0).sum()
                    })
                    
                    # Flag potential issues
                    if analysis['negative_values'] > 0:
                        quality_report['data_issues'].append(
                            f"{col_name} has {analysis['negative_values']} negative values"
                        )
                    
                    if analysis['zero_values'] > len(df) * 0.5:
                        quality_report['data_issues'].append(
                            f"{col_name} has too many zero values ({analysis['zero_values']})"
                        )
                
                # Text column analysis
                elif col_type in ['name', 'category', 'supplier']:
                    analysis.update({
                        'avg_length': col_data.str.len().mean() if col_data.dtype == 'object' else 0,
                        'empty_strings': (col_data == '').sum()
                    })
                
                quality_report['column_analysis'][col_type] = analysis
        
        # Generate recommendations
        self._generate_data_recommendations(quality_report)
        
        return quality_report

    def _generate_data_recommendations(self, quality_report: Dict):
        """Generate actionable recommendations based on data quality analysis"""
        
        recommendations = []
        
        for col_type, analysis in quality_report['column_analysis'].items():
            null_pct = analysis.get('null_percentage', 0)
            
            if null_pct > 20:
                recommendations.append(
                    f"Consider reviewing {col_type} column - {null_pct:.1f}% missing data"
                )
            
            if col_type in ['stock', 'sales'] and analysis.get('zero_values', 0) > 0:
                recommendations.append(
                    f"Review zero values in {col_type} - may indicate data entry issues"
                )
            
            if col_type == 'category' and analysis.get('unique_values', 0) > quality_report['total_rows'] * 0.8:
                recommendations.append(
                    "Too many unique categories - consider grouping similar categories"
                )
        
        quality_report['recommendations'] = recommendations

    def clean_data(self, df: pd.DataFrame, columns_map: Dict[str, str]) -> pd.DataFrame:
        """Enhanced data cleaning with intelligent handling"""
        
        df_clean = df.copy()
        cleaning_log = []
        
        # Clean numeric columns
        numeric_columns = ['stock', 'sales', 'reorder', 'price', 'turnover']
        
        for col_type in numeric_columns:
            if col_type in columns_map and columns_map[col_type] in df_clean.columns:
                col_name = columns_map[col_type]
                original_col = df_clean[col_name].copy()
                
                # Convert to numeric, coercing errors to NaN
                df_clean[col_name] = pd.to_numeric(df_clean[col_name], errors='coerce')
                
                # Handle negative values for stock/sales (shouldn't be negative)
                if col_type in ['stock', 'sales']:
                    negative_count = (df_clean[col_name] < 0).sum()
                    if negative_count > 0:
                        df_clean[col_name] = df_clean[col_name].abs()
                        cleaning_log.append(f"Converted {negative_count} negative values to positive in {col_name}")
                
                # Fill NaN values intelligently
                if df_clean[col_name].isnull().any():
                    null_count = df_clean[col_name].isnull().sum()
                    
                    if col_type == 'stock':
                        # For stock, use median or 0 if all null
                        fill_value = df_clean[col_name].median() if not df_clean[col_name].isna().all() else 0
                    elif col_type == 'sales':
                        # For sales, use mean or 1 (minimal sales)
                        fill_value = df_clean[col_name].mean() if not df_clean[col_name].isna().all() else 1
                    elif col_type == 'reorder':
                        # For reorder, use 20% of average stock
                        stock_col = columns_map.get('stock')
                        if stock_col and stock_col in df_clean.columns:
                            fill_value = df_clean[stock_col].mean() * 0.2
                        else:
                            fill_value = 10  # Default reorder level
                    else:
                        # For price and others, use median
                        fill_value = df_clean[col_name].median() if not df_clean[col_name].isna().all() else 0
                    
                    df_clean[col_name].fillna(fill_value, inplace=True)
                    cleaning_log.append(f"Filled {null_count} null values in {col_name} with {fill_value}")
        
        # Clean text columns
        text_columns = ['name', 'category', 'supplier']
        
        for col_type in text_columns:
            if col_type in columns_map and columns_map[col_type] in df_clean.columns:
                col_name = columns_map[col_type]
                
                # Convert to string and clean
                df_clean[col_name] = df_clean[col_name].astype(str)
                
                # Remove extra whitespace
                df_clean[col_name] = df_clean[col_name].str.strip()
                
                # Replace empty strings and 'nan' with meaningful defaults
                empty_mask = (df_clean[col_name] == '') | (df_clean[col_name] == 'nan') | (df_clean[col_name].isna())
                
                if empty_mask.any():
                    if col_type == 'name':
                        df_clean.loc[empty_mask, col_name] = 'Unknown Product'
                    elif col_type == 'category':
                        df_clean.loc[empty_mask, col_name] = 'Uncategorized'
                    elif col_type == 'supplier':
                        df_clean.loc[empty_mask, col_name] = 'Unknown Supplier'
                    
                    cleaning_log.append(f"Cleaned {empty_mask.sum()} empty values in {col_name}")
        
        # Remove rows with all NaN values in critical columns
        critical_cols = [columns_map.get(col) for col in ['name', 'stock', 'sales'] if columns_map.get(col)]
        critical_cols = [col for col in critical_cols if col and col in df_clean.columns]
        
        if critical_cols:
            initial_rows = len(df_clean)
            df_clean = df_clean.dropna(subset=critical_cols, how='all')
            removed_rows = initial_rows - len(df_clean)
            
            if removed_rows > 0:
                cleaning_log.append(f"Removed {removed_rows} rows with missing critical data")
        
        # Store cleaning log for reporting
        self.cleaning_log = cleaning_log
        
        return df_clean

    def process_csv(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Enhanced main processing function
        Returns: (cleaned_dataframe, columns_mapping, processing_report)
        """
        try:
            # Load CSV with enhanced error handling
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # Try different encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except:
                        continue
                else:
                    raise ValueError("Unable to read CSV file - encoding issues")

            print(f"📊 Dataset loaded successfully! Shape: {df.shape}")
            print(f"🔍 Columns detected: {list(df.columns)}")

            # Detect columns
            columns_map = self.detect_columns(df)
            print(f"🎯 Column mapping: {columns_map}")

            # Validate required columns
            is_valid, missing_cols = self.validate_required_columns(columns_map)
            if not is_valid:
                raise ValueError(f"❌ Missing required columns: {', '.join(missing_cols)}")

            print("✅ All required columns detected!")

            # Analyze data quality
            self.data_quality_report = self.analyze_data_quality(df, columns_map)
            print(f"📈 Data quality analysis completed")

            # Clean data
            df_clean = self.clean_data(df, columns_map)
            print(f"🧹 Data cleaning completed")

            # Final validation
            if len(df_clean) == 0:
                raise ValueError("No valid data remaining after cleaning")

            # Store results
            self.data = df_clean
            self.columns_map = columns_map

            # Print summary
            print(f"✅ Processing completed successfully!")
            print(f"   📊 Final dataset: {df_clean.shape}")
            print(f"   🔧 Columns mapped: {len([v for v in columns_map.values() if v])}")
            print(f"   ⚠️  Data issues: {len(self.data_quality_report.get('data_issues', []))}")

            return df_clean, columns_map

        except FileNotFoundError:
            raise FileNotFoundError(f"❌ CSV file not found: {file_path}")
        except pd.errors.EmptyDataError:
            raise ValueError("❌ CSV file is empty")
        except Exception as e:
            raise Exception(f"❌ Error processing CSV: {str(e)}")

    def get_column_info(self) -> Dict:
        """Return comprehensive information about detected columns and data quality"""
        if not hasattr(self, 'data') or self.data is None:
            return {"error": "No data processed yet"}

        return {
            "detected_columns": self.columns_map,
            "total_columns": len(self.data.columns) if self.data is not None else 0,
            "all_columns": list(self.data.columns) if self.data is not None else [],
            "data_quality": self.data_quality_report,
            "validation_report": getattr(self, 'validation_report', {}),
            "cleaning_log": getattr(self, 'cleaning_log', []),
            "processing_summary": {
                "rows_processed": len(self.data) if self.data is not None else 0,
                "columns_mapped": len([v for v in self.columns_map.values() if v]),
                "data_issues_found": len(self.data_quality_report.get('data_issues', [])),
                "recommendations_count": len(self.data_quality_report.get('recommendations', []))
            }
        }

    def get_sample_data(self, n: int = 5) -> Dict:
        """Get sample data for preview"""
        if not hasattr(self, 'data') or self.data is None:
            return {"error": "No data processed yet"}

        sample = self.data.head(n)
        return {
            "sample_data": sample.to_dict('records'),
            "dtypes": sample.dtypes.to_dict(),
            "shape": sample.shape
        }

    def validate_csv_format(self, file_path: str) -> Dict:
        """Quick validation of CSV format without full processing"""
        try:
            # Read just the header and first few rows
            df_sample = pd.read_csv(file_path, nrows=5)
            
            # Basic validation
            if len(df_sample.columns) < 3:
                return {
                    "valid": False,
                    "error": "CSV must have at least 3 columns",
                    "details": None
                }
            
            if len(df_sample) == 0:
                return {
                    "valid": False,
                    "error": "CSV file is empty",
                    "details": None
                }
            
            # Quick column detection
            columns_map = self.detect_columns(df_sample)
            is_valid, missing_cols = self.validate_required_columns(columns_map)
            
            return {
                "valid": is_valid,
                "error": f"Missing required columns: {', '.join(missing_cols)}" if not is_valid else None,
                "details": {
                    "total_columns": len(df_sample.columns),
                    "detected_columns": columns_map,
                    "sample_columns": list(df_sample.columns),
                    "estimated_rows": len(df_sample)  # This is just the sample size
                }
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to read CSV: {str(e)}",
                "details": None
            }
