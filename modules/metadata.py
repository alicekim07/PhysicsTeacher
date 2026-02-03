import yaml

def load_slide_metadata(metadata_path):
    """
    Load slide metadata YAML and return a normalized slide_metadata_map.

    Returns:
        Dict[str, dict]: { slide_filename -> slide_metadata }
    """
    with open(metadata_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "slides" not in data:
        raise ValueError(f"'slides' key not found in metadata file: {metadata_path}")

    return data["slides"]
