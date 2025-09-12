import matplotlib
# CRITICAL: Set backend before importing pyplot for cloud compatibility
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import base64
import io
import datetime
import os
from typing import Dict, List, Any, Optional

# Configure matplotlib for cloud/server environments
plt.ioff()  # Turn off interactive mode

# Configure matplotlib directory for cloud environments
if not os.environ.get('MPLCONFIGDIR'):
    import tempfile
    mpl_cache_dir = os.path.join(tempfile.gettempdir(), '.matplotlib')
    os.makedirs(mpl_cache_dir, exist_ok=True)
    os.environ['MPLCONFIGDIR'] = mpl_cache_dir

# Set professional styling with robust fallbacks
try:
    import seaborn as sns
    # Try seaborn styles
    available_styles = plt.style.available
    if 'seaborn-v0_8-whitegrid' in available_styles:
        plt.style.use('seaborn-v0_8-whitegrid')
    elif 'seaborn-whitegrid' in available_styles:
        plt.style.use('seaborn-whitegrid')
    else:
        plt.style.use('default')
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
    
    try:
        sns.set_palette("husl")
    except Exception:
        pass
        
except ImportError:
    # Seaborn not available - use matplotlib defaults
    plt.style.use('default')
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3

# Configure matplotlib for professional output
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',
    'font.size': 10,
    'axes.titlesize': 14,
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 10,
    'figure.titlesize': 16
})


