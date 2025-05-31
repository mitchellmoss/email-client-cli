"""
Price list reader for Laticrete products.
Parses Excel price list to match products with pricing information.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import re
from difflib import SequenceMatcher
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceListReader:
    """Reads and searches Laticrete price list Excel file."""
    
    def __init__(self, price_list_path: str = "resources/laticrete/lat_price_list.xlsx"):
        """Initialize with path to price list Excel file."""
        self.price_list_path = Path(price_list_path)
        self.price_data = None
        self.load_price_list()
    
    def load_price_list(self):
        """Load price list from Excel file."""
        try:
            if not self.price_list_path.exists():
                raise FileNotFoundError(f"Price list not found at {self.price_list_path}")
            
            # Read Excel file, skip header rows
            self.price_data = pd.read_excel(self.price_list_path, skiprows=4)
            # Filter out rows with no description
            self.price_data = self.price_data[self.price_data['Description'].notna() & 
                                              (self.price_data['Description'] != 'No Data')]
            logger.info(f"Loaded price list with {len(self.price_data)} items")
            logger.debug(f"Columns: {list(self.price_data.columns)}")
            
        except Exception as e:
            logger.error(f"Error loading price list: {e}")
            raise
    
    def find_product(self, product_name: str, sku: Optional[str] = None) -> Optional[Dict]:
        """
        Find product in price list by name or SKU using multiple matching strategies.
        
        Args:
            product_name: Product name to search for
            sku: Optional SKU to search for
            
        Returns:
            Dict with product info or None if not found
        """
        if self.price_data is None:
            logger.error("Price data not loaded")
            return None
        
        try:
            # 1. Try exact SKU match first if provided
            if sku:
                result = self._find_by_exact_sku(sku)
                if result:
                    logger.info(f"Found by exact SKU match: {sku}")
                    return result
                
                # 2. Try partial SKU match (SKU might have extra prefixes/suffixes)
                result = self._find_by_partial_sku(sku)
                if result:
                    logger.info(f"Found by partial SKU match: {sku}")
                    return result
            
            # 3. Try exact product name match
            result = self._find_by_exact_name(product_name)
            if result:
                logger.info(f"Found by exact name match: {product_name}")
                return result
            
            # 4. Try keyword-based search
            result = self._find_by_keywords(product_name)
            if result:
                logger.info(f"Found by keyword match: {product_name}")
                return result
            
            # 5. Try fuzzy matching as last resort
            result = self._find_by_fuzzy_match(product_name)
            if result:
                logger.info(f"Found by fuzzy match: {product_name}")
                return result
            
            logger.warning(f"Product not found after all matching attempts: {product_name} (SKU: {sku})")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for product: {e}")
            return None
    
    def _extract_product_info(self, row) -> Dict:
        """Extract product information from DataFrame row."""
        info = {}
        
        # Map common column names (updated for Laticrete Excel)
        column_mappings = {
            'sku': ['LATICRETE Item No', 'SKU', 'Item #', 'Item Number', 'Product Code', 'Part Number'],
            'name': ['Description', 'Product', 'Product Name', 'Item Description'],
            'price': ['Price', 'List Price', 'Unit Price', 'Cost'],
            'unit': ['Unit', 'UOM', 'Unit of Measure'],
            'category': ['Category', 'Product Category', 'Type'],
            'brand': ['Brand'],
            'size': ['Unit Size'],
            'weight': ['Unit Weight']
        }
        
        for key, possible_cols in column_mappings.items():
            for col in possible_cols:
                if col in row.index and pd.notna(row[col]):
                    info[key] = str(row[col]).strip()
                    break
        
        # Special handling for name: combine Brand and Description if both exist
        if 'Brand' in row.index and 'Description' in row.index:
            brand = str(row['Brand']).strip() if pd.notna(row['Brand']) else ''
            desc = str(row['Description']).strip() if pd.notna(row['Description']) else ''
            if brand and desc:
                info['name'] = f"{brand} {desc}"
            elif brand:
                info['name'] = brand
            elif desc:
                info['name'] = desc
        
        # Include all other columns as additional info
        for col in row.index:
            if col not in [c for cols in column_mappings.values() for c in cols]:
                if pd.notna(row[col]):
                    info[col.lower().replace(' ', '_')] = str(row[col]).strip()
        
        return info
    
    def _find_by_exact_sku(self, sku: str) -> Optional[Dict]:
        """Find product by exact SKU match."""
        clean_sku = sku.replace('#', '').strip()
        
        for col in ['LATICRETE Item No', 'SKU', 'Item #', 'Item Number', 'Product Code', 'Part Number']:
            if col in self.price_data.columns:
                matches = self.price_data[
                    self.price_data[col].astype(str).str.strip() == clean_sku
                ]
                if not matches.empty:
                    return self._extract_product_info(matches.iloc[0])
        return None
    
    def _find_by_partial_sku(self, sku: str) -> Optional[Dict]:
        """Find product by partial SKU match (handle wrong prefixes/suffixes)."""
        clean_sku = sku.replace('#', '').strip()
        
        # Extract core SKU parts (numbers and key identifiers)
        sku_parts = re.findall(r'\d+|[A-Z]+', clean_sku.upper())
        
        if not sku_parts:
            return None
        
        for col in ['LATICRETE Item No', 'SKU']:
            if col in self.price_data.columns:
                for _, row in self.price_data.iterrows():
                    row_sku = str(row[col]).strip().upper()
                    row_parts = re.findall(r'\d+|[A-Z]+', row_sku)
                    
                    # Check if significant parts match
                    matching_parts = sum(1 for part in sku_parts if part in row_parts)
                    if matching_parts >= len(sku_parts) * 0.7:  # 70% match threshold
                        return self._extract_product_info(row)
        return None
    
    def _find_by_exact_name(self, product_name: str) -> Optional[Dict]:
        """Find product by exact name match."""
        # Check individual columns first
        for col in ['Description', 'Product', 'Product Name', 'Brand']:
            if col in self.price_data.columns:
                matches = self.price_data[
                    self.price_data[col].astype(str).str.contains(
                        re.escape(product_name), case=False, na=False
                    )
                ]
                if not matches.empty:
                    return self._extract_product_info(matches.iloc[0])
        
        # Try concatenated Brand + Description search
        if 'Brand' in self.price_data.columns and 'Description' in self.price_data.columns:
            self.price_data['_combined_name'] = (self.price_data['Brand'].fillna('') + ' ' + 
                                                 self.price_data['Description'].fillna('')).str.strip()
            matches = self.price_data[
                self.price_data['_combined_name'].str.contains(
                    re.escape(product_name), case=False, na=False
                )
            ]
            if not matches.empty:
                return self._extract_product_info(matches.iloc[0])
        
        return None
    
    def _find_by_keywords(self, product_name: str) -> Optional[Dict]:
        """Find product by matching key words."""
        # Extract key words from product name
        keywords = self._extract_keywords(product_name)
        
        if not keywords:
            return None
        
        best_match = None
        best_score = 0
        
        # Create combined text for searching
        if 'Brand' in self.price_data.columns and 'Description' in self.price_data.columns:
            self.price_data['_search_text'] = (self.price_data['Brand'].fillna('') + ' ' + 
                                               self.price_data['Description'].fillna('')).str.upper()
        
        search_columns = ['_search_text'] if '_search_text' in self.price_data.columns else ['Description', 'Product', 'Brand']
        
        for col in search_columns:
            if col in self.price_data.columns:
                for _, row in self.price_data.iterrows():
                    row_text = str(row[col]).upper()
                    
                    # Count matching keywords
                    matches = sum(1 for kw in keywords if kw in row_text)
                    score = matches / len(keywords)
                    
                    if score > best_score and score >= 0.6:  # At least 60% keywords match
                        best_score = score
                        best_match = row
        
        if best_match is not None:
            return self._extract_product_info(best_match)
        return None
    
    def _find_by_fuzzy_match(self, product_name: str) -> Optional[Dict]:
        """Find product using fuzzy string matching."""
        best_match = None
        best_score = 0
        
        product_upper = product_name.upper()
        
        # Create combined text for fuzzy matching
        if 'Brand' in self.price_data.columns and 'Description' in self.price_data.columns:
            self.price_data['_fuzzy_text'] = (self.price_data['Brand'].fillna('') + ' ' + 
                                              self.price_data['Description'].fillna('')).str.upper()
        
        search_columns = ['_fuzzy_text'] if '_fuzzy_text' in self.price_data.columns else ['Description', 'Product', 'Brand']
        
        for col in search_columns:
            if col in self.price_data.columns:
                for _, row in self.price_data.iterrows():
                    row_text = str(row[col]).upper()
                    
                    # Calculate similarity score
                    score = SequenceMatcher(None, product_upper, row_text).ratio()
                    
                    if score > best_score and score >= 0.6:  # At least 60% similar
                        best_score = score
                        best_match = row
        
        if best_match is not None:
            logger.debug(f"Fuzzy match score: {best_score:.2f}")
            return self._extract_product_info(best_match)
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from product name."""
        # Remove common words and extract key product identifiers
        stop_words = {'the', 'a', 'an', 'and', 'or', 'with', 'for', 'in', 'on', 'at', 'to', 'of', 
                     'various', 'sizes', 'size', 'laticrete', '-', '(', ')', 'x'}
        
        # Convert to uppercase and split
        words = text.upper().split()
        
        # Extract meaningful keywords
        keywords = []
        for word in words:
            # Remove non-alphanumeric characters
            clean_word = re.sub(r'[^A-Z0-9]', '', word)
            if clean_word and clean_word.lower() not in stop_words and len(clean_word) > 2:
                keywords.append(clean_word)
        
        # Also extract dimensions if present (e.g., "12x12")
        dimensions = re.findall(r'\d+[xX]\d+', text)
        keywords.extend(dimensions)
        
        return keywords
    
    def find_best_match(self, product_name: str, sku: Optional[str] = None, 
                       return_alternatives: bool = False) -> Dict:
        """Find best matching product with confidence score."""
        result = self.find_product(product_name, sku)
        
        if result:
            result['match_confidence'] = 'high'
            return result
        
        # If no match found and return_alternatives is True, 
        # return top 3 closest matches
        if return_alternatives:
            alternatives = self._find_alternatives(product_name)
            return {
                'match_found': False,
                'alternatives': alternatives,
                'original_search': {'name': product_name, 'sku': sku}
            }
        
        return None
    
    def _find_alternatives(self, product_name: str, top_n: int = 3) -> List[Dict]:
        """Find top N alternative products that might match."""
        alternatives = []
        keywords = self._extract_keywords(product_name)
        
        if not keywords:
            return alternatives
        
        scores = []
        
        for col in ['Description', 'Product']:
            if col in self.price_data.columns:
                for idx, row in self.price_data.iterrows():
                    row_text = str(row[col]).upper()
                    
                    # Calculate keyword match score
                    keyword_matches = sum(1 for kw in keywords if kw in row_text)
                    keyword_score = keyword_matches / len(keywords) if keywords else 0
                    
                    # Calculate fuzzy match score
                    fuzzy_score = SequenceMatcher(None, product_name.upper(), row_text).ratio()
                    
                    # Combined score
                    total_score = (keyword_score * 0.7) + (fuzzy_score * 0.3)
                    
                    if total_score > 0.3:  # Minimum threshold
                        scores.append((idx, total_score, row))
        
        # Sort by score and get top N
        scores.sort(key=lambda x: x[1], reverse=True)
        
        for idx, score, row in scores[:top_n]:
            alt = self._extract_product_info(row)
            alt['match_score'] = round(score, 2)
            alternatives.append(alt)
        
        return alternatives
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from price list."""
        if self.price_data is None:
            logger.error("Price data not loaded")
            return []
        
        products = []
        for _, row in self.price_data.iterrows():
            products.append(self._extract_product_info(row))
        
        return products


if __name__ == "__main__":
    # Test the price list reader
    reader = PriceListReader()
    
    # Test searching for a product
    test_products = [
        ("Hydro Ban", None),
        ("254 Platinum", None),
        ("STRATA MAT", None),
        ("HYDRO BAN Preformed Niches (various sizes) - Square 12\" x 12\"", "#9315-0808-S"),
        ("HYDRO BAN PREFORMED NICHE 12X12", None)
    ]
    
    for name, sku in test_products:
        print(f"\nSearching for: {name}")
        result = reader.find_product(name, sku)
        if result:
            print(f"Found: {result}")
        else:
            print("Not found")