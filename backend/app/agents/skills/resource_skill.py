from typing import Any, Dict, List

class ResourceSkill:
    """Encapsulates supply allocation math, inventory safety checks, and resource prioritization."""

    def evaluate_stock_level(self, inventory_data: Dict[str, Any]) -> bool:
        """Determines if a supply item requires reordering based on stock thresholds."""
        return inventory_data.get("reorder_required", False)

    def optimize_supply_dispatch(
        self, available_stock: int, requested_amount: int, priority_level: str
    ) -> int:
        """Caps the allocated items to available stock bounds, adjusting for critical priority."""
        if available_stock <= 0:
            return 0
            
        if priority_level.upper() == "HIGH":
            # Allocate 100% of demand up to stock limit
            return min(available_stock, requested_amount)
        else:
            # Allocate up to 50% of stock for normal request to preserve buffer
            allocated = min(int(available_stock * 0.5), requested_amount)
            return max(allocated, 1) if requested_amount > 0 else 0
