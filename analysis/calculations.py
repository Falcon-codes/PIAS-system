import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')


class InventoryCalculations:
    """
    Professional Inventory Calculations Engine
    Handles all inventory KPIs, analytics, and business intelligence metrics
    """

    def __init__(self, df: pd.DataFrame, columns_map: Dict[str, str]):
        self.df = df.copy()
        self.cols = columns_map
        self.safety_stock_multiplier = 1.5
        self.optimal_turnover_target = 4.0
        self._prepare_data()
        self._validate_data()

    def _validate_data(self):
        """Validate input data and columns"""
        required_cols = ['stock', 'sales', 'name', 'category']
        missing_cols = [col for col in required_cols if not self.cols.get(col)]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Ensure numeric columns are properly typed
        numeric_cols = ['stock', 'sales', 'reorder']
        for col in numeric_cols:
            if self.cols.get(col) and self.cols[col] in self.df.columns:
                self.df[self.cols[col]] = pd.to_numeric(self.df[self.cols[col]], errors='coerce')
                
        # Fill NaN values with appropriate defaults
        self.df.fillna({
            self.cols.get('stock', 'stock'): 0,
            self.cols.get('sales', 'sales'): 0,
            self.cols.get('reorder', 'reorder_level'): 0
        }, inplace=True)

    def _prepare_data(self):
        """Prepare data with calculated fields and professional metrics"""
        
        # Calculate annual sales (assuming sales data is monthly)
        self.df['Annual_Sales'] = self.df[self.cols['sales']] * 12
        
        # Calculate Cost of Goods Sold (COGS) - estimate if price not available
        if self.cols.get('price') and self.cols['price'] in self.df.columns:
            self.df[self.cols['price']] = pd.to_numeric(self.df[self.cols['price']], errors='coerce')
            self.df['COGS'] = self.df['Annual_Sales'] * self.df[self.cols['price']]
        else:
            # Estimate COGS based on sales volume (industry standard estimation)
            self.df['COGS'] = self.df['Annual_Sales'] * 25  # $25 average unit cost estimation
        
        # Calculate Inventory Turnover Ratio (Professional Formula)
        self.df['Inventory_Turnover'] = np.where(
            self.df[self.cols['stock']] > 0,
            self.df['COGS'] / (self.df[self.cols['stock']] * self.df.get('COGS', 25) / self.df['Annual_Sales']),
            0
        )
        
        # Alternative turnover calculation for validation
        self.df['Simple_Turnover'] = np.where(
            self.df[self.cols['stock']] > 0,
            self.df['Annual_Sales'] / self.df[self.cols['stock']],
            0
        )
        
        # Use the more conservative turnover calculation
        self.df['Final_Turnover'] = np.minimum(self.df['Inventory_Turnover'], self.df['Simple_Turnover'])
        self.cols['turnover'] = 'Final_Turnover'
        
        # Calculate Days of Supply (Professional Formula)
        self.df['Days_of_Supply'] = np.where(
            self.df[self.cols['sales']] > 0,
            (self.df[self.cols['stock']] / self.df[self.cols['sales']]) * 30,  # Monthly to days
            365  # High days if no sales
        )
        
        # Calculate Safety Stock Requirements
        monthly_sales = self.df[self.cols['sales']]
        self.df['Safety_Stock'] = monthly_sales * self.safety_stock_multiplier
        
        # Calculate Optimal Reorder Point (Professional Formula)
        # Reorder Point = (Average Daily Usage × Lead Time) + Safety Stock
        daily_usage = monthly_sales / 30
        lead_time_days = 14  # Assume 2 weeks lead time
        self.df['Optimal_Reorder_Point'] = (daily_usage * lead_time_days) + self.df['Safety_Stock']
        
        # Calculate Economic Order Quantity (EOQ) estimation
        annual_demand = self.df['Annual_Sales']
        ordering_cost = 50  # Estimated ordering cost per order
        holding_cost_rate = 0.25  # 25% annual holding cost rate
        
        unit_cost = np.where(
            self.cols.get('price') and self.cols['price'] in self.df.columns,
            self.df[self.cols['price']],
            25  # Default unit cost
        )
        
        holding_cost = unit_cost * holding_cost_rate
        
        self.df['EOQ'] = np.sqrt(
            (2 * annual_demand * ordering_cost) / np.maximum(holding_cost, 1)
        )
        
        # Calculate Inventory Value
        self.df['Inventory_Value'] = self.df[self.cols['stock']] * unit_cost
        
        # Calculate ABC Analysis (Pareto Analysis)
        self.df = self._calculate_abc_analysis()
        
        # Stock Status Classification (Professional)
        self._classify_stock_status()

    def _calculate_abc_analysis(self) -> pd.DataFrame:
        """Calculate ABC analysis based on inventory value and turnover"""
        df_sorted = self.df.copy()
        df_sorted['Revenue_Impact'] = df_sorted['Annual_Sales'] * df_sorted.get('COGS', 25) / df_sorted['Annual_Sales']
        df_sorted = df_sorted.sort_values('Revenue_Impact', ascending=False)
        
        cumulative_value = df_sorted['Revenue_Impact'].cumsum()
        total_value = df_sorted['Revenue_Impact'].sum()
        cumulative_percent = (cumulative_value / total_value) * 100
        
        # ABC Classification
        conditions = [
            cumulative_percent <= 70,
            cumulative_percent <= 90,
            cumulative_percent <= 100
        ]
        choices = ['A', 'B', 'C']
        
        df_sorted['ABC_Class'] = np.select(conditions, choices, default='C')
        
        # Merge back to original dataframe
        self.df = self.df.merge(
            df_sorted[['ABC_Class']], 
            left_index=True, 
            right_index=True, 
            how='left'
        )
        
        return self.df

    def _classify_stock_status(self):
        """Professional stock status classification"""
        # Get reorder levels
        if self.cols.get('reorder') and self.cols['reorder'] in self.df.columns:
            reorder_level = self.df[self.cols['reorder']]
        else:
            reorder_level = self.df['Optimal_Reorder_Point']
        
        current_stock = self.df[self.cols['stock']]
        days_supply = self.df['Days_of_Supply']
        
        # Professional status classification
        conditions = [
            (current_stock <= reorder_level * 0.5) | (days_supply <= 7),    # Critical
            (current_stock <= reorder_level) | (days_supply <= 15),         # Low
            (current_stock <= reorder_level * 2) & (days_supply <= 45),     # Normal
            (current_stock <= reorder_level * 3) & (days_supply <= 90),     # Healthy
        ]
        
        choices = ['CRITICAL', 'LOW', 'NORMAL', 'HEALTHY']
        
        self.df['Stock_Status'] = np.select(conditions, choices, default='EXCESS')
        
        # Calculate Priority Score (for reordering)
        self.df['Priority_Score'] = (
            (100 - self.df['Days_of_Supply']) * 0.4 +  # Days supply weight
            self.df[self.cols['sales']] * 0.3 +         # Sales volume weight
            (self.df['ABC_Class'] == 'A').astype(int) * 20 +  # A-class items priority
            (self.df['Stock_Status'] == 'CRITICAL').astype(int) * 30  # Critical status boost
        )

    def calculate_kpis(self) -> Dict[str, Any]:
        """Calculate comprehensive KPI metrics for executive dashboard"""
        
        # Basic counts
        total_products = len(self.df)
        
        # Stock status counts
        critical_count = len(self.df[self.df['Stock_Status'] == 'CRITICAL'])
        low_count = len(self.df[self.df['Stock_Status'] == 'LOW'])
        healthy_count = len(self.df[self.df['Stock_Status'] == 'HEALTHY'])
        excess_count = len(self.df[self.df['Stock_Status'] == 'EXCESS'])
        
        # Financial metrics
        total_inventory_value = self.df['Inventory_Value'].sum()
        total_annual_sales = self.df['Annual_Sales'].sum()
        
        # Turnover analysis
        avg_turnover = self.df['Final_Turnover'].mean()
        weighted_turnover = (
            self.df['Final_Turnover'] * self.df['Inventory_Value']
        ).sum() / total_inventory_value if total_inventory_value > 0 else 0
        
        # Inventory health percentage (professional calculation)
        healthy_percentage = (healthy_count + len(self.df[self.df['Stock_Status'] == 'NORMAL'])) / total_products * 100
        
        # Days of supply analysis
        avg_days_supply = self.df['Days_of_Supply'].median()
        
        # ABC Analysis summary
        abc_breakdown = self.df.groupby('ABC_Class').agg({
            'Inventory_Value': 'sum',
            self.cols['name']: 'count'
        }).to_dict()
        
        # Service level calculation (ability to fulfill orders)
        service_level = (total_products - critical_count) / total_products * 100 if total_products > 0 else 0
        
        # Obsolete inventory (>180 days supply)
        obsolete_inventory = len(self.df[self.df['Days_of_Supply'] > 180])
        obsolete_value = self.df[self.df['Days_of_Supply'] > 180]['Inventory_Value'].sum()
        
        return {
            # Core KPIs
            'totalProducts': int(total_products),
            'criticalAlerts': int(critical_count),
            'averageTurnover': round(float(avg_turnover), 2),
            'inventoryHealth': round(float(healthy_percentage), 1),
            
            # Financial KPIs
            'totalInventoryValue': round(float(total_inventory_value), 2),
            'totalAnnualSales': round(float(total_annual_sales), 2),
            'inventoryROI': round(float(total_annual_sales / total_inventory_value * 100) if total_inventory_value > 0 else 0, 1),
            
            # Operational KPIs
            'weightedTurnover': round(float(weighted_turnover), 2),
            'avgDaysSupply': round(float(avg_days_supply), 1),
            'serviceLevel': round(float(service_level), 1),
            
            # Stock distribution
            'emergencyStock': int(critical_count),
            'lowStock': int(low_count),
            'healthyStock': int(healthy_count),
            'excessStock': int(excess_count),
            
            # Risk metrics
            'obsoleteItems': int(obsolete_inventory),
            'obsoleteValue': round(float(obsolete_value), 2),
            'stockoutRisk': round(float(critical_count / total_products * 100) if total_products > 0 else 0, 1),
            
            # ABC Analysis
            'abcBreakdown': abc_breakdown
        }

    def get_priority_reorders(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get intelligently prioritized reorder recommendations"""
        
        # Filter items that need reordering
        reorder_candidates = self.df[
            (self.df['Stock_Status'].isin(['CRITICAL', 'LOW'])) |
            (self.df['Days_of_Supply'] <= 30)
        ].copy()
        
        if reorder_candidates.empty:
            return []
        
        # Sort by priority score (highest first)
        priority_reorders = reorder_candidates.nlargest(limit, 'Priority_Score')
        
        reorder_list = []
        for _, product in priority_reorders.iterrows():
            
            # Calculate suggested order quantity (EOQ or minimum reorder)
            suggested_qty = max(
                int(product['EOQ']),
                int(product['Optimal_Reorder_Point'] - product[self.cols['stock']]),
                int(product[self.cols['sales']] * 2)  # At least 2 months supply
            )
            
            # Calculate urgency score
            urgency = 'CRITICAL' if product['Days_of_Supply'] <= 7 else \
                     'HIGH' if product['Days_of_Supply'] <= 15 else \
                     'MEDIUM' if product['Days_of_Supply'] <= 30 else 'LOW'
            
            # Estimate cost impact
            cost_impact = suggested_qty * product.get('COGS', 25) / product.get('Annual_Sales', 1)
            
            reorder_list.append({
                'product': str(product[self.cols['name']]),
                'category': str(product[self.cols['category']]),
                'currentStock': int(product[self.cols['stock']]),
                'reorderPoint': int(product['Optimal_Reorder_Point']),
                'suggestedOrder': int(suggested_qty),
                'daysOfSupply': round(float(product['Days_of_Supply']), 1),
                'urgency': urgency,
                'priority_score': round(float(product['Priority_Score']), 1),
                'monthlySales': int(product[self.cols['sales']]),
                'turnoverRate': round(float(product['Final_Turnover']), 2),
                'abcClass': str(product.get('ABC_Class', 'C')),
                'estimatedCost': round(float(cost_impact), 2),
                'status': str(product['Stock_Status'])
            })
        
        return reorder_list

    def get_category_performance(self) -> Dict[str, Dict[str, float]]:
        """Enhanced category performance analysis"""
        
        category_metrics = self.df.groupby(self.cols['category']).agg({
            self.cols['sales']: ['sum', 'mean', 'count'],
            'Final_Turnover': 'mean',
            'Inventory_Value': 'sum',
            'Days_of_Supply': 'median',
            self.cols['stock']: 'sum'
        }).round(2)
        
        # Flatten column names
        category_metrics.columns = ['_'.join(col).strip() for col in category_metrics.columns]
        
        # Convert to nested dictionary
        result = {}
        for category in category_metrics.index:
            metrics = category_metrics.loc[category]
            result[category] = {
                'totalSales': float(metrics[f'{self.cols["sales"]}_sum']),
                'avgSales': float(metrics[f'{self.cols["sales"]}_mean']),
                'productCount': int(metrics[f'{self.cols["sales"]}_count']),
                'avgTurnover': float(metrics['Final_Turnover_mean']),
                'inventoryValue': float(metrics['Inventory_Value_sum']),
                'avgDaysSupply': float(metrics['Days_of_Supply_median']),
                'totalStock': int(metrics[f'{self.cols["stock"]}_sum'])
            }
            
        # Sort by total sales descending
        result = dict(sorted(result.items(), key=lambda x: x[1]['totalSales'], reverse=True))
        
        return result

    def get_fast_slow_movers(self) -> Dict[str, List[Dict]]:
        """Enhanced fast/slow movers analysis with professional metrics"""
        
        # Calculate percentiles for turnover
        turnover_75th = self.df['Final_Turnover'].quantile(0.75)
        turnover_25th = self.df['Final_Turnover'].quantile(0.25)
        
        # Fast movers: top 25% turnover
        fast_movers = self.df[self.df['Final_Turnover'] >= turnover_75th].copy()
        
        # Slow movers: bottom 25% turnover
        slow_movers = self.df[self.df['Final_Turnover'] <= turnover_25th].copy()
        
        def format_movers(df, limit=10):
            df_sorted = df.nlargest(limit, 'Priority_Score') if not df.empty else df
            return [
                {
                    'name': str(row[self.cols['name']]),
                    'category': str(row[self.cols['category']]),
                    'turnover': round(float(row['Final_Turnover']), 2),
                    'stock': int(row[self.cols['stock']]),
                    'monthlySales': int(row[self.cols['sales']]),
                    'daysSupply': round(float(row['Days_of_Supply']), 1),
                    'inventoryValue': round(float(row['Inventory_Value']), 2),
                    'abcClass': str(row.get('ABC_Class', 'C')),
                    'status': str(row['Stock_Status']),
                    'priorityScore': round(float(row['Priority_Score']), 1)
                }
                for _, row in df_sorted.iterrows()
            ]
        
        return {
            'fastMovers': format_movers(fast_movers.nlargest(10, 'Final_Turnover')),
            'slowMovers': format_movers(slow_movers.nsmallest(10, 'Final_Turnover')),
            'fastMoversCount': len(fast_movers),
            'slowMoversCount': len(slow_movers),
            'turnoverThresholds': {
                'fastMover': round(float(turnover_75th), 2),
                'slowMover': round(float(turnover_25th), 2)
            }
        }

    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get comprehensive filter options"""
        
        categories = sorted(self.df[self.cols['category']].unique().tolist())
        statuses = sorted(self.df['Stock_Status'].unique().tolist())
        abc_classes = sorted(self.df['ABC_Class'].unique().tolist())
        
        return {
            'categories': ['All Categories'] + [str(cat) for cat in categories],
            'statuses': ['All'] + [str(status) for status in statuses],
            'abcClasses': ['All'] + [str(abc) for abc in abc_classes],
            'turnoverRanges': ['All', 'High (>6x)', 'Medium (2-6x)', 'Low (<2x)'],
            'daysSupplyRanges': ['All', 'Critical (<15)', 'Low (15-30)', 'Normal (30-90)', 'Excess (>90)']
        }

    def filter_products(self, category: str = None, status: str = None, 
                       search: str = None, abc_class: str = None) -> List[Dict]:
        """Enhanced product filtering with multiple criteria"""
        
        filtered_df = self.df.copy()
        
        # Apply filters
        if category and category not in ['All Categories', 'All']:
            filtered_df = filtered_df[filtered_df[self.cols['category']] == category]
            
        if status and status not in ['All']:
            if status in filtered_df['Stock_Status'].values:
                filtered_df = filtered_df[filtered_df['Stock_Status'] == status]
            else:
                # Handle legacy status mapping
                status_mapping = {
                    'Critical': 'CRITICAL',
                    'Low Stock': 'LOW',
                    'Healthy': 'HEALTHY',
                    'Excess': 'EXCESS'
                }
                mapped_status = status_mapping.get(status)
                if mapped_status:
                    filtered_df = filtered_df[filtered_df['Stock_Status'] == mapped_status]
                    
        if abc_class and abc_class not in ['All']:
            filtered_df = filtered_df[filtered_df['ABC_Class'] == abc_class]
            
        if search and search.strip():
            search_mask = filtered_df[self.cols['name']].str.contains(
                search.strip(), case=False, na=False
            )
            filtered_df = filtered_df[search_mask]
        
        # Format results with comprehensive data
        results = []
        for _, row in filtered_df.iterrows():
            results.append({
                'name': str(row[self.cols['name']]),
                'category': str(row[self.cols['category']]),
                'currentStock': int(row[self.cols['stock']]),
                'monthlySales': int(row[self.cols['sales']]),
                'turnover': round(float(row['Final_Turnover']), 2),
                'daysOfSupply': round(float(row['Days_of_Supply']), 1),
                'status': str(row['Stock_Status']),
                'abcClass': str(row.get('ABC_Class', 'C')),
                'inventoryValue': round(float(row['Inventory_Value']), 2),
                'reorderPoint': int(row['Optimal_Reorder_Point']),
                'suggestedOrder': int(row.get('EOQ', 0)),
                'priorityScore': round(float(row['Priority_Score']), 1)
            })
            
        # Sort by priority score
        results.sort(key=lambda x: x['priorityScore'], reverse=True)
        
        return results

    def get_inventory_insights(self) -> Dict[str, Any]:
        """Generate actionable business insights"""
        
        insights = {
            'alerts': [],
            'recommendations': [],
            'opportunities': [],
            'risks': []
        }
        
        # Critical alerts
        critical_items = len(self.df[self.df['Stock_Status'] == 'CRITICAL'])
        if critical_items > 0:
            insights['alerts'].append(f"{critical_items} items are critically low on stock")
            
        # Excess inventory
        excess_value = self.df[self.df['Stock_Status'] == 'EXCESS']['Inventory_Value'].sum()
        if excess_value > 10000:
            insights['alerts'].append(f"${excess_value:,.0f} tied up in excess inventory")
            
        # Slow movers
        slow_movers = len(self.df[self.df['Final_Turnover'] < 1])
        if slow_movers > 0:
            insights['recommendations'].append(f"Review {slow_movers} slow-moving items for promotion or discontinuation")
            
        # ABC optimization
        a_class_low = len(self.df[(self.df['ABC_Class'] == 'A') & (self.df['Stock_Status'].isin(['CRITICAL', 'LOW']))])
        if a_class_low > 0:
            insights['risks'].append(f"{a_class_low} high-value A-class items are understocked")
            
        return insights
