"""Mela MCP Server - Recipe database and meal scheduling integration."""

import os
from mcp.server.fastmcp import FastMCP

from . import database
from . import calendar

mcp = FastMCP("mela")

CALENDAR_NAME = os.environ.get("MELA_CALENDAR_NAME", "Family")


@mcp.tool()
def search_recipes(query: str) -> list[dict]:
    """Search recipes by name or ingredients.

    Args:
        query: Search term to match against recipe title or ingredients

    Returns:
        List of matching recipes with id, title, prep_time, cook_time, total_time
    """
    return database.search_recipes(query)


@mcp.tool()
def get_recipe(recipe_id: int) -> dict | None:
    """Get full details for a specific recipe.

    Args:
        recipe_id: The recipe's ID number

    Returns:
        Full recipe details including title, ingredients, instructions, notes,
        nutrition, yield, times, favorite status, want_to_cook status, and link
    """
    return database.get_recipe(recipe_id)


@mcp.tool()
def list_recipes(filter: str = "all") -> list[dict]:
    """List all recipes with optional filter.

    Args:
        filter: One of "all", "favorites", or "want_to_cook"

    Returns:
        List of recipes with id, title, favorite, want_to_cook
    """
    return database.list_recipes(filter)


@mcp.tool()
def get_scheduled_meals(days: int = 7) -> list[dict]:
    """Get meals scheduled in the next N days from the calendar.

    Args:
        days: Number of days to look ahead (default 7)

    Returns:
        List of scheduled meals with title, date, time
    """
    return calendar.get_scheduled_meals(CALENDAR_NAME, days)


@mcp.tool()
def schedule_meal(recipe_name: str, date: str, time: str = "18:00") -> dict:
    """Schedule a meal on the calendar.

    Args:
        recipe_name: Name of the meal/recipe to schedule
        date: Date in YYYY-MM-DD format (e.g., "2024-01-15")
        time: Time in HH:MM 24-hour format (default "18:00" for 6 PM)

    Returns:
        Dict with success status and event details
    """
    return calendar.schedule_meal(CALENDAR_NAME, recipe_name, date, time)


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
