import re


def extract_param_desc(param_name: str, docstring: str):
    """Extract parameter description from docstring.

    Args:
        param_name (str): Param name.
        docstring (str): Docstring.

    Returns:
        Parameter description.
    """
    param_description = ""

    # Google style: "param_name (type): description"
    google_match = re.search(
        rf"{re.escape(param_name)}\s*\([^)]*\)\s*:\s*(.+?)(?=\n\s*\w+\s*\([^)]*\)\s*:|\n\s*Returns?:|\n\s*Raises?:|\n\s*Examples?:|\n\s*Note:|\n\s*Yields?:|\n\s*Attributes?:|\n\s*\n|\Z)",
        docstring,
        re.DOTALL,
    )
    if google_match:
        # Clean up multi-line description
        param_description = " ".join(google_match.group(1).split())
    else:
        # reST style: ":param param_name: description"
        rest_match = re.search(
            rf":param\s+{re.escape(param_name)}\s*:\s*(.+?)(?=\n\s*:\w+|\n\s*\n|\Z)",
            docstring,
            re.DOTALL,
        )
        if rest_match:
            param_description = " ".join(rest_match.group(1).split())
        else:
            # Sphinx style with type: ":param type param_name: description"
            sphinx_match = re.search(
                rf":param\s+\w+\s+{re.escape(param_name)}\s*:\s*(.+?)(?=\n\s*:\w+|\n\s*\n|\Z)",
                docstring,
                re.DOTALL,
            )
            if sphinx_match:
                param_description = " ".join(sphinx_match.group(1).split())

    return param_description
