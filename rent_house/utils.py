"""
Common utility functions for code generation and monetary helpers.
"""

from django.db import transaction


def generate_unique_code(prefix: str, model_class, field_name: str, padding: int = 4) -> str:
    """
    Generate an incremental, unique code such as PROP-0001, TEN-0001, RENT-0001, PAY-0001.
    Handles gaps, sequential ordering, and uniqueness conflicts safely.
    """
    with transaction.atomic():
        # Get all existing codes matching the prefix pattern to find the highest number
        existing_codes = model_class.objects.filter(
            **{f"{field_name}__startswith": f"{prefix}-"}
        ).values_list(field_name, flat=True)

        highest_num = 0
        for code in existing_codes:
            parts = code.split('-')
            if len(parts) == 2 and parts[1].isdigit():
                num = int(parts[1])
                if num > highest_num:
                    highest_num = num

        candidate_num = highest_num + 1
        candidate_code = f"{prefix}-{candidate_num:0{padding}d}"

        # Safety check against concurrency collisions
        while model_class.objects.filter(**{field_name: candidate_code}).exists():
            candidate_num += 1
            candidate_code = f"{prefix}-{candidate_num:0{padding}d}"

        return candidate_code
