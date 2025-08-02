"""Centralized help/description strings for the whyx CLI."""

CLI_DESCRIPTION = "whyx CLI - Intelligent Code Exploration & Tracing (Python MVP)"

INDEX_HELP = "Build static index of the project"

RUN_HELP = "Run a script with tracing and/or watchpoints"
DIFF_HELP = "Compare two execution trace files to find behavioral differences"
REPORT_HELP = "Report coverage/impact from a saved trace"

QUERY_HELP = "Static/dynamic queries"
Q_CALLERS_HELP = "Find all call chains leading to a function"
Q_CALLEES_HELP = "List callees of a function"
Q_FINDPATH_HELP = "Find call paths from A to B"
Q_HISTORY_HELP = "Show history of a watched attribute from a trace file"
Q_SEARCH_HELP = "Search events inside a trace file"

LEG_CALLERS_HELP = "(Synonym) Find all call chains that lead to the given function"
LEG_CALLEES_HELP = "(Synonym) List direct callees of a function"
LEG_FINDPATH_HELP = "(Synonym) Find a call path from one function to another"
LEG_HISTORY_HELP = "(Synonym) Show history of assignments to a watched variable"
