"""Given a dashboard title, search all dashboards to retrieve its id, render and export the dashboard to pdf.
   Repeat as necessary and merge all pdfs.
Last modified: July 12, 2022
"""

import looker_sdk
import urllib
import urllib3
import json
from looker_sdk import models
from typing import cast, Dict, Optional
import time
import re
from PyPDF2 import PdfFileMerger

sdk = looker_sdk.init40("looker.ini")
urllib3.disable_warnings()

class Dashboard:
    """Create Dashboard objects for each exported dashboard"""
    def __init__(self, params):
        self.title = params[0]
        if not params[1]:
            self.filters = None
        else:
            self.filters = json.loads(params[1])
        if not params[2]:
            self.style = "tiled"
        else:
            self.style = params[2]
        if not params[3]:
            self.width = 545
        else:
            self.width = int(params[3])
        if not params[4]:
            self.height = 842
        else:
            self.height = int(params[4])


def main():
    pdfs = []
    response = re.findall(r'\"(.+?)\"', input("""
    Input the required information: 
    <dashboard_title> [<dashboard_filters>] [<dashboard_style>] [<pdf_width>] [<pdf_height>]    
    Example: "A Test Dashboard" '{"filter1": "value1, value2", "filter2": "value3"}' "single_column"
    dashboard_style defaults to "tiled"
    pdf_width defaults to 545
    pdf_height defaults to 842
    """))
    # print(response)
    # exit()
    while True:
        dashboard = Dashboard(response)
        if not dashboard.title:
            response = re.findall(r'\"(.+?)\"', input("""
             Input the required information: 
             <dashboard_title> [<dashboard_filters>] [<dashboard_style>] [<pdf_width>] [<pdf_height>]    
             Example: "A Test Dashboard" '{"filter1": "value1, value2", "filter2": "value3"}' "single_column"
             dashboard_style defaults to "tiled"
             pdf_width defaults to 545
             pdf_height defaults to 842
             """))
            continue
        dashboard_id = get_dashboard(dashboard.title)
        download_dashboard(dashboard.title, dashboard_id, dashboard.style, dashboard.width, dashboard.height, dashboard.filters)
        response = re.findall(r'\"(.+?)\"', input("Add another dashboard to the pdf? Leave blank to exit."))
        if len(response) > 0:
            pdfs.append(dashboard.title+".pdf")
            continue
        else:
            pdfs.append(dashboard.title + ".pdf")
        pdf_merge(pdfs)
        print("Merged file has been exported as result.pdf")
        break


def get_dashboard(title):
    """Get dashboard by title."""
    title = title.lower()
    dashboard = next(iter(sdk.search_dashboards(title=title)), None)
    if not dashboard:
        raise Exception(f'dashboard "{title}" not found')
    dashboard_id = dashboard['id']
    return dashboard_id

def download_dashboard(
        title: str,
        id: str,
        style: str,
        width: int,
        height: int,
        filters: [Dict[str, str]]):
    """Download specified dashboard as PDF"""
    task = sdk.create_dashboard_render_task(
        id,
        "pdf",
        models.CreateDashboardRenderTask(
            dashboard_style=style,
            dashboard_filters=urllib.parse.urlencode(filters) if filters else None,
        ),
        width,
        height,
    )

    if not (task and task.id):
        raise Exception(
            f'Could not create a render task for "{title}"'
        )

    # poll the render task until it completes
    elapsed = 0.0
    delay = 0.5  # wait .5 seconds
    print("Rendering, please wait.")
    while True:
        poll = sdk.render_task(task.id)
        if poll.status == "failure":
            print(poll)
            raise Exception(
                f'Render failed for "{title}"'
            )
        elif poll.status == "success":
            break

        time.sleep(delay)
        elapsed += delay
    print(f"Render task completed in {elapsed} seconds")

    result = sdk.render_task_results(task.id)
    filename = f"{title}.pdf"
    with open(filename, "wb") as f:
        f.write(result)
    print(f'Dashboard pdf saved to "{filename}"')

def pdf_merge(list):
    """Merges all downloaded pdf files"""
    merger = PdfFileMerger()
    [merger.append(pdf) for pdf in list]
    with open("Merged_pdfs.pdf", "wb") as new_file:
        merger.write(new_file)

if __name__ == '__main__': main()