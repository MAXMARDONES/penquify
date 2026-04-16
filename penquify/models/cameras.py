"""Camera preset library — named configs for common phone models."""

CAMERAS = {
    # 2016
    "galaxy_s7": {"camera": "Samsung Galaxy S7", "year_device_style": "2016 Android flagship", "lens_equivalent": "26mm"},
    "iphone_7": {"camera": "iPhone 7", "year_device_style": "2016 iOS", "lens_equivalent": "28mm"},

    # 2017
    "galaxy_s8": {"camera": "Samsung Galaxy S8", "year_device_style": "2017 Android flagship", "lens_equivalent": "26mm"},
    "galaxy_a5_2017": {"camera": "Samsung Galaxy A5 2017", "year_device_style": "2017 Android mid-range", "lens_equivalent": "28mm"},
    "moto_g5": {"camera": "Motorola Moto G5 Plus", "year_device_style": "2017 budget Android", "lens_equivalent": "28mm"},
    "iphone_8": {"camera": "iPhone 8", "year_device_style": "2017 iOS", "lens_equivalent": "28mm"},
    "pixel_2": {"camera": "Google Pixel 2", "year_device_style": "2017 Android", "lens_equivalent": "27mm"},
    "huawei_p10": {"camera": "Huawei P10 Lite", "year_device_style": "2017 Android mid-range", "lens_equivalent": "27mm"},
    "xiaomi_note4": {"camera": "Xiaomi Redmi Note 4", "year_device_style": "2017 budget Android", "lens_equivalent": "28mm"},

    # 2018
    "galaxy_s9": {"camera": "Samsung Galaxy S9", "year_device_style": "2018 Android flagship", "lens_equivalent": "26mm"},
    "iphone_xr": {"camera": "iPhone XR", "year_device_style": "2018 iOS", "lens_equivalent": "26mm"},

    # 2019
    "galaxy_a10": {"camera": "Samsung Galaxy A10", "year_device_style": "2019 budget Android", "lens_equivalent": "28mm"},
    "galaxy_a50": {"camera": "Samsung Galaxy A50", "year_device_style": "2019 Android mid-range", "lens_equivalent": "26mm"},
    "iphone_11": {"camera": "iPhone 11", "year_device_style": "2019 iOS", "lens_equivalent": "26mm"},

    # 2020
    "galaxy_a21s": {"camera": "Samsung Galaxy A21s", "year_device_style": "2020 budget Android", "lens_equivalent": "28mm"},
    "iphone_12": {"camera": "iPhone 12", "year_device_style": "2020 iOS", "lens_equivalent": "26mm"},
    "pixel_4a": {"camera": "Google Pixel 4a", "year_device_style": "2020 Android mid-range", "lens_equivalent": "27mm"},

    # 2021-2023
    "galaxy_a13": {"camera": "Samsung Galaxy A13", "year_device_style": "2022 budget Android", "lens_equivalent": "26mm"},
    "iphone_14": {"camera": "iPhone 14", "year_device_style": "2022 iOS", "lens_equivalent": "26mm"},
    "pixel_7": {"camera": "Google Pixel 7", "year_device_style": "2022 Android", "lens_equivalent": "25mm"},

    # Generic
    "warehouse_generic": {"camera": "generic mid-range Android smartphone", "year_device_style": "2017 budget Android", "lens_equivalent": "28mm"},
    "field_worker": {"camera": "rugged Android phone with screen protector", "year_device_style": "2019 field device", "lens_equivalent": "28mm"},
}


def get_camera(name: str) -> dict:
    """Get camera config by preset name or return as free text."""
    if name in CAMERAS:
        return CAMERAS[name]
    return {"camera": name, "year_device_style": "unknown", "lens_equivalent": "28mm"}
