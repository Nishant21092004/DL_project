"""
bml - Balanced Multimodal Learning (OPM / OGM-GE) toolkit.

Quick API:
    from bml import BalancedModulator, LateFusionModel
    from bml.modulation import OPM, OGMGE, discrepancy_ratios, unimodal_scores_from_logits
"""
from .modulation import (BalancedModulator, OGMGE, OPM, discrepancy_ratios, make_z,
                         unimodal_logits_zero_out, unimodal_scores_from_logits)
from .models import (HFTextEncoder, ImageEncoderResNet18, LateFusionModel, SmallCNN, TextTransformerEncoder,
                     build_image_encoder, build_text_encoder)

__version__ = "1.0.0"
__all__ = [
    "BalancedModulator", "OGMGE", "OPM", "discrepancy_ratios", "make_z", "unimodal_logits_zero_out",
    "unimodal_scores_from_logits", "HFTextEncoder", "ImageEncoderResNet18", "LateFusionModel", "SmallCNN",
    "TextTransformerEncoder", "build_image_encoder", "build_text_encoder",
]
