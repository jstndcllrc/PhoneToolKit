"""Finance Lock Guide Data and Service"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class LockType(Enum):
    """Types of finance locks"""
    PAYJOY = "Payjoy"
    SALMON = "Salmon / Home Credit / Billease"
    FRP = "FRP Lock"
    OTHER = "Other"


class Brand(Enum):
    """Phone brands"""
    TRANSION = "Transsion (Tecno/Infinix/Itel)"
    TRANSSION = "Transsion (Tecno/Infinix/Itel)"  # Alias with proper spelling
    HONOR = "Honor"
    XIAOMI = "Xiaomi / Redmi / POCO"
    OPPO = "Oppo / Realme"
    VIVO = "Vivo"
    SAMSUNG = "Samsung"
    OTHER = "Other"


@dataclass
class ToolInfo:
    """Information about a tool/service needed"""
    name: str
    description: str
    url: str = ""
    is_online: bool = False
    cost: str = ""  # "Free", "Paid", "Pricy"


@dataclass
class UnlockMethod:
    """A method to unlock a finance lock"""
    lock_type: LockType
    brand: Brand
    models: str  # e.g., "All models", "Camon 40/40 Pro (CM5/CM6)"
    method: str  # Step-by-step description
    tools: List[ToolInfo] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: str = ""
    is_permanent: bool = True
    difficulty: str = "Medium"  # Easy, Medium, Hard


# Comprehensive Finance Lock Database
FINANCE_GUIDE_DATA: List[UnlockMethod] = [
    # ============ TRANSISION DEVICES ============
    UnlockMethod(
        lock_type=LockType.PAYJOY,
        brand=Brand.TRANSION,
        models="Tecno Camon 40/40 Pro (CM5/CM6), All Transsion models with Payjoy",
        method=(
            "1. Flash old Android 15 version using AMT Tool iFlash\n"
            "2. After flashing, do System Update\n"
            "3. After restart, reset phone via Factory Settings\n"
            "4. This removes the Developer Menu from homescreen"
        ),
        tools=[
            ToolInfo("AMT Tool", "Flashing tool for Transsion devices", is_online=True),
            ToolInfo("iFlash", "Component of AMT for flashing", is_online=True),
        ],
        warnings=[
            "Requires AMT Tool (paid/authorized)",
            "Must flash OLD Android 15 version specifically",
            "Factory reset after update is mandatory"
        ],
        notes="Any Transsion model with Payjoy finance lock follows this method",
        difficulty="Hard"
    ),
    UnlockMethod(
        lock_type=LockType.SALMON,
        brand=Brand.TRANSION,
        models="All Transsion models (Tecno/Infinix/Itel) with Salmon/Home Credit/Billease",
        method="Format via FRP using AMT/UT/TSM Tool - any online tool that supports FRP",
        tools=[
            ToolInfo("AMT Tool", "Transsion flashing/unlock tool", is_online=True),
            ToolInfo("UT Tool", "Universal Tool for FRP", is_online=True),
            ToolInfo("TSM Tool", "Transsion Service Tool", is_online=True),
        ],
        warnings=[
            "Any online FRP-supported tool can work",
            "Tools may require authorization/credits"
        ],
        notes="Not limited to specific tool - any FRP-capable tool works",
        difficulty="Medium"
    ),

    # ============ HONOR DEVICES ============
    UnlockMethod(
        lock_type=LockType.PAYJOY,
        brand=Brand.HONOR,
        models="All Honor models with Payjoy",
        method="AVOID - May cause relock. Not recommended for Payjoy on Honor devices.",
        tools=[],
        warnings=[
            "High risk of relock after unlock attempt",
            "Payjoy on Honor is particularly problematic"
        ],
        notes="Any Honor model with Payjoy finance lock - proceed with extreme caution",
        is_permanent=False,
        difficulty="Hard"
    ),
    UnlockMethod(
        lock_type=LockType.SALMON,
        brand=Brand.HONOR,
        models="All Honor models with Salmon/Home Credit/Billease",
        method="Format via FRP Server using serial registration",
        tools=[
            ToolInfo("GMS Reseller", "FRP server via serial registration", url="https://gmsreseller.com/", is_online=True, cost="Pricy"),
        ],
        warnings=[
            "Requires paid server access (gmsreseller.com)",
            "Serial registration required",
            "Service is expensive"
        ],
        notes="FRP server method via serial registration on gmsreseller.com",
        difficulty="Medium"
    ),

    # ============ XIAOMI / REDMI / POCO ============
    UnlockMethod(
        lock_type=LockType.PAYJOY,
        brand=Brand.XIAOMI,
        models="All Redmi/Xiaomi/POCO models with any finance lock",
        method="Format via FRP Server using FCKTOOL",
        tools=[
            ToolInfo("FCKTOOL", "FRP server tool for Xiaomi", is_online=True),
            ToolInfo("GMS Reseller", "Credits available here", url="https://gmsreseller.com/", is_online=True, cost="Paid"),
        ],
        warnings=[
            "SEMI-PERMANENT ONLY - Finance lock WILL return after reset or system update",
            "Phone will work normally after unlock",
            "DO NOT RESET or do SYSTEM UPDATE - phone will get stuck in recovery",
            "Credits required from gmsreseller.com"
        ],
        notes="Works for Payjoy, Salmon, Home Credit, Billease on all Xiaomi/Redmi/POCO",
        is_permanent=False,
        difficulty="Medium"
    ),
    UnlockMethod(
        lock_type=LockType.SALMON,
        brand=Brand.XIAOMI,
        models="All Redmi/Xiaomi/POCO models",
        method="Same as Payjoy - Format via FRP Server using FCKTOOL",
        tools=[
            ToolInfo("FCKTOOL", "FRP server tool", is_online=True),
            ToolInfo("GMS Reseller", "Credits", url="https://gmsreseller.com/", is_online=True, cost="Paid"),
        ],
        warnings=[
            "SEMI-PERMANENT - lock returns after reset/update",
            "No reset or system update allowed",
            "Paid credits required"
        ],
        is_permanent=False,
        difficulty="Medium"
    ),

    # ============ OPPO & REALME ============
    UnlockMethod(
        lock_type=LockType.PAYJOY,
        brand=Brand.OPPO,
        models="All Oppo & Realme models with Payjoy",
        method="AVOID - May cause relock. Not recommended for Payjoy on Oppo/Realme.",
        tools=[],
        warnings=[
            "High risk of relock",
            "Payjoy on Oppo/Realme is problematic"
        ],
        notes="Any Oppo/Realme model with Payjoy - proceed with extreme caution",
        is_permanent=False,
        difficulty="Hard"
    ),
    UnlockMethod(
        lock_type=LockType.SALMON,
        brand=Brand.OPPO,
        models="All Oppo & Realme models (MTK devices)",
        method="Format via FRP/FRP Server - try UT Tool for MTK devices first (new update)",
        tools=[
            ToolInfo("UT Tool", "New update for MTK Oppo/Realme devices", is_online=True),
            ToolInfo("FRP Server", "Paid server option", is_online=True, cost="Pricy"),
        ],
        warnings=[
            "Realme FRP server is pricey",
            "Try UT Tool for MTK devices first (newer update available)",
            "Server method expensive"
        ],
        notes="New UT Tool update for MTK Oppo/Realme - try this first before paid server",
        difficulty="Medium"
    ),

    # ============ VIVO ============
    UnlockMethod(
        lock_type=LockType.PAYJOY,
        brand=Brand.VIVO,
        models="All Vivo models with Payjoy",
        method="AVOID - May cause relock. Not recommended for Payjoy on Vivo.",
        tools=[],
        warnings=[
            "High risk of relock",
            "Payjoy on Vivo is problematic"
        ],
        notes="Any Vivo model with Payjoy - proceed with extreme caution",
        is_permanent=False,
        difficulty="Hard"
    ),
    UnlockMethod(
        lock_type=LockType.SALMON,
        brand=Brand.VIVO,
        models="All Vivo models with Salmon/Home Credit/Billease",
        method="Format via FRP/FRP Server - try latest TSM Tool update for Vivo models",
        tools=[
            ToolInfo("TSM Tool", "Latest update for Vivo models", is_online=True),
            ToolInfo("GMS Reseller", "Remote service available", url="https://gmsreseller.com/", is_online=True, cost="Pricy"),
        ],
        warnings=[
            "FRP server is pricey",
            "TSM Tool has latest update for Vivo - try this first",
            "Remote service available via gmsreseller.com (expensive)"
        ],
        notes="Latest TSM Tool update for Vivo models available",
        difficulty="Medium"
    ),
]


def get_all_brands() -> List[Brand]:
    """Get all unique brands in the database"""
    brands = set()
    for method in FINANCE_GUIDE_DATA:
        brands.add(method.brand)
    return sorted(brands, key=lambda b: b.value)


def get_all_lock_types() -> List[LockType]:
    """Get all unique lock types in the database"""
    types = set()
    for method in FINANCE_GUIDE_DATA:
        types.add(method.lock_type)
    return sorted(types, key=lambda t: t.value)


def get_methods_by_brand(brand: Brand) -> List[UnlockMethod]:
    """Get all unlock methods for a specific brand"""
    return [m for m in FINANCE_GUIDE_DATA if m.brand == brand]


def get_methods_by_lock_type(lock_type: LockType) -> List[UnlockMethod]:
    """Get all unlock methods for a specific lock type"""
    return [m for m in FINANCE_GUIDE_DATA if m.lock_type == lock_type]


def search_methods(query: str) -> List[UnlockMethod]:
    """Search unlock methods by keyword"""
    query = query.lower()
    results = []
    for method in FINANCE_GUIDE_DATA:
        searchable = (
            method.brand.value.lower() + " " +
            method.lock_type.value.lower() + " " +
            method.models.lower() + " " +
            method.method.lower() + " " +
            method.notes.lower()
        )
        if query in searchable:
            results.append(method)
    return results


def get_method_summary() -> Dict[str, int]:
    """Get summary statistics"""
    return {
        "total_methods": len(FINANCE_GUIDE_DATA),
        "brands": len(get_all_brands()),
        "lock_types": len(get_all_lock_types()),
        "permanent": sum(1 for m in FINANCE_GUIDE_DATA if m.is_permanent),
        "semi_permanent": sum(1 for m in FINANCE_GUIDE_DATA if not m.is_permanent),
    }