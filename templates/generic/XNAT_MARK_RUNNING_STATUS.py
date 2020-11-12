#!/usr/bin/env python3
import argparse
import os
import subprocess
from xnat_file_client import XnatFileClient


serverlist = "{{ XNAT_PBS_JOBS_PUT_SERVER_LIST }}"
server = "{{ PUT_SERVER }}"
project = "{{ SUBJECT_PROJECT }}"
subject = "{{ SUBJECT_ID }}"
session = "{{ SUBJECT_SESSION }}"
credentials_file = "{{ XNAT_CREDENTIALS_FILE }}"
g_resource="RunningStatus"
g_scan="{% if PIPELINE_NAME == 'FunctionalPreprocessing' %}_{{ SUBJECT_EXTRA }}{% endif %}"

client = XnatFileClient(project, subject, session, serverlist, credentials_file)

directory=f"{{XNAT_PBS_JOBS_BUILD_DIR}}/{{SUBJECT_PROJECT}}/{{ PIPELINE_NAME }}.{{SUBJECT_ID}}_{{SUBJECT_CLASSIFIER}}{g_scan}_RUNNING_STATUS"
file=f"{{ PIPELINE_NAME }}.{{SUBJECT_ID}}_{{SUBJECT_CLASSIFIER}}{g_scan}.RUNNING"
existing_file=f"{{XNAT_PBS_JOBS_ARCHIVE_ROOT}}/{{ SUBJECT_PROJECT }}/arc001/{{SUBJECT_SESSION}}/RESOURCES/RunningStatus/{file}"
path=f"{directory}/{file}"

parser = argparse.ArgumentParser("Set up a running status file")
parser.add_argument("--status", choices=["queued", "done"], default="done")
args = parser.parse_args()
reason = args.status


if reason == "queued":
    os.makedirs(directory, exist_ok=True)
    with open(path, "w") as fd:
        fd.write(f"Reason: {reason}")
    client.upload_resource_filepath(g_resource, directory, reason)
    subprocess.call(["rm", "-rf", directory])
else:
    if os.path.exists(existing_file):
        client.remove_resource_filepath(g_resource, file)