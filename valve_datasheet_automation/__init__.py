"""
VDS-Driven Valve Datasheet Automation System

A production-grade system that generates complete Valve Datasheets
from a single VDS No. input by fetching and mapping data from
PMS, Valve Standards, and configurable decoding rules.

Example:
    >>> from valve_datasheet_automation import DatasheetEngine
    >>> engine = DatasheetEngine()
    >>> datasheet = engine.generate("BSFA1R")
"""

__version__ = "1.0.0"
__author__ = "Valve Automation Team"

from .core.datasheet_engine import DatasheetEngine
from .core.vds_decoder import VDSDecoder
from .models.vds import DecodedVDS
from .models.datasheet import ValveDatasheet

__all__ = [
    "DatasheetEngine",
    "VDSDecoder",
    "DecodedVDS",
    "ValveDatasheet",
]
