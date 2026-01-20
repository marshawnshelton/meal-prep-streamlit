"""
PDF Export for Shopping Lists and Recipe Booklets
Clean, printable format
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
from pathlib import Path


class PDFExporter:
    """Export shopping lists and recipes to PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#10b981'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='StoreHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#059669'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='RecipeTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#10b981'),
            spaceAfter=10
        ))
    
    def export_shopping_list(self, shopping_list: dict, output_path: str, 
                            include_prices: bool = False, cost_data: dict = None) -> str:
        """Export shopping list to PDF"""
        
        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        story = []
        
        # Title
        title = Paragraph("Shopping List", self.styles['CustomTitle'])
        story.append(title)
        
        # Date range and info
        info_text = f"""
        <b>Period:</b> {shopping_list.get('start_date', 'N/A')} to {shopping_list.get('end_date', 'N/A')}<br/>
        <b>For:</b> {shopping_list.get('people', 2)} people<br/>
        <b>Budget:</b> ${shopping_list.get('budget', 400)}<br/>
        """
        
        if include_prices and cost_data:
            info_text += f"""
            <b>Estimated Total:</b> ${cost_data.get('grand_total', 0)}<br/>
            <b>Under Budget:</b> ${cost_data.get('under_budget', 0)}<br/>
            """
        
        info = Paragraph(info_text, self.styles['Normal'])
        story.append(info)
        story.append(Spacer(1, 0.3*inch))
        
        # Shopping list by store
        stores = shopping_list.get('stores', {})
        
        for store_name, store_data in stores.items():
            # Store header
            store_title = store_name.replace('_', ' ').title()
            
            if include_prices and cost_data:
                store_cost_data = cost_data.get('stores', {}).get(store_name, {})
                store_total = store_cost_data.get('total', 0)
                store_title += f" - ${store_total:.2f}"
            
            header = Paragraph(f"📍 {store_title}", self.styles['StoreHeader'])
            story.append(header)
            
            # Items table
            items = store_data.get('items', [])
            
            if include_prices and cost_data:
                # Table with prices
                table_data = [['', 'Item', 'Amount', 'Cost']]
                
                store_cost_items = cost_data.get('stores', {}).get(store_name, {}).get('items_with_costs', [])
                
                for i, item in enumerate(items):
                    cost_info = store_cost_items[i] if i < len(store_cost_items) else {}
                    cost = cost_info.get('cost')
                    cost_str = f"${cost:.2f}" if cost else "N/A"
                    
                    table_data.append([
                        '☐',
                        item.get('item', ''),
                        f"{item.get('amount', '')} {item.get('unit', '')}",
                        cost_str
                    ])
            else:
                # Table without prices
                table_data = [['', 'Item', 'Amount']]
                
                for item in items:
                    table_data.append([
                        '☐',
                        item.get('item', ''),
                        f"{item.get('amount', '')} {item.get('unit', '')}"
                    ])
            
            # Create table
            table = Table(table_data, colWidths=[0.4*inch, 3.5*inch, 1.5*inch, 1*inch] if include_prices else [0.4*inch, 4*inch, 1.5*inch])
            
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def export_recipe_booklet(self, recipes: list, output_path: str) -> str:
        """Export recipe booklet to PDF"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        story = []
        
        # Title page
        title = Paragraph("Recipe Booklet", self.styles['CustomTitle'])
        story.append(title)
        
        subtitle = Paragraph(
            f"<i>{len(recipes)} Recipes for Your Meal Plan</i>",
            self.styles['Normal']
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Table of contents
        toc_title = Paragraph("Recipes Included:", self.styles['Heading2'])
        story.append(toc_title)
        
        for i, recipe in enumerate(recipes, 1):
            toc_item = Paragraph(
                f"{i}. {recipe.get('name', 'Untitled')} - {recipe.get('cuisine', 'N/A')}",
                self.styles['Normal']
            )
            story.append(toc_item)
        
        story.append(PageBreak())
        
        # Individual recipes
        for i, recipe in enumerate(recipes, 1):
            # Recipe title
            recipe_title = Paragraph(
                f"{i}. {recipe.get('name', 'Untitled')}",
                self.styles['RecipeTitle']
            )
            story.append(recipe_title)
            
            # Basic info
            info_text = f"""
            <b>Cuisine:</b> {recipe.get('cuisine', 'N/A')}<br/>
            <b>Servings:</b> {recipe.get('servings', 'N/A')}<br/>
            <b>Prep Time:</b> {recipe.get('prep_time', 'N/A')} minutes<br/>
            <b>Cook Time:</b> {recipe.get('cook_time', 'N/A')} minutes<br/>
            """
            
            info = Paragraph(info_text, self.styles['Normal'])
            story.append(info)
            story.append(Spacer(1, 0.2*inch))
            
            # Ingredients
            ingredients_title = Paragraph("<b>Ingredients:</b>", self.styles['Normal'])
            story.append(ingredients_title)
            
            ingredients = recipe.get('ingredients', [])
            
            if isinstance(ingredients, dict):
                # Handle nested ingredients
                for section, ing_list in ingredients.items():
                    section_title = Paragraph(f"<i>{section.title()}:</i>", self.styles['Normal'])
                    story.append(section_title)
                    
                    for ing in ing_list:
                        if isinstance(ing, dict):
                            ing_text = f"• {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}"
                            if ing.get('prep'):
                                ing_text += f" ({ing.get('prep')})"
                        else:
                            ing_text = f"• {ing}"
                        
                        ing_para = Paragraph(ing_text, self.styles['Normal'])
                        story.append(ing_para)
            else:
                # Simple list
                for ing in ingredients:
                    if isinstance(ing, dict):
                        ing_text = f"• {ing.get('amount', '')} {ing.get('unit', '')} {ing.get('item', '')}"
                        if ing.get('prep'):
                            ing_text += f" ({ing.get('prep')})"
                    else:
                        ing_text = f"• {ing}"
                    
                    ing_para = Paragraph(ing_text, self.styles['Normal'])
                    story.append(ing_para)
            
            story.append(Spacer(1, 0.2*inch))
            
            # Instructions
            instructions_title = Paragraph("<b>Instructions:</b>", self.styles['Normal'])
            story.append(instructions_title)
            
            instructions = recipe.get('instructions', [])
            for j, step in enumerate(instructions, 1):
                step_para = Paragraph(f"{j}. {step}", self.styles['Normal'])
                story.append(step_para)
            
            # Add page break after each recipe except the last
            if i < len(recipes):
                story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        
        return output_path


if __name__ == "__main__":
    # Test PDF export
    exporter = PDFExporter()
    
    # Test shopping list
    test_shopping_list = {
        'start_date': '2026-01-20',
        'end_date': '2026-02-02',
        'people': 2,
        'budget': 400,
        'stores': {
            'costco': {
                'items': [
                    {'item': 'Chicken breast', 'amount': '5', 'unit': 'lbs'},
                    {'item': 'Salmon', 'amount': '2', 'unit': 'lbs'}
                ]
            }
        }
    }
    
    output = exporter.export_shopping_list(
        test_shopping_list,
        'output/test_shopping_list.pdf'
    )
    
    print(f"✓ Test PDF created: {output}")
