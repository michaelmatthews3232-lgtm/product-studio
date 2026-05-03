"""
Cozy/rustic scene templates for soap product photography.

Each template is a hand-tuned prompt that, when combined with a buyer's
reference image via Flux Kontext, produces a styled scene with their
actual product preserved.

PROMPT STRUCTURE (keep consistent across templates):
1. Anchor on preservation: "professional product photograph of this exact bar of soap..."
2. Surface description (specific material + texture)
3. Props (2-3 items, no more — over-styling confuses the model)
4. Lighting (specific time of day or quality)
5. Composition / framing
6. Mood/aesthetic descriptors

Each template should read as cozy/rustic — see CLAUDE.md for the
visual vocabulary lock-in.
"""

COZY_RUSTIC_TEMPLATES = [
    {
        "name": "barnwood_lavender",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "resting on a weathered reclaimed barnwood plank with visible "
            "grain and knots, a small bundle of dried lavender tied with "
            "natural jute twine placed beside it, warm afternoon side light "
            "from the right creating soft natural shadows, shallow depth of "
            "field, cozy rustic farmhouse aesthetic, magazine-quality "
            "editorial styling"
        ),
    },
    {
        "name": "linen_kraft_unwrap",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "partially unwrapped from natural kraft paper tied with thin "
            "jute twine, resting on a rumpled cream linen napkin, a few "
            "scattered dried chamomile flower petals nearby, soft warm "
            "golden hour window light, handmade artisan aesthetic, "
            "minimal cozy composition"
        ),
    },
    {
        "name": "farmhouse_kitchen",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "on a worn wooden cutting board on a rustic farmhouse kitchen "
            "counter, a small fresh sprig of rosemary placed alongside, "
            "soft warm afternoon light filtering through a gauzy "
            "linen curtain in the background, cozy lived-in feel, "
            "shallow depth of field with softly blurred background"
        ),
    },
    {
        "name": "herb_garden_stone",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "on an aged limestone garden surface, fresh growing herbs "
            "(thyme and lavender) softly blurred in the background, "
            "dappled natural outdoor afternoon light coming through "
            "leaves, soft realistic shadows, cottagecore garden "
            "aesthetic, warm earthy tones"
        ),
    },
    {
        "name": "apothecary_shelf",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "on a weathered wooden apothecary shelf, amber glass "
            "apothecary bottles softly blurred in the background, a "
            "small bundle of dried herbs hanging at the edge of frame, "
            "warm tungsten afternoon light, vintage herbalist atmosphere, "
            "moody cottagecore feel with rich warm tones"
        ),
    },
    {
        "name": "wool_winter_warm",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "resting on a soft cream chunky-knit wool throw blanket, "
            "two dried orange slices and three cinnamon sticks tied "
            "with twine placed beside it, warm late-afternoon light, "
            "cozy winter holiday aesthetic, rich warm tones, "
            "shallow depth of field"
        ),
    },
    {
        "name": "stoneware_botanical",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "nestled in a small handmade stoneware ceramic dish in "
            "natural earth tones, surrounded by loose dried botanicals "
            "(calendula petals and chamomile flowers), placed on a pale "
            "weathered wood surface, soft natural daylight from above, "
            "minimal handmade artisan composition"
        ),
    },
    {
        "name": "vintage_scale",
        "prompt": (
            "professional product photograph of this exact bar of soap "
            "balanced on the platform of an antique brass kitchen scale, "
            "set on a flour-dusted weathered wooden table, a single "
            "dried lavender stem resting beside the scale base, warm "
            "nostalgic afternoon light, vintage farmhouse aesthetic, "
            "richly textured composition with soft realistic shadows"
        ),
    },
]