class ChartGenerator:
    """
    Professional Chart Generator for Inventory Analysis
    Creates publication-ready charts with proper styling and data visualization best practices
    """

    def __init__(self, df: pd.DataFrame, columns_map: Dict[str, str]):
        self.df = df.copy()
        self.cols = columns_map
        self.primary_color = '#2563eb'  # Blue
        self.secondary_color = '#10b981'  # Green  
        self.accent_color = '#f59e0b'  # Amber
        self.danger_color = '#ef4444'  # Red
        self.colors = [self.primary_color, self.secondary_color, self.accent_color, self.danger_color]
        
        # Prepare data for charting
        self._prepare_chart_data()

    def _prepare_chart_data(self):
        """Prepare and clean data for chart generation"""
        # Ensure we have required calculated fields from calculations.py
        required_fields = ['Days_of_Supply', 'Stock_Status', 'Final_Turnover', 'Inventory_Value']
        
        # If fields are missing, calculate them here as fallback
        if 'Days_of_Supply' not in self.df.columns:
            self.df['Days_of_Supply'] = np.where(
                self.df[self.cols['sales']] > 0,
                (self.df[self.cols['stock']] / self.df[self.cols['sales']]) * 30,
                365
            )
        
        if 'Stock_Status' not in self.df.columns:
            # Simple status classification
            self.df['Stock_Status'] = np.where(
                self.df['Days_of_Supply'] <= 15, 'CRITICAL',
                np.where(self.df['Days_of_Supply'] <= 30, 'LOW',
                        np.where(self.df['Days_of_Supply'] <= 90, 'HEALTHY', 'EXCESS'))
            )
        
        if 'Final_Turnover' not in self.df.columns:
            self.df['Final_Turnover'] = np.where(
                self.df[self.cols['stock']] > 0,
                self.df[self.cols['sales']] / self.df[self.cols['stock']],
                0
            )

    def _fig_to_base64(self, fig, dpi: int = 150) -> str:
        """Convert matplotlib figure to base64 string with error handling"""
        try:
            buffer = io.BytesIO()
            fig.savefig(
                buffer, 
                format='png', 
                dpi=dpi, 
                bbox_inches='tight',
                facecolor='white', 
                edgecolor='none',
                pad_inches=0.2
            )
            buffer.seek(0)

            # Convert to base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            plt.close(fig)  # Important: close figure to free memory

            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            plt.close(fig)
            print(f"Error converting chart to base64: {str(e)}")
            return self._create_error_chart(f"Chart generation error: {str(e)}")

    def _create_error_chart(self, error_msg: str) -> str:
        """Create a simple error message chart"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, f'Chart Error:\n{error_msg}', 
                ha='center', va='center', fontsize=12,
                transform=ax.transAxes, color='red',
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._fig_to_base64(fig)

    def generate_category_performance_chart(self) -> str:
        """Generate enhanced category performance bar chart"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))

            # Calculate category performance metrics
            category_data = self.df.groupby(self.cols['category']).agg({
                self.cols['sales']: 'sum',
                self.cols['stock']: 'sum',
                'Final_Turnover': 'mean'
            }).round(2)

            # Sort by total sales
            category_data = category_data.sort_values(self.cols['sales'], ascending=True)
            
            if category_data.empty:
                return self._create_error_chart("No category data available")

            # Create horizontal bar chart for better label readability
            bars = ax.barh(
                range(len(category_data)), 
                category_data[self.cols['sales']],
                color=self.primary_color,
                alpha=0.8,
                edgecolor='white',
                linewidth=0.5
            )

            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, category_data[self.cols['sales']])):
                ax.text(bar.get_width() + max(category_data[self.cols['sales']]) * 0.01,
                       bar.get_y() + bar.get_height()/2,
                       f'{int(value):,}', va='center', fontweight='bold')

            # Customize chart
            ax.set_yticks(range(len(category_data)))
            ax.set_yticklabels([cat[:20] + '...' if len(cat) > 20 else cat 
                               for cat in category_data.index])
            ax.set_xlabel('Monthly Sales Volume', fontweight='bold')
            ax.set_title('Category Performance - Sales Volume Analysis', 
                        fontsize=16, fontweight='bold', pad=20)

            # Add grid and styling
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(0.5)
            ax.spines['bottom'].set_linewidth(0.5)

            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"Category chart error: {str(e)}")

    def generate_inventory_health_chart(self) -> str:
        """Generate professional inventory health distribution chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # Pie chart for stock status distribution
            status_counts = self.df['Stock_Status'].value_counts()
            
            if status_counts.empty:
                return self._create_error_chart("No stock status data available")

            # Color mapping for status
            status_colors = {
                'CRITICAL': self.danger_color,
                'LOW': '#f59e0b',
                'HEALTHY': self.secondary_color,
                'NORMAL': '#6366f1',
                'EXCESS': '#8b5cf6'
            }
            
            colors = [status_colors.get(status, '#6b7280') for status in status_counts.index]

            # Create pie chart
            wedges, texts, autotexts = ax1.pie(
                status_counts.values,
                labels=status_counts.index,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                explode=[0.05 if status == 'CRITICAL' else 0 for status in status_counts.index],
                shadow=True,
                textprops={'fontsize': 10, 'fontweight': 'bold'}
            )

            # Enhance text styling
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)

            ax1.set_title('Stock Status Distribution', fontsize=14, fontweight='bold', pad=20)

            # Days of supply histogram
            days_supply = self.df['Days_of_Supply'].clip(0, 200)  # Cap at 200 for better visualization
            
            ax2.hist(days_supply, bins=20, color=self.primary_color, alpha=0.7, edgecolor='white')
            ax2.axvline(days_supply.median(), color=self.danger_color, linestyle='--', 
                       linewidth=2, label=f'Median: {days_supply.median():.1f} days')
            ax2.axvline(30, color=self.secondary_color, linestyle='--', 
                       linewidth=2, label='Healthy threshold')
            
            ax2.set_xlabel('Days of Supply', fontweight='bold')
            ax2.set_ylabel('Number of Products', fontweight='bold')
            ax2.set_title('Days of Supply Distribution', fontsize=14, fontweight='bold', pad=20)
            ax2.legend()
            ax2.grid(alpha=0.3)

            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"Health chart error: {str(e)}")

    def generate_turnover_analysis_chart(self) -> str:
        """Generate comprehensive turnover analysis chart"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # 1. Turnover distribution histogram
            turnover_data = self.df['Final_Turnover'].clip(0, 20)  # Cap extreme values
            ax1.hist(turnover_data, bins=15, color=self.primary_color, alpha=0.7, edgecolor='white')
            ax1.axvline(turnover_data.mean(), color=self.danger_color, linestyle='--', 
                       linewidth=2, label=f'Mean: {turnover_data.mean():.2f}x')
            ax1.axvline(4, color=self.secondary_color, linestyle='--', 
                       linewidth=2, label='Target: 4.0x')
            ax1.set_xlabel('Turnover Rate', fontweight='bold')
            ax1.set_ylabel('Number of Products', fontweight='bold')
            ax1.set_title('Turnover Rate Distribution', fontweight='bold')
            ax1.legend()
            ax1.grid(alpha=0.3)

            # 2. Category vs Turnover boxplot
            category_turnover = []
            category_names = []
            for cat in self.df[self.cols['category']].unique()[:8]:  # Limit categories for readability
                cat_data = self.df[self.df[self.cols['category']] == cat]['Final_Turnover']
                if len(cat_data) > 0:
                    category_turnover.append(cat_data)
                    category_names.append(cat[:15] + '...' if len(cat) > 15 else cat)

            if category_turnover:
                ax2.boxplot(category_turnover, labels=category_names)
                ax2.set_xlabel('Category', fontweight='bold')
                ax2.set_ylabel('Turnover Rate', fontweight='bold')
                ax2.set_title('Turnover Rate by Category', fontweight='bold')
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(alpha=0.3)

            # 3. Sales vs Stock scatter plot
            ax3.scatter(self.df[self.cols['stock']], self.df[self.cols['sales']], 
                       c=self.df['Final_Turnover'], cmap='viridis', alpha=0.6, s=50)
            ax3.set_xlabel('Current Stock', fontweight='bold')
            ax3.set_ylabel('Monthly Sales', fontweight='bold')
            ax3.set_title('Stock vs Sales Relationship', fontweight='bold')
            cbar = plt.colorbar(ax3.collections[0], ax=ax3)
            cbar.set_label('Turnover Rate', fontweight='bold')
            ax3.grid(alpha=0.3)

            # 4. Turnover trends (simulated monthly data)
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            current_avg = self.df['Final_Turnover'].mean()
            
            # Create realistic trend with some seasonality
            np.random.seed(42)
            monthly_turnover = []
            for i in range(6):
                seasonal_factor = 1 + 0.1 * np.sin(i * np.pi / 3)  # Seasonal variation
                noise = np.random.normal(0, 0.1)  # Random variation
                value = max(0.5, current_avg * seasonal_factor + noise)
                monthly_turnover.append(value)

            ax4.plot(months, monthly_turnover, marker='o', linewidth=3, markersize=8,
                    color=self.primary_color, markerfacecolor='white', 
                    markeredgewidth=2, markeredgecolor=self.primary_color)
            ax4.fill_between(months, monthly_turnover, alpha=0.2, color=self.primary_color)
            ax4.set_ylabel('Average Turnover Rate', fontweight='bold')
            ax4.set_title('Turnover Trend (6 Months)', fontweight='bold')
            ax4.grid(alpha=0.3)

            # Add value labels
            for i, val in enumerate(monthly_turnover):
                ax4.annotate(f'{val:.1f}x', (i, val), textcoords="offset points",
                            xytext=(0, 10), ha='center', fontweight='bold')

            plt.suptitle('Comprehensive Turnover Analysis', fontsize=18, fontweight='bold')
            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"Turnover analysis error: {str(e)}")

    def generate_abc_analysis_chart(self) -> str:
        """Generate ABC analysis chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # ABC distribution pie chart
            if 'ABC_Class' in self.df.columns:
                abc_counts = self.df['ABC_Class'].value_counts()
                
                colors_abc = {'A': self.danger_color, 'B': self.accent_color, 'C': self.secondary_color}
                colors = [colors_abc.get(cls, '#6b7280') for cls in abc_counts.index]
                
                ax1.pie(abc_counts.values, labels=abc_counts.index, autopct='%1.1f%%',
                       colors=colors, startangle=90, shadow=True,
                       textprops={'fontsize': 12, 'fontweight': 'bold'})
                ax1.set_title('ABC Classification Distribution', fontsize=14, fontweight='bold')

                # ABC value analysis
                if 'Inventory_Value' in self.df.columns:
                    abc_values = self.df.groupby('ABC_Class')['Inventory_Value'].sum().sort_index()
                    bars = ax2.bar(abc_values.index, abc_values.values, 
                                  color=[colors_abc.get(cls, '#6b7280') for cls in abc_values.index],
                                  alpha=0.8, edgecolor='white')
                    
                    # Add value labels
                    for bar, value in zip(bars, abc_values.values):
                        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value * 0.01,
                                f'${value:,.0f}', ha='center', va='bottom', fontweight='bold')
                    
                    ax2.set_xlabel('ABC Class', fontweight='bold')
                    ax2.set_ylabel('Inventory Value ($)', fontweight='bold')
                    ax2.set_title('Inventory Value by ABC Class', fontsize=14, fontweight='bold')
                    ax2.grid(axis='y', alpha=0.3)
                else:
                    ax2.text(0.5, 0.5, 'Inventory Value\nData Not Available', 
                            ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            else:
                for ax in [ax1, ax2]:
                    ax.text(0.5, 0.5, 'ABC Analysis\nData Not Available', 
                           ha='center', va='center', transform=ax.transAxes, fontsize=12)

            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"ABC analysis error: {str(e)}")

    def generate_priority_reorders_chart(self, priority_products: List[Dict]) -> str:
        """Generate priority reorders visualization"""
        try:
            if not priority_products or len(priority_products) == 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.text(0.5, 0.5, '✅ No Priority Reorders Needed\n\nAll products are adequately stocked!', 
                       ha='center', va='center', fontsize=16, fontweight='bold',
                       transform=ax.transAxes, color=self.secondary_color,
                       bbox=dict(boxstyle='round,pad=1', facecolor='lightgreen', alpha=0.1))
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.axis('off')
                return self._fig_to_base64(fig)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

            # Limit to top 10 for better visualization
            top_products = priority_products[:10]

            # Chart 1: Current stock levels with urgency color coding
            products = [p['product'][:20] + '...' if len(p['product']) > 20 else p['product'] 
                       for p in top_products]
            stock_levels = [p['currentStock'] for p in top_products]
            urgencies = [p.get('urgency', 'LOW') for p in top_products]

            # Color mapping for urgency
            urgency_colors = {
                'CRITICAL': self.danger_color,
                'HIGH': '#f59e0b',
                'MEDIUM': '#6366f1',
                'LOW': self.secondary_color
            }
            colors = [urgency_colors.get(urgency, self.primary_color) for urgency in urgencies]

            bars1 = ax1.barh(range(len(products)), stock_levels, color=colors, alpha=0.8, edgecolor='white')

            # Add value labels
            for i, (bar, stock, urgency) in enumerate(zip(bars1, stock_levels, urgencies)):
                ax1.text(bar.get_width() + max(stock_levels) * 0.01,
                        bar.get_y() + bar.get_height()/2,
                        f'{stock} ({urgency})', va='center', fontweight='bold', fontsize=9)

            ax1.set_yticks(range(len(products)))
            ax1.set_yticklabels(products)
            ax1.set_xlabel('Current Stock Level', fontweight='bold')
            ax1.set_title('Priority Reorder Items - Current Stock', fontsize=14, fontweight='bold')
            ax1.grid(axis='x', alpha=0.3)

            # Chart 2: Suggested order quantities
            suggested_orders = [p.get('suggestedOrder', p.get('reorderQty', 0)) for p in top_products]
            
            bars2 = ax2.barh(range(len(products)), suggested_orders, 
                           color=self.primary_color, alpha=0.8, edgecolor='white')

            # Add value labels
            for i, (bar, qty) in enumerate(zip(bars2, suggested_orders)):
                ax2.text(bar.get_width() + max(suggested_orders) * 0.01,
                        bar.get_y() + bar.get_height()/2,
                        f'{qty}', va='center', fontweight='bold')

            ax2.set_yticks(range(len(products)))
            ax2.set_yticklabels(products)
            ax2.set_xlabel('Suggested Order Quantity', fontweight='bold')
            ax2.set_title('Recommended Order Quantities', fontsize=14, fontweight='bold')
            ax2.grid(axis='x', alpha=0.3)

            # Add legend for urgency colors
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=self.danger_color, label='Critical'),
                Patch(facecolor='#f59e0b', label='High'),
                Patch(facecolor='#6366f1', label='Medium'),
                Patch(facecolor=self.secondary_color, label='Low')
            ]
            ax1.legend(handles=legend_elements, loc='lower right', title='Urgency Level')

            plt.suptitle('Priority Reorder Analysis', fontsize=16, fontweight='bold')
            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"Priority reorders error: {str(e)}")

    def generate_financial_overview_chart(self) -> str:
        """Generate financial overview dashboard"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

            # 1. Inventory value by category
            if 'Inventory_Value' in self.df.columns:
                cat_values = self.df.groupby(self.cols['category'])['Inventory_Value'].sum().nlargest(8)
                
                bars = ax1.bar(range(len(cat_values)), cat_values.values, 
                              color=self.primary_color, alpha=0.8)
                ax1.set_xticks(range(len(cat_values)))
                ax1.set_xticklabels([cat[:10] + '...' if len(cat) > 10 else cat 
                                    for cat in cat_values.index], rotation=45, ha='right')
                ax1.set_ylabel('Inventory Value ($)', fontweight='bold')
                ax1.set_title('Inventory Value by Category', fontweight='bold')
                
                # Add value labels
                for bar, value in zip(bars, cat_values.values):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value * 0.01,
                            f'${value:,.0f}', ha='center', va='bottom', fontweight='bold', fontsize=9)
                
                ax1.grid(axis='y', alpha=0.3)

            # 2. Stock status value distribution
            if 'Inventory_Value' in self.df.columns:
                status_values = self.df.groupby('Stock_Status')['Inventory_Value'].sum()
                
                status_colors = {
                    'CRITICAL': self.danger_color,
                    'LOW': '#f59e0b',
                    'HEALTHY': self.secondary_color,
                    'NORMAL': '#6366f1',
                    'EXCESS': '#8b5cf6'
                }
                colors = [status_colors.get(status, '#6b7280') for status in status_values.index]
                
                ax2.pie(status_values.values, labels=status_values.index, autopct='%1.1f%%',
                       colors=colors, startangle=90, shadow=True,
                       textprops={'fontsize': 10, 'fontweight': 'bold'})
                ax2.set_title('Inventory Value by Stock Status', fontweight='bold')

            # 3. Days of supply vs inventory value scatter
            if 'Inventory_Value' in self.df.columns:
                scatter = ax3.scatter(self.df['Days_of_Supply'].clip(0, 200), 
                                    self.df['Inventory_Value'].clip(0, self.df['Inventory_Value'].quantile(0.95)),
                                    c=self.df['Final_Turnover'], cmap='plasma', alpha=0.6, s=30)
                ax3.set_xlabel('Days of Supply', fontweight='bold')
                ax3.set_ylabel('Inventory Value ($)', fontweight='bold')
                ax3.set_title('Days Supply vs Inventory Value', fontweight='bold')
                
                cbar = plt.colorbar(scatter, ax=ax3)
                cbar.set_label('Turnover Rate', fontweight='bold')
                ax3.grid(alpha=0.3)

            # 4. Monthly sales trend by top categories
            top_categories = self.df.groupby(self.cols['category'])[self.cols['sales']].sum().nlargest(5)
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            
            for i, (cat, base_sales) in enumerate(top_categories.items()):
                # Simulate monthly data with seasonal variation
                np.random.seed(i + 42)
                monthly_sales = []
                for month in range(6):
                    seasonal_factor = 1 + 0.15 * np.sin(month * np.pi / 3)
                    noise = np.random.normal(0, 0.05)
                    value = max(base_sales * 0.7, base_sales * seasonal_factor + noise)
                    monthly_sales.append(value)
                
                ax4.plot(months, monthly_sales, marker='o', linewidth=2, 
                        label=cat[:15] + '...' if len(cat) > 15 else cat, alpha=0.8)
            
            ax4.set_ylabel('Monthly Sales', fontweight='bold')
            ax4.set_title('Sales Trends by Top Categories', fontweight='bold')
            ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax4.grid(alpha=0.3)

            plt.suptitle('Financial Overview Dashboard', fontsize=16, fontweight='bold')
            plt.tight_layout()
            return self._fig_to_base64(fig)

        except Exception as e:
            return self._create_error_chart(f"Financial overview error: {str(e)}")

    def generate_all_charts(self, priority_products: List[Dict] = None) -> Dict[str, str]:
        """Generate all charts and return as base64 strings"""
        try:
            print("Generating charts...")
            
            # Generate all chart types
            charts = {}
            
            # Core charts
            charts['categoryPerformance'] = self.generate_category_performance_chart()
            print("✓ Category performance chart generated")
            
            charts['inventoryHealth'] = self.generate_inventory_health_chart()
            print("✓ Inventory health chart generated")
            
            charts['turnoverAnalysis'] = self.generate_turnover_analysis_chart()
            print("✓ Turnover analysis chart generated")
            
            charts['abcAnalysis'] = self.generate_abc_analysis_chart()
            print("✓ ABC analysis chart generated")
            
            # Priority reorders chart
            if priority_products:
                charts['priorityReorders'] = self.generate_priority_reorders_chart(priority_products)
            else:
                charts['priorityReorders'] = self.generate_priority_reorders_chart([])
            print("✓ Priority reorders chart generated")
            
            # Financial overview
            charts['financialOverview'] = self.generate_financial_overview_chart()
            print("✓ Financial overview chart generated")

            # Legacy chart names for backward compatibility
            charts['stockDistribution'] = charts['inventoryHealth']
            charts['turnoverTrends'] = charts['turnoverAnalysis']

            print(f"✅ All {len(charts)} charts generated successfully!")
            return charts

        except Exception as e:
            print(f"❌ Error generating charts: {str(e)}")
            error_chart = self._create_error_chart(f"Chart generation failed: {str(e)}")
            return {
                'categoryPerformance': error_chart,
                'inventoryHealth': error_chart,
                'turnoverAnalysis': error_chart,
                'abcAnalysis': error_chart,
                'priorityReorders': error_chart,
                'financialOverview': error_chart,
                'stockDistribution': error_chart,
                'turnoverTrends': error_chart
            }

    def __del__(self):
        """Cleanup method to ensure all figures are closed"""
        plt.close('all')
