"""Patches for VCR compatibility with newer urllib3."""

import logging
from vcr.stubs import VCRHTTPResponse

# Add version_string attribute to VCRHTTPResponse for urllib3 compatibility
def patch_vcr_response():
    """Add missing attributes to VCRHTTPResponse for urllib3 compatibility."""
    if not hasattr(VCRHTTPResponse, 'version_string'):
        VCRHTTPResponse.version_string = "HTTP/1.1"
        logging.info("Added version_string attribute to VCRHTTPResponse")

# Apply the patch
patch_vcr_response()