CANDLE_TEMPLATES = [
    {
        "name": "barnwood_cotton_wick",
        "prompt": (
            "professional product photograph of this exact candle "
            "resting on a weathered reclaimed barnwood plank with visible "
            "grain and knots, a small bundle of dried cotton stems tied "
            "with natural jute twine placed beside it, warm flame glow "
            "mixing with soft afternoon side light, shallow depth of "
            "field, cozy rustic farmhouse aesthetic, magazine-quality "
            "editorial styling"
        ),
    },
    {
        "name": "linen_herbs_lit",
        "prompt": (
            "professional product photograph of this exact candle "
            "glowing warmly on a rumpled cream linen napkin, fresh sprigs "
            "of eucalyptus and thyme arranged loosely beside it, soft "
            "golden window light blending with the candle flame, "
            "handmade artisan aesthetic, minimal cozy composition, "
            "warm amber tones"
        ),
    },
    {
        "name": "farmhouse_windowsill",
        "prompt": (
            "professional product photograph of this exact candle "
            "sitting on a worn wooden windowsill, soft gauzy linen "
            "curtain diffusing warm afternoon light behind it, a small "
            "dried lavender bundle leaning against the sill edge, "
            "cozy lived-in farmhouse feel, shallow depth of field "
            "with softly blurred outdoor background"
        ),
    },
    {
        "name": "apothecary_moody",
        "prompt": (
            "professional product photograph of this exact candle "
            "on a dark weathered wooden apothecary shelf, amber glass "
            "bottles and dried herb bundles softly blurred in the "
            "background, candle flame casting warm dramatic shadows, "
            "moody low-key lighting, vintage herbalist atmosphere, "
            "rich warm tones with deep shadows"
        ),
    },
    {
        "name": "stone_botanicals",
        "prompt": (
            "professional product photograph of this exact candle "
            "on an aged limestone surface surrounded by loose dried "
            "botanicals — calendula petals, dried rose buds, and "
            "chamomile flowers — soft natural daylight from above, "
            "minimal handmade artisan composition, warm earthy tones, "
            "cottagecore aesthetic"
        ),
    },
    {
        "name": "holiday_pine",
        "prompt": (
            "professional product photograph of this exact candle "
            "nestled among fresh pine sprigs and small pine cones on "
            "a weathered wooden surface dusted with snow, warm candle "
            "glow against cool natural winter light from the side, "
            "cozy holiday aesthetic, shallow depth of field, "
            "rich green and amber tones"
        ),
    },
    {
        "name": "ceramic_tray_spa",
        "prompt": (
            "professional product photograph of this exact candle "
            "placed on a handmade speckled stoneware ceramic tray, "
            "small river stones and a rolled linen towel arranged "
            "beside it, soft diffused natural spa light from above, "
            "clean and calming aesthetic, warm neutral tones, "
            "shallow depth of field"
        ),
    },
    {
        "name": "vintage_books_amber",
        "prompt": (
            "professional product photograph of this exact candle "
            "resting on a stack of worn vintage hardcover books on "
            "a dark wooden side table, warm amber candlelight the "
            "primary light source with a hint of soft window light, "
            "a single dried orange slice and cinnamon stick beside "
            "the books, cozy reading nook aesthetic, rich warm tones"
        ),
    },
]

STAGING_TEMPLATES = [
    {
        "name": "scandinavian_living",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in Scandinavian style, light oak furniture, cream linen "
            "sofa, minimal decor with a single potted fiddle-leaf fig, "
            "soft natural daylight from large windows, white walls with "
            "warm wood accents, clean and airy, magazine-quality staging"
        ),
    },
    {
        "name": "modern_farmhouse",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in modern farmhouse style, shiplap accent wall, "
            "distressed wood coffee table, neutral linen seating, "
            "galvanized metal accents, dried pampas grass in a ceramic vase, "
            "warm afternoon light, cozy lived-in aesthetic"
        ),
    },
    {
        "name": "luxury_contemporary",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in luxury contemporary style, deep navy or emerald "
            "velvet sofa, gold and brass accents, marble side table, "
            "statement artwork on wall, dramatic moody lighting with "
            "warm highlights, high-end real estate listing quality"
        ),
    },
    {
        "name": "coastal_bright",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in coastal style, whitewashed wood furniture, "
            "navy and white striped throw, natural rattan accents, "
            "fresh white walls, abundant natural light suggesting ocean "
            "proximity, fresh flowers in a clear glass vase, bright "
            "and airy vacation rental aesthetic"
        ),
    },
    {
        "name": "bohemian_eclectic",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in bohemian style, layered patterned rugs, macrame "
            "wall hanging, mixed vintage furniture in warm terracotta "
            "and sage tones, trailing pothos plants, warm ambient "
            "lighting from floor lamps, rich and layered texture"
        ),
    },
    {
        "name": "mid_century_modern",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in mid-century modern style, walnut credenza, "
            "tapered leg furniture in mustard and avocado tones, "
            "geometric patterned area rug, Eames-era accent chair, "
            "sunburst wall clock, warm directional lighting casting "
            "clean graphic shadows"
        ),
    },
    {
        "name": "dark_moody_dramatic",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in dark moody style, deep charcoal or forest green "
            "walls, rich leather seating, antique brass fixtures, "
            "stacked vintage books, single dramatic pendant light, "
            "dark academia atmosphere, sophisticated and dramatic"
        ),
    },
    {
        "name": "japandi_minimal",
        "prompt": (
            "professional interior design photograph of this exact room "
            "staged in Japandi style, low-profile natural wood furniture, "
            "wabi-sabi ceramic vase with single dried branch, cream "
            "boucle textiles, shoji-inspired natural light diffusion, "
            "absolute minimalism with warm organic materials, "
            "zen and calming atmosphere"
        ),
    },
]

