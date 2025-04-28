import click
from .worklogs import submit_worklog_cmd

@click.command("log-work")
@click.argument("issue_id", required=True)
@click.option("-c", "--comment", help="Comment for the worklog")
@click.option("-s", "--starttime", required=False, help="Start time in HH:MM format (defaults to the end time of the last worklog)")
@click.option("-e", "--endtime", help="End time in HH:MM format (defaults to now)")
@click.option("--json", "-j", is_flag=True, help="Output raw JSON")
@click.option("--debug", is_flag=True, help="Show debug information")
@click.pass_context
def log_work_cmd(ctx, issue_id, comment, starttime, endtime, json, debug):
    """
    Log work for a specific issue.

    ISSUE_ID: The Jira issue ID (e.g., PROJECT-123).
    """
    from ...core.worklogs import get_last_worklog
    import datetime as dt

    # If starttime is not provided, fetch the last worklog and calculate its end time
    if not starttime:
        last_worklog = get_last_worklog(issue_id)
        if last_worklog and "started" in last_worklog and "timeSpentSeconds" in last_worklog:
            started = dt.datetime.fromisoformat(last_worklog["started"].split("+")[0])
            duration = dt.timedelta(seconds=last_worklog["timeSpentSeconds"])
            starttime = (started + duration).strftime("%H:%M")
        else:
            ctx.fail("Unable to determine start time from the last worklog. Please provide a start time.")

    # Debugging: Display calculated start and end times
    if debug:
        ctx.obj.console.print(f"[debug] Calculated start time: {starttime}")
        ctx.obj.console.print(f"[debug] Provided end time: {endtime}")

    # Use Context.invoke to call the submit_worklog_cmd
    ctx.invoke(submit_worklog_cmd, issue_id=issue_id, comment=comment, starttime=starttime, endtime=endtime, json=json, debug=debug)