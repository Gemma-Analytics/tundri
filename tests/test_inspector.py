from unittest.mock import MagicMock, patch
from tundri.inspector import inspect_schemas
from tundri.objects import Schema


@patch("tundri.inspector.get_snowflake_cursor")
def test_inspect_schemas_filters_next_schemas(mock_cursor_factory):
    """Test that schemas ending with _next or _NEXT are filtered out"""
    # Mock cursor that returns schemas including _next and _NEXT schemas
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=False)

    # Mock data: (row[4] = database, row[1] = schema)
    # Include regular schemas and schemas ending with _next/_NEXT
    mock_cursor.__iter__ = MagicMock(
        return_value=iter(
            [
                [None, "PUBLIC", None, None, "ANALYTICS", None],  # Normal schema
                [None, "REPORTING", None, None, "ANALYTICS", None],  # Normal schema
                [
                    None,
                    "STAGING_NEXT",
                    None,
                    None,
                    "ANALYTICS",
                    None,
                ],  # Should be filtered
                [None, "DATA_NEXT", None, None, "RAW", None],  # Should be filtered
                [None, "PROD", None, None, "RAW", None],  # Normal schema
                [
                    None,
                    "TEMP_next",
                    None,
                    None,
                    "RAW",
                    None,
                ],  # Should be filtered (mixed case)
            ]
        )
    )

    mock_cursor_factory.return_value = mock_cursor

    # Run the function
    result = inspect_schemas()

    # Verify that only non-_next schemas are returned
    expected = frozenset(
        [
            Schema(name="ANALYTICS.PUBLIC"),
            Schema(name="ANALYTICS.REPORTING"),
            Schema(name="RAW.PROD"),
        ]
    )

    assert result == expected
    assert len(result) == 3

    # Verify that _next schemas are not in the result
    result_names = {schema.name for schema in result}
    assert "ANALYTICS.STAGING_NEXT" not in result_names
    assert "RAW.DATA_NEXT" not in result_names
    assert "RAW.TEMP_next" not in result_names