JEWELRY_TEMPLATES = [
    {
        "name": "marble_gold",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "displayed on a smooth white Carrara marble surface with soft gold "
            "accents, a single dried ivory rose placed beside it, soft diffused "
            "studio light from the left creating gentle shadows, luxury editorial "
            "styling, clean and elegant composition, shallow depth of field"
        ),
    },
    {
        "name": "dark_velvet",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "resting on a rich deep navy velvet display surface, dramatic moody "
            "side lighting casting subtle shadows, a small crystal cluster softly "
            "blurred in the background, luxury jeweler aesthetic, rich jewel "
            "tones, high-end editorial composition"
        ),
    },
    {
        "name": "linen_botanical",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "laid on rumpled cream linen fabric, small dried lavender sprigs "
            "and chamomile flowers scattered nearby, soft natural window light "
            "from above, artisan handmade aesthetic, warm neutral tones, "
            "minimal and delicate composition"
        ),
    },
    {
        "name": "vintage_vanity",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "placed on a vintage antique silver trinket tray on a dark walnut "
            "wood surface, a few small pearls and a single dried rose petal "
            "beside it, warm nostalgic afternoon light, romantic heirloom "
            "aesthetic, shallow depth of field with rich warm tones"
        ),
    },
    {
        "name": "pressed_flowers",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "displayed on textured watercolor paper with delicate pressed flowers "
            "— dried violets, tiny daisies, and ferns — arranged artfully around "
            "it, soft diffused overhead natural light, botanical art studio "
            "aesthetic, pastel and cream tones, ultra-delicate composition"
        ),
    },
    {
        "name": "raw_crystal",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "resting on a natural dark slate surface, rough raw amethyst and "
            "quartz crystal clusters arranged beside it, cool natural overhead "
            "light with soft shadows, earthy mineral gemstone aesthetic, "
            "organic textures, editorial product styling"
        ),
    },
    {
        "name": "kraft_ribbon_gift",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "presented on unfolded kraft paper with a cream satin ribbon bow, "
            "a small sprig of fresh eucalyptus beside it, soft warm afternoon "
            "window light, gifting occasion styling, warm neutral tones, "
            "clean artisan presentation"
        ),
    },
    {
        "name": "white_editorial",
        "prompt": (
            "professional product photograph of this exact piece of jewelry "
            "on a pure white seamless surface, a single dried pampas grass "
            "stem elegantly placed beside it, bright clean high-key studio "
            "lighting with soft shadows, minimalist luxury editorial styling, "
            "crisp modern composition, magazine-quality product shot"
        ),
    },
]

PRODUCT_TEMPLATES = {
    "soap": COZY_RUSTIC_TEMPLATES,
    "candle": CANDLE_TEMPLATES,
    "staging": STAGING_TEMPLATES,
    "jewelry": JEWELRY_TEMPLATES,
}


def get_template(name: str) -> dict:
    """Look up a template by name. Raises KeyError if not found."""
    for t in COZY_RUSTIC_TEMPLATES:
        if t["name"] == name:
            return t
    raise KeyError(
        f"Template '{name}' not found. Available: "
        f"{[t['name'] for t in COZY_RUSTIC_TEMPLATES]}"
    )


def list_templates() -> list[str]:
    """Return all template names in this aesthetic."""
    return [t["name"] for t in COZY_RUSTIC_TEMPLATES]
