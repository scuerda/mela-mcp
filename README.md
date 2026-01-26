# Mela MCP Server

MCP server for Mela recipe database and meal scheduling via Apple Calendar.

## Features

- **Recipe Access**: Search, list, and get full details from your Mela recipe database
- **Meal Scheduling**: Schedule meals on your Apple Calendar

## Installation

```bash
cd mela-mcp
uv sync
```

## Usage

### With Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mela": {
      "command": "uv",
      "args": ["--directory", "/Users/sashacuerda/projects/mela-mcp", "run", "mela-mcp"],
      "env": {
        "MELA_CALENDAR_NAME": "Family"
      }
    }
  }
}
```

## Configuration

- `MELA_CALENDAR_NAME`: Calendar name for meal scheduling (default: "Family")

## Tools

- `search_recipes(query)`: Search recipes by name or ingredients
- `get_recipe(recipe_id)`: Get full recipe details
- `list_recipes(filter)`: List recipes (all/favorites/want_to_cook)
- `get_scheduled_meals(days)`: Get upcoming scheduled meals
- `schedule_meal(recipe_name, date, time)`: Schedule a meal
